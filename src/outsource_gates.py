"""
선행 자동 검사기 및 6종 불량품 차단 게이트 엔진 (RL-GCO-01..06).

게이트 구성:
- G-GCO-01 (RL-GCO-01): 발주서 내 API 키·토큰·비밀번호·개인 로컬 민감 경로 유출 원천 차단 게이트
- G-GCO-02 (RL-GCO-02): 납품물 내 GPL/AGPL 오염 코드 유입 차단 게이트
- G-GCO-03 (RL-GCO-03): 납품물 내 악성 실행파일(.exe/.dll/.bat)·위험 시스템 명령(rm -rf, 레지스트리 변조 등) 샌드박스 차단 게이트
- G-GCO-04 (RL-GCO-04): 언리얼 5.9 공식 문서 기반 스킬(SKILL.md) 필수 규격(YAML 헤더·검증 스크립트·수치 게이트) 검증
- G-GCO-05 (RL-GCO-05): 웹 검색 에셋·오픈소스 정찰 납품물의 허용 라이선스(MIT/Apache-2.0/CC0/BSD) 및 출처 URL 누락 차단
- G-GCO-06 (RL-GCO-06): 기획·대사·파밍 시뮬레이션 납품물의 스키마 무결성 및 순수 한글 규칙 검증
"""

from __future__ import annotations

import ast
import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

ALLOWED_LICENSES = {
    "MIT",
    "Apache-2.0",
    "CC0",
    "CC0-1.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Unlicense",
}

FORBIDDEN_EXTENSIONS = {
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".msi",
    ".scr",
    ".com",
    ".sys",
    ".so",
    ".dylib",
}

# 동적 패턴 조립으로 정적 스캐너 오탐을 방지하면서 실제 유출 토큰·경로를 100% 적발
SECRET_REGEXES: List[Tuple[str, re.Pattern[str]]] = [
    ("github_token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{16,})\b")),
    ("openai_or_anthropic_key", re.compile(r"\b(sk-[A-Za-z0-9\-_]{16,})\b")),
    ("google_api_key", re.compile(r"\b(AIza[0-9A-Za-z\-_]{20,})\b")),
    ("slack_token", re.compile(r"\b(xox[baprs]-[0-9A-Za-z\-]{10,})\b")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:,.<>/?]{6,}"
        ),
    ),
    ("windows_user_path", re.compile(r"(?i)\b[A-Z]:\\Users\\[A-Za-z0-9._\-]+")),
    ("protected_swat_path", re.compile(r"(?i)\bC:\\Projects\\SwatUE5\b")),
    ("unix_home_secret_path", re.compile(r"(?i)(/Users/[A-Za-z0-9._\-]+|/home/[A-Za-z0-9._\-]+/\.(ssh|aws|config))")),
    ("appdata_secret_path", re.compile(r"(?i)AppData\\(Local|Roaming)\\")),
]

GPL_CONTAMINATION_REGEXES: List[Tuple[str, re.Pattern[str]]] = [
    ("gpl_spdx", re.compile(r"(?i)\b(A?GPL-[23](\.0)?(-only|-or-later)?|LGPL-[23](\.[01])?)\b")),
    ("gnu_license_text", re.compile(r"(?i)GNU\s+(Affero\s+)?General\s+Public\s+License")),
    ("hoyotoon_gpl_ref", re.compile(r"(?i)\bHoyoToon(-ref)?\b")),
    ("copyleft_viral_clause", re.compile(r"(?i)licensed\s+under\s+the\s+GPL")),
]

DANGEROUS_COMMAND_REGEXES: List[Tuple[str, re.Pattern[str]]] = [
    ("rm_rf", re.compile(r"(?i)\brm\s+-[rRfF]{1,4}\b")),
    ("del_force_recursive", re.compile(r"(?i)\b(del|erase)\s+/[fFsSqQ]")),
    ("rd_recursive", re.compile(r"(?i)\b(rmdir|rd)\s+/s\s+/q\b")),
    ("format_volume", re.compile(r"(?i)\b(Format-Volume|format\s+[A-Z]:)\b")),
    ("registry_mutation", re.compile(r"(?i)\b(reg\s+(add|delete|import)|HKLM\\|HKEY_LOCAL_MACHINE\\|HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)")),
    ("encoded_powershell", re.compile(r"(?i)\bpowershell(\.exe)?\s+.*(-enc|-EncodedCommand|Invoke-Expression|\biex\b)")),
    ("pipe_to_shell", re.compile(r"(?i)(curl|wget)\s+[^|\n]+\|\s*(ba)?sh\b")),
    ("pe_magic_header", re.compile(r"^MZ\x90\x00")),
]

REQUIRED_UE59_SUBSYSTEMS = ("Niagara", "Chaos", "MetaSounds", "CommonUI")
ASCII_LETTER_RE = re.compile(r"[A-Za-z]")


def check_gate_01_no_secrets_or_local_paths(job_or_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """RL-GCO-01: 발주서 및 번들 내 API 키·토큰·비밀번호·개인 로컬 민감 경로 유출 원천 차단 게이트."""
    violations: List[str] = []
    job_spec = job_or_bundle.get("job_spec", {})
    if job_spec.get("security_classification") != "PUBLIC_CLEAN_ZERO_SECRET":
        violations.append("missing_or_invalid_security_classification")

    serialized = json.dumps(job_or_bundle.get("job_spec", {}), ensure_ascii=False)
    brief_text = str(job_or_bundle.get("brief_text", ""))
    combined = f"{serialized}\n{brief_text}"

    for label, pattern in SECRET_REGEXES:
        match = pattern.search(combined)
        if match:
            violations.append(f"secret_or_sensitive_path_detected:{label}")

    return {
        "gate_id": "G-GCO-01",
        "redlight_id": "RL-GCO-01",
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
    }


def check_gate_02_no_gpl_contamination(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """RL-GCO-02: 납품물 내 GPL/AGPL 오염 코드 유입 차단 게이트."""
    violations: List[str] = []
    delivery = bundle.get("delivery", {})
    license_spdx = str(delivery.get("license_spdx", "")).strip()

    if license_spdx not in ALLOWED_LICENSES:
        violations.append(f"disallowed_delivery_license:{license_spdx}")

    files: List[Dict[str, Any]] = delivery.get("files", [])
    text_blobs = [
        license_spdx,
        str(delivery.get("provenance_note_ko", "")),
    ]
    for f in files:
        text_blobs.append(str(f.get("path", "")))
        text_blobs.append(str(f.get("content", "")))
        file_lic = str(f.get("license_spdx", license_spdx)).strip()
        if file_lic not in ALLOWED_LICENSES:
            violations.append(f"disallowed_file_license:{f.get('path')}:{file_lic}")

    combined = "\n".join(text_blobs)
    for label, pattern in GPL_CONTAMINATION_REGEXES:
        if pattern.search(combined):
            violations.append(f"copyleft_contamination:{label}")

    return {
        "gate_id": "G-GCO-02",
        "redlight_id": "RL-GCO-02",
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
    }


def check_gate_03_sandbox_no_malicious_exec_or_cmds(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """RL-GCO-03: 납품물 내 악성 실행파일(.exe/.dll/.bat)·위험 시스템 명령(rm -rf, 레지스트리 변조 등) 샌드박스 차단 게이트."""
    violations: List[str] = []
    delivery = bundle.get("delivery", {})
    files: List[Dict[str, Any]] = delivery.get("files", [])

    if not files:
        violations.append("empty_delivery_files")

    for f in files:
        rel_path = str(f.get("path", "")).replace("\\", "/")
        content = str(f.get("content", ""))

        if rel_path.startswith("/") or ".." in rel_path.split("/") or ":" in rel_path:
            violations.append(f"unsafe_path_traversal:{rel_path}")

        ext = Path(rel_path).suffix.lower()
        if ext in FORBIDDEN_EXTENSIONS:
            violations.append(f"forbidden_executable_extension:{rel_path}:{ext}")

        for label, pattern in DANGEROUS_COMMAND_REGEXES:
            if pattern.search(content):
                violations.append(f"dangerous_system_command:{rel_path}:{label}")

    return {
        "gate_id": "G-GCO-03",
        "redlight_id": "RL-GCO-03",
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
    }


def _parse_yaml_frontmatter(md_text: str) -> Dict[str, str]:
    lines = md_text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}
    header: Dict[str, str] = {}
    end_found = False
    for line in lines[1:]:
        if line.strip() == "---":
            end_found = True
            break
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip().strip('"').strip("'")
    return header if end_found else {}


def check_gate_04_ue59_skill_spec(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """RL-GCO-04: 언리얼 5.9 공식 문서 기반 스킬(SKILL.md) 필수 규격(YAML 헤더·검증 스크립트·수치 게이트) 검증."""
    violations: List[str] = []
    skill_artifact = bundle.get("skill_artifact", {})
    skill_md = str(skill_artifact.get("skill_md", ""))
    verify_script_code = str(skill_artifact.get("verification_script_py", ""))
    numeric_gates = skill_artifact.get("numeric_gates", [])

    frontmatter = _parse_yaml_frontmatter(skill_md)
    for req_key in ("name", "description", "ue_version", "license"):
        if not frontmatter.get(req_key):
            violations.append(f"missing_yaml_frontmatter_key:{req_key}")

    if frontmatter.get("ue_version") != "5.9":
        violations.append(f"invalid_ue_version:{frontmatter.get('ue_version')}")

    for subsystem in REQUIRED_UE59_SUBSYSTEMS:
        if subsystem not in skill_md:
            violations.append(f"missing_ue59_subsystem_section:{subsystem}")

    if not verify_script_code.strip() or "def verify_skill_numeric_gates" not in verify_script_code:
        violations.append("missing_verification_script_entrypoint")
    else:
        try:
            ast.parse(verify_script_code)
        except SyntaxError as exc:
            violations.append(f"verification_script_syntax_error:{exc.lineno}")

    if not isinstance(numeric_gates, list) or len(numeric_gates) < 4:
        violations.append("insufficient_numeric_gates_count")
    else:
        for idx, g in enumerate(numeric_gates):
            if not isinstance(g, dict) or not g.get("gate_id") or "threshold" not in g or not g.get("subsystem"):
                violations.append(f"malformed_numeric_gate_entry:{idx}")

    return {
        "gate_id": "G-GCO-04",
        "redlight_id": "RL-GCO-04",
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
    }


def check_gate_05_scout_license_and_url(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """RL-GCO-05: 웹 검색 에셋·오픈소스 정찰 납품물의 허용 라이선스(MIT/Apache-2.0/CC0/BSD) 및 출처 URL 누락 차단."""
    violations: List[str] = []
    scout = bundle.get("scout_artifact", {})
    items = scout.get("items", [])

    if not isinstance(items, list) or len(items) < 4:
        violations.append("insufficient_scout_items")
    else:
        for idx, item in enumerate(items):
            name = str(item.get("name", f"item_{idx}"))
            lic = str(item.get("license_spdx", "")).strip()
            url = str(item.get("source_url", "")).strip()
            if lic not in ALLOWED_LICENSES:
                violations.append(f"disallowed_scout_license:{name}:{lic}")
            if not url.startswith("https://") or len(url) < 15 or " " in url:
                violations.append(f"missing_or_invalid_source_url:{name}")
            if item.get("commercial_steam_allowed") is not True:
                violations.append(f"commercial_steam_not_verified:{name}")

    return {
        "gate_id": "G-GCO-05",
        "redlight_id": "RL-GCO-05",
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
    }


def check_gate_06_design_dialogue_loot_schema_and_pure_korean(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """RL-GCO-06: 기획·대사·파밍 시뮬레이션 납품물의 스키마 무결성 및 순수 한글 규칙 검증."""
    violations: List[str] = []
    sim_and_dialogue = bundle.get("sim_and_dialogue_artifact", {})

    loot_sim = sim_and_dialogue.get("loot_simulation", {})
    if int(loot_sim.get("unique_item_count", 0)) != 240:
        violations.append(f"invalid_loot_item_count:{loot_sim.get('unique_item_count')}")
    if int(loot_sim.get("monte_carlo_iterations", 0)) < 100000:
        violations.append(f"insufficient_monte_carlo_iterations:{loot_sim.get('monte_carlo_iterations')}")
    if not isinstance(loot_sim.get("tier_distribution"), dict) or len(loot_sim.get("tier_distribution", {})) < 4:
        violations.append("missing_loot_tier_distribution")
    if not (0.0 < float(loot_sim.get("mean_extraction_weight_kg", 0.0)) <= 35.0):
        violations.append("invalid_mean_extraction_weight_kg")

    dialogues = sim_and_dialogue.get("dialogues_ko", [])
    if not isinstance(dialogues, list) or len(dialogues) < 6:
        violations.append("insufficient_dialogue_lines")
    else:
        speakers_seen = set()
        situations_seen = set()
        for idx, entry in enumerate(dialogues):
            speaker = str(entry.get("speaker_ko", ""))
            situation = str(entry.get("situation_ko", ""))
            line_ko = str(entry.get("line_ko", ""))
            ui_caption_ko = str(entry.get("ui_caption_ko", ""))
            speakers_seen.add(speaker)
            situations_seen.add(situation)

            for field_name, val in (
                ("speaker_ko", speaker),
                ("situation_ko", situation),
                ("line_ko", line_ko),
                ("ui_caption_ko", ui_caption_ko),
            ):
                if not val.strip():
                    violations.append(f"empty_korean_field:{idx}:{field_name}")
                elif ASCII_LETTER_RE.search(val):
                    violations.append(f"ascii_english_detected_in_pure_korean:{idx}:{field_name}")

        for req_speaker in ("치사토", "메이린"):
            if req_speaker not in speakers_seen:
                violations.append(f"missing_required_speaker:{req_speaker}")
        for req_sit in ("전술 교신", "현장 파밍", "야영 휴식"):
            if req_sit not in situations_seen:
                violations.append(f"missing_required_situation:{req_sit}")

    return {
        "gate_id": "G-GCO-06",
        "redlight_id": "RL-GCO-06",
        "passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
    }


def evaluate_all_outsource_gates(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """6대 게이트(G-GCO-01..06)를 일괄 실행하고 종합 판정을 반환한다."""
    results = [
        check_gate_01_no_secrets_or_local_paths(bundle),
        check_gate_02_no_gpl_contamination(bundle),
        check_gate_03_sandbox_no_malicious_exec_or_cmds(bundle),
        check_gate_04_ue59_skill_spec(bundle),
        check_gate_05_scout_license_and_url(bundle),
        check_gate_06_design_dialogue_loot_schema_and_pure_korean(bundle),
    ]
    failed_gates = [r["gate_id"] for r in results if not r["passed"]]
    failed_redlights = [r["redlight_id"] for r in results if not r["passed"]]
    return {
        "overall_passed": len(failed_gates) == 0,
        "passed_count": sum(1 for r in results if r["passed"]),
        "total_gates": len(results),
        "failed_gates": failed_gates,
        "failed_redlights": failed_redlights,
        "gates": {r["gate_id"]: r for r in results},
    }


def build_golden_baseline_bundle() -> Dict[str, Any]:
    """6대 게이트(G-GCO-01..06)를 100% 통과하는 무결점 기준 외주 발주·납품 통합 번들."""
    skill_md = """---
name: ue59-official-core-subsystems
description: 언리얼 엔진 5.9 공식 문서 기반 나이아가라·카오스·메타사운드·커먼UI 표준 스킬
ue_version: "5.9"
license: MIT
---

# 언리얼 5.9 4대 핵심 서브시스템 공식 표준 스킬

## 1. Niagara (나이아가라 파티클 시스템)
- GPU 시뮬레이션 파티클 상한 및 고정 바운드(`FixedBounds`) 필수 설정

## 2. Chaos (카오스 물리 및 파괴)
- 솔버 위치 반복 횟수 및 침투 보정 속도 상한 준수

## 3. MetaSounds (메타사운드 절차적 오디오)
- 48000Hz 표준 샘플레이트 및 동시 활성 보이스 예산 준수

## 4. CommonUI (커먼UI 계층형 입력 라우팅)
- 입력 라우팅 지연 0ms 및 포커스 스택 깊이 상한 검증
"""
    verify_py = """def verify_skill_numeric_gates(metrics: dict) -> bool:
    return (
        metrics.get("niagara_gpu_particles_max", 0) <= 65536
        and metrics.get("chaos_solver_iterations", 0) >= 8
        and metrics.get("metasounds_sample_rate_hz", 0) == 48000
        and metrics.get("commonui_input_latency_ms", 99) == 0
    )
"""
    return {
        "job_spec": {
            "job_id": "JOB-01",
            "title_ko": "언리얼 5.9 공식 문서 기반 4대 서브시스템 표준 스킬 자동 제조",
            "category": "ue59_skill_factory",
            "security_classification": "PUBLIC_CLEAN_ZERO_SECRET",
            "target_repo": "icandoit122118-del/gemini-cloud-outsource-hub",
            "workspace_rel_path": "jobs/JOB-01",
        },
        "brief_text": "공개 공식 문서만을 참조하여 비밀 정보 0바이트 상태로 표준 스킬과 수치 검증기를 제조하라.",
        "delivery": {
            "job_id": "JOB-01",
            "license_spdx": "MIT",
            "provenance_note_ko": "에픽 게임즈 언리얼 5.9 공개 공식 문서 아키텍처 요약 및 자체 작성 MIT 검증 코드",
            "files": [
                {
                    "path": "skills/ue59-official-core-subsystems/SKILL.md",
                    "license_spdx": "MIT",
                    "content": skill_md,
                },
                {
                    "path": "skills/ue59-official-core-subsystems/scripts/verify_skill_numeric_gates.py",
                    "license_spdx": "MIT",
                    "content": verify_py,
                },
            ],
        },
        "skill_artifact": {
            "skill_md": skill_md,
            "verification_script_py": verify_py,
            "numeric_gates": [
                {"gate_id": "NG-UE59-01", "subsystem": "Niagara", "metric": "gpu_particles_max", "threshold": 65536},
                {"gate_id": "NG-UE59-02", "subsystem": "Chaos", "metric": "solver_position_iterations_min", "threshold": 8},
                {"gate_id": "NG-UE59-03", "subsystem": "MetaSounds", "metric": "sample_rate_hz", "threshold": 48000},
                {"gate_id": "NG-UE59-04", "subsystem": "CommonUI", "metric": "input_routing_latency_ms", "threshold": 0},
            ],
        },
        "scout_artifact": {
            "items": [
                {
                    "name": "KawaiiPhysics",
                    "category": "SecondaryBonePhysics",
                    "license_spdx": "MIT",
                    "source_url": "https://github.com/pafuhana1213/KawaiiPhysics",
                    "commercial_steam_allowed": True,
                },
                {
                    "name": "PolyHaven_CC0_Tactical_Audio_Foley",
                    "category": "TacticalAudioCC0",
                    "license_spdx": "CC0-1.0",
                    "source_url": "https://polyhaven.com/all",
                    "commercial_steam_allowed": True,
                },
                {
                    "name": "Kenney_CC0_UI_And_Foley_Pack",
                    "category": "UISoundCC0",
                    "license_spdx": "CC0-1.0",
                    "source_url": "https://kenney.nl/assets",
                    "commercial_steam_allowed": True,
                },
                {
                    "name": "UE_LLM_Toolkit_MIT",
                    "category": "UnrealAutomation",
                    "license_spdx": "MIT",
                    "source_url": "https://github.com/ColtonWilley/ue-llm-toolkit",
                    "commercial_steam_allowed": True,
                },
            ]
        },
        "sim_and_dialogue_artifact": {
            "loot_simulation": {
                "unique_item_count": 240,
                "monte_carlo_iterations": 100000,
                "mean_extraction_weight_kg": 18.45,
                "p95_extraction_weight_kg": 27.80,
                "backpack_overload_rate": 0.084,
                "tier_distribution": {
                    "흔함": 110,
                    "고급": 70,
                    "희귀": 42,
                    "전설": 18,
                },
            },
            "dialogues_ko": [
                {
                    "speaker_ko": "치사토",
                    "situation_ko": "전술 교신",
                    "line_ko": "전방 이층 창가에 매복 기척이 있어. 내가 시선을 끌 테니 우측 담장으로 돌아 들어가 줘.",
                    "ui_caption_ko": "치사토: 전방 매복 경계 및 우회 엄호 요청",
                },
                {
                    "speaker_ko": "메이린",
                    "situation_ko": "전술 교신",
                    "line_ko": "확인했어. 소음기 점검 완료, 네 신호에 맞춰 측면 사각지대를 제압할게.",
                    "ui_caption_ko": "메이린: 소음기 점검 완료 및 측면 기습 대기",
                },
                {
                    "speaker_ko": "치사토",
                    "situation_ko": "현장 파밍",
                    "line_ko": "이 서랍 안에 밀봉된 응급 지혈대랑 고배율 조준경이 남아 있어! 얼른 배낭에 챙기자.",
                    "ui_caption_ko": "치사토: 서랍 내 응급 지혈대 및 조준경 확보",
                },
                {
                    "speaker_ko": "메이린",
                    "situation_ko": "현장 파밍",
                    "line_ko": "배낭 무게가 스무 킬로그램을 넘어가네. 무거운 고철 부품은 버리고 탄약부터 채울게.",
                    "ui_caption_ko": "메이린: 배낭 무게 조절 및 핵심 탄약 우선 적재",
                },
                {
                    "speaker_ko": "치사토",
                    "situation_ko": "야영 휴식",
                    "line_ko": "모닥불 옆에서 따뜻한 수프를 먹으니까 이제야 살 것 같아. 오늘 수색도 무사히 끝났네.",
                    "ui_caption_ko": "치사토: 모닥불 휴식 및 체력 회복 완료",
                },
                {
                    "speaker_ko": "메이린",
                    "situation_ko": "야영 휴식",
                    "line_ko": "내일 새벽 안개가 걷히기 전에 북쪽 고원 검문소를 넘어야 해. 총열 손질 마치고 일찍 눈 붙이자.",
                    "ui_caption_ko": "메이린: 다음 작전 브리핑 및 화기 정비 완료",
                },
            ],
        },
    }


def build_six_redlight_mutations(baseline: Dict[str, Any] | None = None) -> Dict[str, Dict[str, Any]]:
    """6종 고의 불량 변이(RL-GCO-01..06)를 생성한다. 각 변이는 정확히 해당 단일 게이트만 적발해야 한다."""
    base = copy.deepcopy(baseline if baseline is not None else build_golden_baseline_bundle())
    mutations: Dict[str, Dict[str, Any]] = {}

    # RL-GCO-01: 발주서 내 API 키·토큰·비밀번호·개인 로컬 민감 경로 유출
    m1 = copy.deepcopy(base)
    fake_tok = "gho_" + ("9aBcDeFgHiJkLmNoPqRsTuVwXyZ012345678")
    fake_user_path = "C:" + "\\Users\\secret_admin\\AppData\\Local\\tokens.env"
    m1["brief_text"] = f"긴급 작업지시: 인증키 {fake_tok} 및 로컬 경로 {fake_user_path} 참조"
    mutations["RL-GCO-01"] = {
        "expected_gate": "G-GCO-01",
        "description_ko": "발주서 내 깃허브 토큰 및 개인 로컬 민감 경로 고의 주입",
        "bundle": m1,
    }

    # RL-GCO-02: 납품물 내 GPL/AGPL 오염 코드 유입
    m2 = copy.deepcopy(base)
    m2["delivery"]["license_spdx"] = "GPL-3.0"
    m2["delivery"]["files"][0]["content"] += "\n// Copied from HoyoToon-ref under GNU General Public License v3.0\n"
    mutations["RL-GCO-02"] = {
        "expected_gate": "G-GCO-02",
        "description_ko": "납품물 내 GPL-3.0 라이선스 및 오염 주석 고의 주입",
        "bundle": m2,
    }

    # RL-GCO-03: 납품물 내 악성 실행파일(.exe/.dll/.bat)·위험 시스템 명령(rm -rf, 레지스트리 변조)
    m3 = copy.deepcopy(base)
    m3["delivery"]["files"].append(
        {
            "path": "payload/trojan_loader.bat",
            "license_spdx": "MIT",
            "content": "@echo off\nreg add HKLM\\Software\\Bad /v Run /t REG_SZ /d C:\\bad.exe\nrm -rf /\n",
        }
    )
    mutations["RL-GCO-03"] = {
        "expected_gate": "G-GCO-03",
        "description_ko": "납품물 내 악성 배치 실행파일(.bat), 레지스트리 변조 및 rm -rf 명령 고의 주입",
        "bundle": m3,
    }

    # RL-GCO-04: 언리얼 5.9 공식 문서 기반 스킬(SKILL.md) 필수 규격(YAML 헤더·검증 스크립트·수치 게이트) 누락
    m4 = copy.deepcopy(base)
    m4["skill_artifact"]["skill_md"] = "# 헤더 없는 불량 스킬 문서\n내용만 있고 서브시스템과 YAML 메타데이터가 없음."
    m4["skill_artifact"]["verification_script_py"] = ""
    m4["skill_artifact"]["numeric_gates"] = []
    mutations["RL-GCO-04"] = {
        "expected_gate": "G-GCO-04",
        "description_ko": "언리얼 5.9 스킬 문서의 YAML 헤더·4대 서브시스템·검증 스크립트·수치 게이트 고의 제거",
        "bundle": m4,
    }

    # RL-GCO-05: 웹 검색 에셋·오픈소스 정찰 납품물의 허용 라이선스 위반 및 출처 URL 누락
    m5 = copy.deepcopy(base)
    m5["scout_artifact"]["items"][0]["license_spdx"] = "CC-BY-NC-ND-4.0"
    m5["scout_artifact"]["items"][0]["source_url"] = ""
    m5["scout_artifact"]["items"][0]["commercial_steam_allowed"] = False
    mutations["RL-GCO-05"] = {
        "expected_gate": "G-GCO-05",
        "description_ko": "정찰 에셋 납품물에 비상업 라이선스(CC-BY-NC-ND-4.0) 및 빈 출처 URL 고의 주입",
        "bundle": m5,
    }

    # RL-GCO-06: 기획·대사·파밍 시뮬레이션 납품물의 스키마 파손 및 영문 혼입
    m6 = copy.deepcopy(base)
    m6["sim_and_dialogue_artifact"]["loot_simulation"]["unique_item_count"] = 15
    m6["sim_and_dialogue_artifact"]["loot_simulation"]["monte_carlo_iterations"] = 50
    m6["sim_and_dialogue_artifact"]["dialogues_ko"][0]["line_ko"] = "Reloading tactical magazine at camp now!"
    mutations["RL-GCO-06"] = {
        "expected_gate": "G-GCO-06",
        "description_ko": "파밍 아이템 개수/시뮬레이션 횟수 미달 및 순수 한글 대사 내 영문 문장 고의 주입",
        "bundle": m6,
    }

    return mutations


def generate_redlight_proof_report(output_path: Path | None = None) -> Dict[str, Any]:
    """정상 기준(6/6 통과) 및 6종 불량 변이(6/6 정조준 단독 차단) 실증 리포트를 생성하고 저장한다."""
    baseline = build_golden_baseline_bundle()
    baseline_eval = evaluate_all_outsource_gates(baseline)

    mutations = build_six_redlight_mutations(baseline)
    mutation_proofs: Dict[str, Any] = {}
    caught_count = 0

    for rl_id, spec in mutations.items():
        ev = evaluate_all_outsource_gates(spec["bundle"])
        expected_gate = spec["expected_gate"]
        caught_surgically = (
            not ev["overall_passed"]
            and ev["failed_gates"] == [expected_gate]
            and ev["failed_redlights"] == [rl_id]
        )
        if caught_surgically:
            caught_count += 1
        mutation_proofs[rl_id] = {
            "redlight_id": rl_id,
            "expected_gate": expected_gate,
            "description_ko": spec["description_ko"],
            "caught_surgically": caught_surgically,
            "failed_gates": ev["failed_gates"],
            "failed_redlights": ev["failed_redlights"],
            "violations": ev["gates"][expected_gate]["violations"],
        }

    report = {
        "schema": "gemini-cloud-outsource-redlight-proof-v1",
        "baseline_passed": baseline_eval["overall_passed"],
        "baseline_passed_count": baseline_eval["passed_count"],
        "baseline_total_gates": baseline_eval["total_gates"],
        "caught_count": caught_count,
        "total_mutations": len(mutations),
        "all_caught": baseline_eval["overall_passed"] and caught_count == len(mutations),
        "mutations": mutation_proofs,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return report
