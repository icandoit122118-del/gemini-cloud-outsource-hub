"""
웹 제미나이 클라우드 가상 컴퓨터 전용 작업 실행기 (scripts/run_cloud_job.py).

원격 가상 컴퓨터가 공개 저장소를 복제한 뒤 명령 한 줄로 지정된 외주 작업(JOB-01..JOB-08)을
수행하고 자체 6대 게이트 검증을 거쳐 deliveries/ 폴더에 납품 번들(ZIP/JSON)을 생성한다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.outsource_jobs import JOB_DEFINITIONS, execute_cloud_job, materialize_all_job_queues


def main() -> int:
    parser = argparse.ArgumentParser(description="클라우드 가상 컴퓨터 외주 발주서 실행기")
    parser.add_argument("--job", default="JOB-01", help="실행할 작업 ID (JOB-01..JOB-08)")
    parser.add_argument("--all", action="store_true", help="8대 외주 작업(JOB-01..JOB-08) 전수 실행 및 번들 생성")
    args = parser.parse_args()

    materialize_all_job_queues(REPO_ROOT)

    if args.all:
        for jdef in JOB_DEFINITIONS:
            jid = jdef["job_id"]
            res = execute_cloud_job(jid, REPO_ROOT)
            print(
                f"[클라우드 작업 완료] {jid}: 게이트 {res['gate_evaluation']['passed_count']}/6 통과 -> "
                f"{res['zip_delivery_path']} (SHA256: {res['zip_sha256'][:12]}...)"
            )
    else:
        res = execute_cloud_job(args.job, REPO_ROOT)
        print(
            f"[클라우드 작업 완료] {args.job}: 게이트 {res['gate_evaluation']['passed_count']}/6 통과 -> "
            f"{res['zip_delivery_path']} (SHA256: {res['zip_sha256'][:12]}...)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
