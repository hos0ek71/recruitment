# AGENTS.md: 공채 모아보기

모든 코딩 에이전트(Claude Code 오케스트레이터, Orca가 띄운 Codex 워커)가 따르는 공통 규칙의 원본이다.
Codex는 이 파일을 자동으로 읽고, Claude Code는 `CLAUDE.md`의 `@AGENTS.md` 임포트로 읽는다.
이 파일은 지도다. 짧게 유지하고 자세한 내용은 아래 문서로 연결한다.

## 프로젝트

사람인·고용24 공식 API로 조건에 맞는 신입 공고를 마지막 페이지까지 모은다. 확정 조건은 코드로 거르고 공고마다 탈락 사유를 남긴다.
AI는 조건 생성, 적합도 평가, 추가 탐색에만 쓴다. 사용자 1명 전용 웹 서비스다.
스택: Python·FastAPI, PostgreSQL(JSONB, pg_trgm), APScheduler, httpx·tenacity, React·TypeScript, Docker Compose.

## 문서 지도 (필요할 때만 읽는다)

| 문서 | 내용 · 언제 읽나 |
| --- | --- |
| `공채 모아보기 MVP 설계 문서.md` | 제품 기준 명세. 기능·데이터 모델·API·필터 규칙 |
| `docs/mvp-design-review.md` | 설계 검증 결과와 구현 전 결정 사항. 설계 문서와 충돌하면 여기서 "확정"된 결정이 우선 |
| `docs/harness/features.json` | 단계별 기능 목록, 수용 기준, 통과 여부 |
| `docs/harness/progress.md` | 세션 인계 기록. 작업 시작 전에 최신 항목을 읽는다 |
| `docs/harness/task-spec-template.md` | 워커 작업 명세 형식 |
| `docs/research/` | 하네스·채용 API 조사 근거. 필요할 때만 |

## 작업 규칙

1. **모호하면 묻는다.** 추측으로 진행하지 않는다. Orca 워커는 로컬 질문 TUI를 열지 말고 preamble의 `ask` 명령으로 코디네이터에게 묻는다. 코디네이터는 필요하면 사용자에게 묻는다.
2. **기능 코드는 테스트를 먼저 쓴다.** 실패하는 테스트를 쓰고, 실패를 확인하고, 최소 구현 후 통과를 확인한다. 보고에 실패와 통과 출력을 모두 남긴다.
3. **작업 명세의 Ownership 밖 파일은 고치지 않는다.** 필요하면 묻는다.
4. **한 번에 기능 하나.** `features.json`의 `passes`는 검증 증거가 있을 때만 `true`로 바꾼다. 항목을 지우거나 수용 기준을 약하게 고쳐서 완료시키지 않는다. 게이트(`G-*`)는 사용자 승인 후에만 바꾼다.
5. **실행하지 않은 검사를 통과로 보고하지 않는다.** 빈 테스트 묶음도 증거가 아니다.
6. **비밀값은 환경변수로만 다룬다.** `.env`, API 키, LLM 키, 개인 프로필 원문을 커밋하지 않는다. 픽스처에 저장하는 응답에서도 키와 개인정보를 지운다.
7. **테스트에서 외부 API·LLM을 실제로 호출하지 않는다.** 저장한 응답 픽스처와 가짜 클라이언트를 쓴다. 실제 호출은 사람인 일일 한도(500회)를 소모하므로 명시적 지시가 있을 때만 한다.
8. **git commit·push는 코디네이터나 사용자가 지시할 때만 한다.**

## 제품 불변식 (어기면 버그다)

- 확정 필터는 코드로만 판단하고, 탈락한 공고마다 사유 코드를 남긴다. AI는 공고를 탈락시키지 않고 수집 범위도 정하지 않는다.
- 판단할 정보가 없으면 탈락시키지 않는다. '확인 필요'로 통과시킨다.
- 수집 쿼리는 마지막 페이지까지 받은 뒤에만 완료로 기록한다. 실패했거나 끝까지 받지 못한 쿼리를 숨기지 않는다.
- 소스 원본 응답(`raw_posting`)은 그대로 저장하고 정규화 결과와 분리한다.
- AI 출력은 JSON 스키마로 검증한다. 실패하면 버리고, 추측으로 고쳐 쓰지 않는다.
- 승인된 조건(`criteria.status = approved`)만 수집에 쓴다. AI가 새로 시도한 키워드는 사용자가 승인하기 전까지 매일 수집에 넣지 않는다.
- 스크래핑이나 브라우저 자동화로 채용 사이트를 수집하지 않는다. 지원 링크는 항상 원문 URL이다.

## 아키텍처 경계

- 라우터는 얇게 둔다. 라우터 → 서비스 → 저장소 방향으로만 의존한다. 라우터에 SQL이나 외부 호출을 두지 않는다.
- 사람인·고용24·LLM 호출은 어댑터 모듈 뒤에 둔다. 서비스는 어댑터 인터페이스만 안다.
- 서비스 함수는 FastAPI `Request` 같은 HTTP 객체에 의존하지 않는다. 나중에 같은 함수를 MCP 도구로 감쌀 수 있어야 한다.
- 위 규칙은 H-1에서 구조 테스트로 강제한다.

## 검증 명령

작업을 끝내기 전에 `make check`를 돌리고 종료 코드 0을 확인한다. Docker가 실행 중이어야 한다.

| 명령 | 하는 일 |
| --- | --- |
| `make check` | 테스트 DB를 띄우고 백엔드와 웹 검사를 모두 실행한다. 완료 판정은 이것 하나로 한다 |
| `make check-backend` | `backend/`에서 ruff lint, ruff format 검사, mypy(strict), pytest를 실행한다 |
| `make check-web` | `web/`에서 pnpm install(lockfile 고정), ESLint, tsc, Vitest를 실행한다 |
| `make db-up` | PostgreSQL 17(127.0.0.1:5433, `recruitment`과 `recruitment_test`, pg_trgm)을 띄운다 |
| `make db-test-reset` | 로컬 `*_test` DB만 다시 만든다. 원격이거나 `_test`가 아닌 DB는 거부한다 |

- 개별 테스트: `cd backend && uv run pytest tests/unit/test_health.py -q`. DB가 필요한 테스트에는 `@pytest.mark.db`를 붙인다.
- DB 테스트를 직접 돌릴 때는 `TEST_DATABASE_URL=postgresql+psycopg://recruitment:recruitment@127.0.0.1:5433/recruitment_test`를 붙인다. `make`는 이 값을 자동으로 넣는다.
- 의존성(`backend/pyproject.toml`, `web/package.json`)과 락파일은 코디네이터 승인 없이 바꾸지 않는다.

## 완료 보고 형식

변경한 파일, 실행한 검증 명령과 결과(실패 포함), 남은 문제, 다음 할 일.
