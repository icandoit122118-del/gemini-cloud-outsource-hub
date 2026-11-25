# 깃허브 전용 웹 제미나이 클라우드 가상 컴퓨터 외주 우체통 시스템 (`GeminiCloudOutsourceHub`)

> **보안 등급**: `PUBLIC_CLEAN_ZERO_SECRET` (API 키 · 토큰 · 비밀번호 · 개인 로컬 민감 경로 **`0바이트`**)  
> **원격 저장소**: `https://github.com/icandoit122118-del/gemini-cloud-outsource-hub`  
> **운영 목적**: 본체 그래픽카드(`0 MB VRAM`)와 로컬 자원을 단 1%도 쓰지 않고, 공개 읽기 가능한 깃허브 우체통을 통해 웹 제미나이 클라우드 가상 컴퓨터(`gemini.google.com`)가 무인증으로 작업지시서를 내려받아 파이썬 과학연산·시뮬레이션·스킬 제조·대사 기획을 수행한 뒤, **6대 자동 검문 게이트(`RL-GCO-01..06`)**를 통과한 무결점 납품물만 본 프로젝트로 안전 반입한다.

---

## 1. 6대 선행 자동 검문 게이트 및 불량품 차단 실증 (`RL-GCO-01..06`)

| 게이트 ID | 불량 변이 ID | 차단 대상 및 검수 규칙 | 실증 상태 |
|---|---|---|---|
| `G-GCO-01` | `RL-GCO-01` | 발주서 내 API 키·토큰·비밀번호·개인 로컬 민감 경로 유출 원천 차단 | **차단 실증 완료 (`PASS`)** |
| `G-GCO-02` | `RL-GCO-02` | 납품물 내 `GPL/AGPL` 오염 코드 유입 원천 차단 (`MIT/Apache-2.0/CC0/BSD`만 허용) | **차단 실증 완료 (`PASS`)** |
| `G-GCO-03` | `RL-GCO-03` | 납품물 내 악성 실행파일(`.exe/.dll/.bat`) 및 위험 시스템 명령(`rm -rf`, 레지스트리 변조) 차단 | **차단 실증 완료 (`PASS`)** |
| `G-GCO-04` | `RL-GCO-04` | 언리얼 5.9 공식 문서 기반 스킬(`SKILL.md`) 필수 규격(YAML 헤더·4대 서브시스템·검증 스크립트·수치 게이트) 검증 | **차단 실증 완료 (`PASS`)** |
| `G-GCO-05` | `RL-GCO-05` | 웹 검색 에셋·오픈소스 정찰 납품물의 상업 무료 라이선스 및 `https://` 출처 URL 누락 차단 | **차단 실증 완료 (`PASS`)** |
| `G-GCO-06` | `RL-GCO-06` | 기획·대사·파밍 시뮬레이션 납품물의 스키마 무결성(`240종`/`10만 회`) 및 순수 한글(영문자 `0글자`) 검증 | **차단 실증 완료 (`PASS`)** |

---

## 2. 클라우드 가상 컴퓨터 전용 8대 상시 외주 발주서 큐 (`jobs/JOB-01..JOB-08`)

1. **`JOB-01`**: 언리얼 5.9 공식 문서 정독 → 나이아가라·카오스·메타사운드·커먼UI 표준 스킬(`SKILL.md`) 자동 제조
2. **`JOB-02`**: 상업 무료(`CC0/MIT`) 전술 총기/장구/환경 효과음 및 오픈소스 유틸리티 웹 수색 정찰
3. **`JOB-03`**: 하이브리드 파밍 전리품 `240종` & 배낭 무게 경제 `10만 회` 몬테카를로 시뮬레이션
4. **`JOB-04`**: 무저작권 파이썬 과학연산 기반 절차적 빗소리·바람·UI 조작음 `48kHz` 파형 합성
5. **`JOB-05`**: 무봉제 `1024x1024` 전술 직물·스크래치·먼지·녹 마스크 절차적 합성
6. **`JOB-06`**: 치사토·메이린 상황별 순수 한글 전술 교신·파밍·야영 상호작용 대사집 기획
7. **`JOB-07`**: 스팀 서브컬처·익스트랙션 슈터 인기작 리뷰 분석 및 차별화 기획서
8. **`JOB-08`**: 언리얼 5.9 셰이더·물리 수식 사전 격자 검증기(`unittest`) 대량 제작

---

## 3. 카본 발주 및 클라우드 가상 컴퓨터 3줄 실행 워크플로

### ① 카본 발주 명령 (`scripts/dispatch_job.py`)
```bash
python scripts/dispatch_job.py --all
python scripts/dispatch_job.py --job JOB-01
```

### ② 웹 제미나이 클라우드 가상 컴퓨터 복붙용 초간단 3줄 한글 실행 프롬프트
```text
1. 클라우드 가상 컴퓨터 터미널에서 `git clone https://github.com/icandoit122118-del/gemini-cloud-outsource-hub.git work && cd work` 명령으로 공개 외주 우체통 저장소를 복제하세요.
2. `jobs/JOB-01/BRIEF_KO.md` 작업지시서를 읽고 `python scripts/run_cloud_job.py --job JOB-01` 및 `python -m unittest discover -s tests -p "test_*.py" -v`를 실행해 6대 보안·품질 게이트(RL-GCO-01..06) 6/6 통과를 자체 검증하세요.
3. 검증 완료된 납품 번들(`deliveries/JOB-01_delivery.zip` 및 `deliveries/JOB-01_delivery.json`)을 생성하고 터미널 출력 요약과 함께 납품해 주세요.
```

### ③ 카본 자동 검수 수거 명령 (`scripts/harvest_delivery.py`)
```bash
python scripts/harvest_delivery.py --harvest-all
python scripts/harvest_delivery.py --input deliveries/JOB-01_delivery.zip --target-dir staging_harvest/JOB-01
```
