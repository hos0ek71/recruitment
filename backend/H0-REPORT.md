# H-0a 구현 및 검증 보고

2026-10-17 · task_a7eaa6034fb4 · ctx_7b1fd54dcf73

## 변경 내용

- Python 3.14 프로젝트와 uv 잠금 파일, 요청된 런타임/개발 의존성 전체를 구성했다.
- Ruff lint/format, mypy strict(packages=app), pytest/asyncio/db 마커를 구성했다.
- 앱 팩토리와 얇은 `/health` 라우터, 환경변수/저장소 루트 `.env` 기반 Settings를 추가했다.
- PostgreSQL 17과 개발/테스트 DB, 양쪽 pg_trgm 초기화, 로컬 전용 포트와 영구 볼륨을 구성했다.
- 테스트 DB reset은 localhost/127.0.0.1 + `_test` 접미사 + PostgreSQL 드라이버를 요구하며 연결 우회용 URL query를 거부한다.
- Make 검증 진입점과 GitHub Actions 워크플로를 추가했다. CI pnpm 버전은 병렬 워커가 만든 web/package.json의 packageManager와 같은 10.34.5다.

## 생성 파일

```text
.env.example
.github/workflows/ci.yml
Makefile
docker-compose.yml
docker/db/init/001-databases.sql
backend/.python-version
backend/pyproject.toml
backend/uv.lock
backend/app/__init__.py
backend/app/main.py
backend/app/config.py
backend/app/api/__init__.py
backend/app/api/health.py
backend/app/services/__init__.py
backend/app/repositories/__init__.py
backend/app/adapters/__init__.py
backend/app/domain/__init__.py
backend/scripts/__init__.py
backend/scripts/reset_test_db.py
backend/tests/__init__.py
backend/tests/conftest.py
backend/tests/unit/__init__.py
backend/tests/unit/test_health.py
backend/tests/unit/test_settings.py
backend/tests/unit/test_reset_test_db.py
backend/tests/integration/__init__.py
backend/tests/integration/test_db_connection.py
backend/tests/architecture/__init__.py
backend/H0-REPORT.md
```

## 실행 명령과 결과

| 명령/검증 | 종료 코드 | 실제 출력 요약 |
| --- | --- | --- |
| `cd backend && uv run pytest tests/unit/test_health.py` (구현 전) | 2 | `ModuleNotFoundError: No module named 'app.main'`, collection error 1개 |
| `cd backend && uv run pytest tests/unit/test_settings.py tests/unit/test_reset_test_db.py` (구현 전) | 2 | app.config와 scripts.reset_test_db 미구현으로 collection error 2개 |
| `uv run ruff check . --fix` (첫 작성) | 1 | E501 긴 줄 1개를 발견해 수정; Settings 경로 변경 후 발견한 E501도 formatter로 수정 |
| `cd backend && uv run ruff format . && uv run ruff check . && uv run mypy` | 0 | 20 files formatted, All checks passed, 9 source files 타입 검사 통과 |
| `cd backend && uv run pytest tests/unit` | 0 | 11 passed |
| `make db-up` | 0 | postgres:17 다운로드 및 신규 볼륨 초기화, 컨테이너 Healthy |
| `make check-backend` | 0 | Ruff lint/format, mypy strict, pytest 12 passed (DB 테스트 포함) |
| `/health` 기대 상태 코드를 200→500으로 일시 변경 후 `make check-backend` | 2 | `assert 200 == 500`, 1 failed / 11 passed; try/finally로 원본 복원 완료 |
| `TEST_DATABASE_URL=postgresql+psycopg://x:y@example.com:5432/recruitment make db-test-reset` | 2 | `Refusing reset`, DB에 연결하기 전에 거부 |
| `make db-test-reset` | 0 | `Reset test database: recruitment_test` |
| `docker compose exec -T db psql -U recruitment -d recruitment -c "SELECT current_database(), extname FROM pg_extension WHERE extname = 'pg_trgm';"` | 0 | recruitment / pg_trgm 1행 |
| 같은 psql 확인을 `-d recruitment_test`로 실행 | 0 | recruitment_test / pg_trgm 1행 |
| `cd backend && TEST_DATABASE_URL=postgresql+psycopg://recruitment:recruitment@127.0.0.1:1/recruitment_test uv run pytest -m db --tb=short -q` | 1 | 연결 거부로 fixture setup error 1개, skip 없음 |
| 복원 및 DB reset 후 `make check` | 0 | 컨테이너 Healthy, Ruff/mypy 통과, backend 12 passed, pnpm frozen install/lint/typecheck 통과, web 1 passed |

## AGENTS.md 검증 명령 제안

소유권 밖인 AGENTS.md는 수정하지 않았다. 코디네이터가 다음 다섯 줄을 반영하면 된다.

```text
make check          # DB 시작 + 백엔드/웹 전체 검사
make db-up          # PostgreSQL 개발/테스트 DB 시작
make db-test-reset  # 로컬 *_test DB만 재생성
make check-backend  # Ruff lint/format + mypy strict + pytest(DB 포함)
make check-web      # pnpm frozen install + lint + typecheck + test
```

## 남은 문제와 다음 할 일

- GitHub Actions는 작성했으며 원격 실행은 하지 않았다. 코디네이터의 commit/push 후 실제 CI 결과 확인이 필요하다.
- AGENTS.md, features.json, progress.md 갱신은 코디네이터 소유다.
- 외부 채용 API/LLM 호출, 전역 설치, commit/push는 하지 않았다.
- 다음 단계는 코디네이터가 H-0 전체 결과를 종합한 뒤 H-1 구조 테스트를 진행하는 것이다.
