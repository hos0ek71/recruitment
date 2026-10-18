# H-2 외부 응답 픽스처 완료 보고

작성일: 2026-10-17. 변경 범위는 `backend/tests/fixtures/**`와 `backend/tests/unit/test_fixture_hygiene.py`뿐이다.
실제 채용 API 호출·인증키 사용·의존성 파일 변경·git commit은 하지 않았다.
파일별 공식 문서 URL, 합성 내역, 개인정보 처리, 게이트 1 교체 대상은 `SOURCES.md`에 기록했다.

## 변경 파일

공식 예시 그대로 저장(들여쓰기만 정리):

- `saramin/error_missing_key.json`: 공식 JSON 오류 예시(code 1). 코디네이터 답변에 따라 추가.

합성 파일(실제 응답과 다를 수 있음):

- `saramin/list_ok.json`, `saramin/list_page2.json`: 공식 JSON 예시 구조에 가상 공고 총 5건, 첫 페이지 3건·마지막 페이지 2건.
- `saramin/list_empty.json`, `saramin/list_missing_fields.json`: 공식 예시 구조로 빈 결과·누락 결과 구성.
- `saramin/error_auth.json`: 공식 XML code 2와 메시지를 JSON 오류 구조로 옮김. 코디네이터 승인.
- `saramin/error_quota.json`: 공식 code 4와 합성 메시지.
- `work24/list_ok.xml`, `work24/list_page2.xml`: 공식 XML 필드표에 가상 공고 총 5건, 첫 페이지 3건·마지막 페이지 2건.
- `work24/list_empty.xml`, `work24/list_missing_fields.xml`: 공식 필드표로 빈 결과·누락 결과 구성.
- `work24/detail_ok.xml`, `work24/detail_missing_fields.xml`: 공식 필드표의 사원수·직무내용 및 누락 상세 구성.
- `work24/error.xml`: **형식 미확인, 추정**. 문서에서 오류 응답 형식을 찾지 못함.

나머지 변경 파일은 `SOURCES.md`, 이 보고서, `backend/tests/unit/test_fixture_hygiene.py`이다.
검사 함수는 전체 트리의 UTF-8/JSON/XML 파싱, 긴 키 값, 이메일 도메인, 전화번호를 검사하며 민감한 값 자체는 진단에 출력하지 않는다.
XML은 defusedxml로 읽고 엔티티 선언을 거부한다.

## 검증 증거

1. 테스트 먼저 작성하고 검사 함수가 빈 목록만 반환하는 상태에서 실행:
   `cd backend && uv run pytest tests/unit/test_fixture_hygiene.py -q`
   → 종료 코드 1, **16 failed, 1 passed**.
   위반 탐지 자기검증 12건과 미작성 픽스처·출처·페이지 검사 4건이 실패했다.
2. 검사 함수와 픽스처 작성 후 같은 명령:
   → 종료 코드 0, **17 passed in 0.05s**.
3. `cd backend && uv run ruff check tests/unit/test_fixture_hygiene.py`
   → 종료 코드 0, **All checks passed!**.
4. `cd backend && uv run ruff format --check tests/unit/test_fixture_hygiene.py`
   → 종료 코드 0, **1 file already formatted**.
5. 첫 `make check-backend`:
   → 종료 코드 2. 다른 워커가 작성 중인 `app/db.py`, `app/repositories/models.py`,
   `tests/integration/test_migrations.py`의 Ruff 37개 오류로 중단.
6. 별도 `cd backend && uv run mypy`:
   → 종료 코드 1. 다른 워커 작성 중 `app/repositories/collection.py`,
   `app/repositories/api_usage.py`에서 타입 오류 3건. 소유권 밖 파일은 수정하지 않았다.

최종 인계 검증(코디네이터 지시):

- `cd backend && uv run ruff check tests/fixtures tests/unit/test_fixture_hygiene.py`
  → 종료 코드 0, **All checks passed!**.
- `cd backend && uv run ruff format --check tests/fixtures tests/unit/test_fixture_hygiene.py`
  → 종료 코드 0, **3 files already formatted**.
- `cd backend && uv run mypy`
  → 종료 코드 0, **Success: no issues found in 17 source files**. 다른 워커가 앞선 타입 오류를 수정한 뒤의 결과다.
- `cd backend && uv run pytest tests/unit/test_fixture_hygiene.py -q`
  → 종료 코드 0, **17 passed in 0.04s**.

코디네이터가 전체 검증의 이전 실패 증거와 단독 통과로 `worker_done(succeeded)` 인계를 지시했다.
`make check-backend` 전체 통과는 이 워커가 확인하지 않았으며, 병렬 웨이브 종료 후 코디네이터가 재실행한다.

## 남은 문제·다음 할 일

- 고용24 실제 오류 형식과 실제 날짜·급여 단위·링크 형식, 사람인 인증·한도 오류의 실제 JSON 메시지는 게이트 1에서 확인해야 한다.
- 합성 픽스처는 실제 API 동작 확인의 증거가 아니며, 승인 후 실제 응답을 정리해서 교체한다.
- 코디네이터 또는 후속 수집기 워커는 C-2/C-3에서 이 파일들을 읽는 가짜 클라이언트를 사용한다.
