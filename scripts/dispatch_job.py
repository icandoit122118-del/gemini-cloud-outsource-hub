"""
카본 전용 외주 발주기 (scripts/dispatch_job.py).

- 명령 한 줄로 새 외주 발주서를 발행하거나 상시 8대 발주서 큐(JOB-01..JOB-08)를 갱신하여 깃허브 우체통에 반영한다.
- 발주 즉시 RL-GCO-01(API 키·토큰·비밀번호·개인 로컬 민감 경로 유출 차단 게이트)을 강제 수행한다.
- 웹 제미나이 클라우드 가상 컴퓨터(gemini.google.com)에 바로 복붙할 초간단 3줄 한글 실행 프롬프트를 자동 출력한다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.outsource_gates import check_gate_01_no_secrets_or_local_paths
from src.outsource_jobs import (
    GITHUB_PUBLIC_REPO,
    build_three_line_korean_prompt,
    materialize_all_job_queues,
)


def dispatch_single_job(
    repo_root: Path,
    job_id: str,
    title_ko: str | None = None,
    category: str = "custom_cloud_outsource",
    summary_ko: str | None = None,
    target_import_rel_dir: str | None = None,
) -> Dict[str, Any]:
    """단일 발주서를 검증(RL-GCO-01) 후 발행하고 3줄 한글 실행 프롬프트를 반환한다."""
    jobs_dir = repo_root / "jobs"
    jdir = jobs_dir / job_id
    spec_path = jdir / "job_spec.json"
    brief_path = jdir / "BRIEF_KO.md"

    if not spec_path.exists() and title_ko is None:
        materialize_all_job_queues(repo_root)

    if spec_path.exists() and title_ko is None and summary_ko is None:
        spec_obj = json.loads(spec_path.read_text(encoding="utf-8"))
        brief_text = brief_path.read_text(encoding="utf-8")
    else:
        prompt_3lines = build_three_line_korean_prompt(job_id)
        resolved_title = title_ko or f"{job_id} 클라우드 외주 작업"
        resolved_summary = summary_ko or "공개 문서 및 순수 파이썬 표준 라이브러리를 이용해 무결점 납품 번들을 제조한다."
        resolved_import_dir = target_import_rel_dir or f"imported_custom/{job_id.lower()}"
        spec_obj = {
            "schema": "gemini-cloud-outsource-job-v1",
            "job_id": job_id,
            "title_ko": resolved_title,
            "category": category,
            "priority": 9,
            "security_classification": "PUBLIC_CLEAN_ZERO_SECRET",
            "target_repo": GITHUB_PUBLIC_REPO,
            "workspace_rel_path": f"jobs/{job_id}",
            "target_import_rel_dir": resolved_import_dir,
            "summary_ko": resolved_summary,
            "deliverable_expectations_ko": [
                "6대 보안 및 품질 게이트(RL-GCO-01..06) 100% 통과",
                "비밀 정보 0바이트 및 순수 한글 규격 준수",
            ],
            "required_gates": [
                "RL-GCO-01",
                "RL-GCO-02",
                "RL-GCO-03",
                "RL-GCO-04",
                "RL-GCO-05",
                "RL-GCO-06",
            ],
            "cloud_prompt_3lines_ko": prompt_3lines.splitlines(),
        }
        brief_text = (
            f"# [{job_id}] {resolved_title}\n\n"
            f"## 1. 작업 목표\n- {resolved_summary}\n\n"
            f"## 2. 3줄 실행 프롬프트\n```text\n{prompt_3lines}\n```\n"
        )

    gate1 = check_gate_01_no_secrets_or_local_paths({"job_spec": spec_obj, "brief_text": brief_text})
    if not gate1["passed"]:
        raise ValueError(f"RL-GCO-01 발주 보안 차단 적발: {gate1['violations']}")

    jdir.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    brief_path.write_text(brief_text, encoding="utf-8")

    prompt_3lines = build_three_line_korean_prompt(job_id)
    lines = prompt_3lines.splitlines()
    assert len(lines) == 3, "프롬프트는 정확히 3줄이어야 합니다."

    return {
        "dispatched": True,
        "job_id": job_id,
        "title_ko": spec_obj["title_ko"],
        "security_gate": gate1,
        "spec_path": str(spec_path),
        "brief_path": str(brief_path),
        "prompt_3lines_ko": prompt_3lines,
        "prompt_line_count": len(lines),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="카본 전용 깃허브 클라우드 외주 우체통 발주기")
    parser.add_argument("--job", default="JOB-01", help="발주할 작업 ID (예: JOB-01..JOB-08)")
    parser.add_argument("--all", action="store_true", help="8대 상시 외주 발주서 큐 전체 생성 및 갱신")
    parser.add_argument("--title", default=None, help="신규 커스텀 발주 시 한글 제목")
    parser.add_argument("--category", default="custom_cloud_outsource", help="신규 커스텀 발주 카테고리")
    parser.add_argument("--summary", default=None, help="신규 커스텀 발주 작업 목표 설명")
    parser.add_argument("--git-push", action="store_true", help="발주 후 git add/commit/push 자동 실행")
    args = parser.parse_args()

    if args.all:
        manifest = materialize_all_job_queues(REPO_ROOT)
        print(f"[발주 완료] 총 {manifest['total_jobs']}종 상시 외주 발주서 큐 갱신 완료 ({GITHUB_PUBLIC_REPO})")
        print("=" * 78)
        print(build_three_line_korean_prompt(args.job))
        print("=" * 78)
    else:
        res = dispatch_single_job(
            REPO_ROOT,
            job_id=args.job,
            title_ko=args.title,
            category=args.category,
            summary_ko=args.summary,
        )
        print(f"[발주 완료] {res['job_id']} - {res['title_ko']} (RL-GCO-01 보안 검문 통과)")
        print("=" * 78)
        print(res["prompt_3lines_ko"])
        print("=" * 78)

    if args.git_push:
        subprocess.run(["git", "add", "jobs", "outputs"], cwd=str(REPO_ROOT), check=True)
        subprocess.run(
            ["git", "commit", "-m", f"chore(dispatch): update outsource job queue ({args.job})"],
            cwd=str(REPO_ROOT),
            check=False,
        )
        subprocess.run(["git", "push", "origin", "HEAD"], cwd=str(REPO_ROOT), check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
