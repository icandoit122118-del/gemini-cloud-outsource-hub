# [JOB-02] 상업 무료(CC0/MIT) 전술 총기·장구·환경 효과음 및 오픈소스 유틸리티 웹 수색 정찰

> **보안 등급**: `PUBLIC_CLEAN_ZERO_SECRET` (API 키·토큰·비밀번호·개인 로컬 민감 경로 `0바이트`)
> **원격 저장소**: `icandoit122118-del/gemini-cloud-outsource-hub`
> **반입 대상 경로**: `imported_scouts/tactical_audio_and_oss_scout`

## 1. 작업 목표
- 스팀 상업 게임에 조건 없이 즉시 투입 가능한 CC0·MIT·Apache-2.0·BSD 라이선스 전술 총기/장구/발소리/환경 효과음 및 언리얼 보조 유틸리티를 수색하여 출처 URL과 라이선스를 검증한다.

## 2. 필수 납품 규격 및 합격 기준
- 허용 라이선스(MIT, Apache-2.0, CC0, CC0-1.0, BSD-2-Clause, BSD-3-Clause) 100% 준수
- 모든 항목에 https:// 로 시작하는 실제 원본 출처 URL 및 상업 스팀 허용 여부(true) 명시
- GPL/AGPL 및 비상업(CC-BY-NC) 에셋 원천 배제

## 3. 6대 자동 검문 게이트 (전수 통과 필수)
- `RL-GCO-01`: 발주서 및 납품물 내 API 키·토큰·비밀번호·개인 로컬 경로 유출 원천 차단
- `RL-GCO-02`: 납품물 내 GPL/AGPL 오염 코드 유입 원천 차단 (`MIT/Apache-2.0/CC0/BSD`만 허용)
- `RL-GCO-03`: 납품물 내 악성 실행파일(`.exe/.dll/.bat`) 및 위험 시스템 명령(`rm -rf`, 레지스트리 변조) 차단
- `RL-GCO-04`: 언리얼 5.9 공식 문서 기반 스킬(`SKILL.md`) YAML 헤더·검증 스크립트·수치 게이트 검증
- `RL-GCO-05`: 웹 검색 에셋·오픈소스 정찰 납품물의 허용 라이선스 및 `https://` 출처 URL 누락 차단
- `RL-GCO-06`: 기획·대사·파밍 시뮬레이션 납품물의 스키마 무결성 및 순수 한글(영문자 `0개`) 규칙 검증

## 4. 웹 제미나이 클라우드 가상 컴퓨터 복붙용 3줄 실행 프롬프트
```text
1. 클라우드 가상 컴퓨터 터미널에서 `git clone https://github.com/icandoit122118-del/gemini-cloud-outsource-hub.git work && cd work` 명령으로 공개 외주 우체통 저장소를 복제하세요.
2. `jobs/JOB-02/BRIEF_KO.md` 작업지시서를 읽고 `python scripts/run_cloud_job.py --job JOB-02` 및 `python -m unittest discover -s tests -p "test_*.py" -v`를 실행해 6대 보안·품질 게이트(RL-GCO-01..06) 6/6 통과를 자체 검증하세요.
3. 검증 완료된 납품 번들(`deliveries/JOB-02_delivery.zip` 및 `deliveries/JOB-02_delivery.json`)을 생성하고 터미널 출력 요약과 함께 납품해 주세요.
```
