# [JOB-06] 치사토·메이린 상황별 순수 한글 전술 교신·파밍·야영 상호작용 대사집 기획

> **보안 등급**: `PUBLIC_CLEAN_ZERO_SECRET` (API 키·토큰·비밀번호·개인 로컬 민감 경로 `0바이트`)
> **원격 저장소**: `icandoit122118-del/gemini-cloud-outsource-hub`
> **반입 대상 경로**: `imported_narratives/chisato_meilin_dialogues_ko`

## 1. 작업 목표
- 주인공 치사토와 동료 메이린의 전술 교신·현장 파밍(4단 선반/서랍 수색)·야영 휴식 상황별 상호작용 대사집과 자막 UI 표기문을 100% 순수 한글(영문자 0글자)로 작성한다.

## 2. 필수 납품 규격 및 합격 기준
- 치사토·메이린 2인 화자 필수 참여 및 전술 교신·현장 파밍·야영 휴식 3대 상황 전수 포함
- 모든 한글 대사(line_ko) 및 자막(ui_caption_ko) 내 영문 알파벳(A-Z, a-z) 0글자 엄수
- 감정 톤·음성 연출 지시문 및 상황 트리거 조건을 순수 한글로 기술

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
2. `jobs/JOB-06/BRIEF_KO.md` 작업지시서를 읽고 `python scripts/run_cloud_job.py --job JOB-06` 및 `python -m unittest discover -s tests -p "test_*.py" -v`를 실행해 6대 보안·품질 게이트(RL-GCO-01..06) 6/6 통과를 자체 검증하세요.
3. 검증 완료된 납품 번들(`deliveries/JOB-06_delivery.zip` 및 `deliveries/JOB-06_delivery.json`)을 생성하고 터미널 출력 요약과 함께 납품해 주세요.
```
