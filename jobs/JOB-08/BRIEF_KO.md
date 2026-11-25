# [JOB-08] 언리얼 5.9 셰이더·물리 수식 사전 격자 검증기(unittest) 대량 제작

> **보안 등급**: `PUBLIC_CLEAN_ZERO_SECRET` (API 키·토큰·비밀번호·개인 로컬 민감 경로 `0바이트`)
> **원격 저장소**: `icandoit122118-del/gemini-cloud-outsource-hub`
> **반입 대상 경로**: `imported_tests/ue59_shader_physics_grid`

## 1. 작업 목표
- 언리얼 5.9 에디터를 띄우지 않고도 0 MB VRAM 환경에서 카툰 셰이더(GT7 톤매퍼, 부호 깊이 림, 180도 완만 법선)와 물리 잔디 원호 굽힘 수식을 1,000개 이상의 매개변수 격자에서 사전 검증하는 파이썬 unittest 스위트를 제조한다.

## 2. 필수 납품 규격 및 합격 기준
- 표준 파이썬 unittest 기반 0 MB VRAM 고속 격자 검증 스크립트 제공
- GT7 톤매퍼 단조증가성, 부호 깊이 림 가림막 기각, 잔디 줄기 길이 보존(1.0000) 격자 테스트 완비
- 외부 실행파일이나 위험 명령 없이 순수 수학·표준 라이브러리로만 작동

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
2. `jobs/JOB-08/BRIEF_KO.md` 작업지시서를 읽고 `python scripts/run_cloud_job.py --job JOB-08` 및 `python -m unittest discover -s tests -p "test_*.py" -v`를 실행해 6대 보안·품질 게이트(RL-GCO-01..06) 6/6 통과를 자체 검증하세요.
3. 검증 완료된 납품 번들(`deliveries/JOB-08_delivery.zip` 및 `deliveries/JOB-08_delivery.json`)을 생성하고 터미널 출력 요약과 함께 납품해 주세요.
```
