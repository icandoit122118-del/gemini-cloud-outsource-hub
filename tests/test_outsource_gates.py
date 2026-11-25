"""
선행 자동 검사기 및 6종 불량품 차단 실증 + 발주기/수거기/8대 상시 외주 발주서 큐 전수 검증 스위트.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.dispatch_job import dispatch_single_job
from scripts.harvest_delivery import (
    harvest_all_queued_deliveries,
    harvest_delivery_bundle,
    harvest_loaded_bundle,
)
from src.outsource_gates import (
    build_golden_baseline_bundle,
    build_six_redlight_mutations,
    check_gate_01_no_secrets_or_local_paths,
    evaluate_all_outsource_gates,
    generate_redlight_proof_report,
)
from src.outsource_jobs import (
    JOB_DEFINITIONS,
    build_three_line_korean_prompt,
    execute_cloud_job,
    materialize_all_job_queues,
)


class TestOutsourceGates(unittest.TestCase):
    """RL-GCO-01..06 선행 게이트, 6/6 불량 변이 차단, 발주기·수거기 및 8대 발주서 큐 통합 테스트."""

    def test_01_golden_baseline_passes_all_six_gates(self) -> None:
        bundle = build_golden_baseline_bundle()
        result = evaluate_all_outsource_gates(bundle)
        self.assertTrue(result["overall_passed"], f"Baseline failed: {result['failed_gates']}")
        self.assertEqual(result["passed_count"], 6)
        self.assertEqual(result["total_gates"], 6)
        self.assertEqual(result["failed_gates"], [])

    def test_02_rl_gco_01_secret_and_local_path_leak_blocked(self) -> None:
        mutations = build_six_redlight_mutations()
        ev = evaluate_all_outsource_gates(mutations["RL-GCO-01"]["bundle"])
        self.assertFalse(ev["overall_passed"])
        self.assertEqual(ev["failed_gates"], ["G-GCO-01"])
        self.assertEqual(ev["failed_redlights"], ["RL-GCO-01"])
        self.assertGreaterEqual(ev["gates"]["G-GCO-01"]["violation_count"], 2)

    def test_03_rl_gco_02_gpl_agpl_contamination_blocked(self) -> None:
        mutations = build_six_redlight_mutations()
        ev = evaluate_all_outsource_gates(mutations["RL-GCO-02"]["bundle"])
        self.assertFalse(ev["overall_passed"])
        self.assertEqual(ev["failed_gates"], ["G-GCO-02"])
        self.assertEqual(ev["failed_redlights"], ["RL-GCO-02"])
        self.assertTrue(
            any("copyleft_contamination" in v for v in ev["gates"]["G-GCO-02"]["violations"])
        )

    def test_04_rl_gco_03_malicious_binary_and_dangerous_cmd_blocked(self) -> None:
        mutations = build_six_redlight_mutations()
        ev = evaluate_all_outsource_gates(mutations["RL-GCO-03"]["bundle"])
        self.assertFalse(ev["overall_passed"])
        self.assertEqual(ev["failed_gates"], ["G-GCO-03"])
        self.assertEqual(ev["failed_redlights"], ["RL-GCO-03"])
        violations = ev["gates"]["G-GCO-03"]["violations"]
        self.assertTrue(any("forbidden_executable_extension" in v for v in violations))
        self.assertTrue(any("dangerous_system_command" in v for v in violations))

    def test_05_rl_gco_04_ue59_skill_spec_missing_headers_and_gates_blocked(self) -> None:
        mutations = build_six_redlight_mutations()
        ev = evaluate_all_outsource_gates(mutations["RL-GCO-04"]["bundle"])
        self.assertFalse(ev["overall_passed"])
        self.assertEqual(ev["failed_gates"], ["G-GCO-04"])
        self.assertEqual(ev["failed_redlights"], ["RL-GCO-04"])

    def test_06_rl_gco_05_scout_disallowed_license_and_missing_url_blocked(self) -> None:
        mutations = build_six_redlight_mutations()
        ev = evaluate_all_outsource_gates(mutations["RL-GCO-05"]["bundle"])
        self.assertFalse(ev["overall_passed"])
        self.assertEqual(ev["failed_gates"], ["G-GCO-05"])
        self.assertEqual(ev["failed_redlights"], ["RL-GCO-05"])

    def test_07_rl_gco_06_schema_corruption_and_english_contamination_blocked(self) -> None:
        mutations = build_six_redlight_mutations()
        ev = evaluate_all_outsource_gates(mutations["RL-GCO-06"]["bundle"])
        self.assertFalse(ev["overall_passed"])
        self.assertEqual(ev["failed_gates"], ["G-GCO-06"])
        self.assertEqual(ev["failed_redlights"], ["RL-GCO-06"])
        violations = ev["gates"]["G-GCO-06"]["violations"]
        self.assertTrue(any("ascii_english_detected_in_pure_korean" in v for v in violations))
        self.assertTrue(any("invalid_loot_item_count" in v for v in violations))

    def test_08_redlight_proof_json_generated_and_verified(self) -> None:
        proof_path = REPO_ROOT / "outputs" / "outsource_redlight_proof.json"
        report = generate_redlight_proof_report(proof_path)
        self.assertTrue(proof_path.exists())
        loaded = json.loads(proof_path.read_text(encoding="utf-8"))
        self.assertTrue(loaded["all_caught"])
        self.assertEqual(loaded["caught_count"], 6)
        self.assertEqual(loaded["total_mutations"], 6)
        for idx in range(1, 7):
            rl_id = f"RL-GCO-0{idx}"
            self.assertIn(rl_id, report["mutations"])
            self.assertTrue(report["mutations"][rl_id]["caught_surgically"])

    def test_09_eight_job_queues_and_dispatch_3line_prompts_verified(self) -> None:
        manifest = materialize_all_job_queues(REPO_ROOT)
        self.assertEqual(manifest["total_jobs"], 8)
        for idx in range(1, 9):
            job_id = f"JOB-0{idx}"
            spec_file = REPO_ROOT / "jobs" / job_id / "job_spec.json"
            brief_file = REPO_ROOT / "jobs" / job_id / "BRIEF_KO.md"
            self.assertTrue(spec_file.exists(), f"Missing {spec_file}")
            self.assertTrue(brief_file.exists(), f"Missing {brief_file}")

            res = dispatch_single_job(REPO_ROOT, job_id=job_id)
            self.assertTrue(res["dispatched"])
            self.assertEqual(res["prompt_line_count"], 3)
            self.assertTrue(res["security_gate"]["passed"])

        # 비밀 토큰이 포함된 불량 발주 시 즉시 예외로 차단되는지 검증
        bad_token = "ghp_" + ("Z" * 36)
        with self.assertRaises(ValueError):
            dispatch_single_job(
                REPO_ROOT,
                job_id="JOB-99-BAD",
                title_ko="불량 비밀 유출 발주서",
                summary_ko=f"절대 유출되면 안 되는 토큰 {bad_token}",
            )

    def test_10_cloud_execution_and_harvest_delivery_gate_enforcement(self) -> None:
        # 8대 작업 전수 실행 및 ZIP/JSON 납품 번들 생성
        for jdef in JOB_DEFINITIONS:
            jid = jdef["job_id"]
            exec_res = execute_cloud_job(jid, REPO_ROOT)
            self.assertTrue(exec_res["gate_evaluation"]["overall_passed"])
            self.assertTrue(Path(exec_res["zip_delivery_path"]).exists())

        # 정상 납품물 8종 수거 검증
        harvest_summary = harvest_all_queued_deliveries(REPO_ROOT)
        self.assertEqual(harvest_summary["total_deliveries_inspected"], 8)
        self.assertEqual(harvest_summary["accepted_count"], 8)
        self.assertTrue(harvest_summary["all_accepted"])

        # 6종 불량 변이 납품물 투입 시 harvest_loaded_bundle 이 단 1개의 파일도 반입하지 않고 차단하는지 검증
        mutations = build_six_redlight_mutations()
        with tempfile.TemporaryDirectory() as tmpdir:
            for rl_id, mspec in mutations.items():
                dest = Path(tmpdir) / rl_id
                h_res = harvest_loaded_bundle(mspec["bundle"], dest, source_label=rl_id)
                self.assertFalse(h_res["accepted"], f"{rl_id} should be rejected by harvest_delivery")
                self.assertEqual(h_res["imported_file_count"], 0)
                self.assertFalse(dest.exists(), f"Rejected delivery {rl_id} must not create target folder")


if __name__ == "__main__":
    unittest.main()
