"""
카본 전용 자동 검수 수거기 (scripts/harvest_delivery.py).

- 웹 제미나이 클라우드 가상 컴퓨터가 납품한 ZIP / JSON / MD 파일을 수거한다.
- 반입 전 메모리 샌드박스에서 6대 게이트(RL-GCO-01..06)를 전수 검사한다.
- 6/6 게이트를 100% 통과한 경우에만 대상 프로젝트/스킬 폴더로 안전 반입하며,
  단 1개 게이트라도 실패하면 파일 반입을 0바이트로 원천 차단하고 격리 보고서를 남긴다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.outsource_gates import (
    FORBIDDEN_EXTENSIONS,
    build_golden_baseline_bundle,
    evaluate_all_outsource_gates,
)


def _load_bundle_from_input(input_path: Path) -> Dict[str, Any]:
    """ZIP, JSON 또는 MD 납품물을 메모리 내 검증 번들 구조로 로드한다."""
    suffix = input_path.suffix.lower()

    if suffix == ".json":
        return json.loads(input_path.read_text(encoding="utf-8"))

    if suffix == ".zip":
        with zipfile.ZipFile(input_path, "r") as zf:
            names = zf.namelist()
            extra_files: List[Dict[str, Any]] = []
            bundle: Dict[str, Any] = {}

            if "delivery_bundle.json" in names:
                bundle = json.loads(zf.read("delivery_bundle.json").decode("utf-8"))
            else:
                bundle = build_golden_baseline_bundle()
                bundle["delivery"]["files"] = []

            existing_paths = {f.get("path") for f in bundle.get("delivery", {}).get("files", [])}
            for member_name in names:
                if member_name == "delivery_bundle.json" or member_name.endswith("/"):
                    continue
                raw_bytes = zf.read(member_name)
                try:
                    text_content = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = "MZ\x90\x00_BINARY_PAYLOAD"
                if member_name not in existing_paths:
                    extra_files.append(
                        {
                            "path": member_name,
                            "license_spdx": bundle.get("delivery", {}).get("license_spdx", "MIT"),
                            "content": text_content,
                        }
                    )
            bundle.setdefault("delivery", {}).setdefault("files", []).extend(extra_files)
            return bundle

    if suffix == ".md":
        md_text = input_path.read_text(encoding="utf-8")
        bundle = build_golden_baseline_bundle()
        bundle["skill_artifact"]["skill_md"] = md_text
        bundle["delivery"]["files"] = [
            {
                "path": f"skills/{input_path.stem}/SKILL.md",
                "license_spdx": "MIT",
                "content": md_text,
            }
        ]
        return bundle

    raise ValueError(f"지원하지 않는 납품 파일 형식입니다: {input_path}")


def harvest_delivery_bundle(
    input_path: Path,
    target_dir: Path,
) -> Dict[str, Any]:
    """
    납품 파일(ZIP/JSON/MD) 또는 인메모리 번들을 6대 게이트로 검수하고,
    6/6 통과 시에만 target_dir 로 안전 반입한다.
    """
    bundle = _load_bundle_from_input(input_path)
    return harvest_loaded_bundle(bundle, target_dir, source_label=str(input_path))


def harvest_loaded_bundle(
    bundle: Dict[str, Any],
    target_dir: Path,
    source_label: str = "in_memory_bundle",
) -> Dict[str, Any]:
    """로드된 번들 객체를 6대 게이트로 검수하고 6/6 통과 시에만 target_dir에 파일을 기록한다."""
    gate_eval = evaluate_all_outsource_gates(bundle)
    imported_files: List[str] = []

    if not gate_eval["overall_passed"]:
        return {
            "accepted": False,
            "source": source_label,
            "target_dir": str(target_dir),
            "imported_file_count": 0,
            "imported_files": [],
            "gate_evaluation": gate_eval,
        }

    target_dir.mkdir(parents=True, exist_ok=True)
    for f_entry in bundle.get("delivery", {}).get("files", []):
        rel_path = str(f_entry["path"]).replace("\\", "/").lstrip("/")
        if ".." in rel_path.split("/") or Path(rel_path).suffix.lower() in FORBIDDEN_EXTENSIONS:
            raise RuntimeError(f"Sandbox guard blocked file path: {rel_path}")
        dest_file = target_dir / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_text(str(f_entry["content"]), encoding="utf-8")
        imported_files.append(str(dest_file))

    receipt = {
        "accepted": True,
        "job_id": bundle.get("job_spec", {}).get("job_id", "UNKNOWN"),
        "source": source_label,
        "target_dir": str(target_dir),
        "imported_file_count": len(imported_files),
        "imported_files": imported_files,
        "bundle_sha256": hashlib.sha256(
            json.dumps(bundle, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "gate_evaluation": gate_eval,
    }
    (target_dir / "harvest_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def harvest_all_queued_deliveries(repo_root: Path) -> Dict[str, Any]:
    """deliveries/ 폴더 내 8대 작업 납품 번들을 전수 검수·수거하고 종합 보고서를 작성한다."""
    deliveries_dir = repo_root / "deliveries"
    staging_root = repo_root / "staging_harvest"
    results: Dict[str, Any] = {}
    accepted_count = 0

    zip_files = sorted(deliveries_dir.glob("JOB-*_delivery.zip"))
    for zpath in zip_files:
        job_id = zpath.name.split("_")[0]
        dest_dir = staging_root / job_id
        res = harvest_delivery_bundle(zpath, dest_dir)
        if res["accepted"]:
            accepted_count += 1
        results[job_id] = {
            "job_id": job_id,
            "accepted": res["accepted"],
            "imported_file_count": res["imported_file_count"],
            "passed_gates": res["gate_evaluation"]["passed_count"],
            "total_gates": res["gate_evaluation"]["total_gates"],
            "failed_redlights": res["gate_evaluation"]["failed_redlights"],
        }

    summary = {
        "schema": "gemini-cloud-outsource-harvest-report-v1",
        "total_deliveries_inspected": len(zip_files),
        "accepted_count": accepted_count,
        "rejected_count": len(zip_files) - accepted_count,
        "all_accepted": len(zip_files) > 0 and accepted_count == len(zip_files),
        "deliveries": results,
    }
    report_path = repo_root / "outputs" / "harvest_verification_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="카본 전용 외주 납품물 6대 게이트 자동 검수 수거기")
    parser.add_argument("--input", type=str, default=None, help="검수할 납품 파일 경로 (.zip / .json / .md)")
    parser.add_argument("--target-dir", type=str, default=None, help="검수 통과 시 반입할 대상 폴더 경로")
    parser.add_argument("--harvest-all", action="store_true", help="deliveries/ 내 전수 납품 번들 검수 및 수거")
    args = parser.parse_args()

    if args.harvest_all:
        summary = harvest_all_queued_deliveries(REPO_ROOT)
        print(
            f"[수거 완료] 검사 {summary['total_deliveries_inspected']}건 중 "
            f"승인 {summary['accepted_count']}건 / 차단 {summary['rejected_count']}건"
        )
        return 0 if summary["all_accepted"] else 1

    if not args.input:
        parser.error("--input 또는 --harvest-all 중 하나를 지정해야 합니다.")

    in_path = Path(args.input).resolve()
    t_dir = Path(args.target_dir).resolve() if args.target_dir else (REPO_ROOT / "staging_harvest" / in_path.stem)
    res = harvest_delivery_bundle(in_path, t_dir)
    if res["accepted"]:
        print(f"[반입 승인] 6/6 게이트 통과 -> {res['imported_file_count']}개 파일 반입 완료 ({t_dir})")
        return 0
    else:
        print(f"[반입 차단] 불량 적발 게이트: {res['gate_evaluation']['failed_redlights']}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
