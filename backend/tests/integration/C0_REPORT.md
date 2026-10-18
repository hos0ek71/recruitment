# C-0 소스 설정과 실행 오류 분리

## 변경 파일과 동작

- `.env.example`: `ENABLED_SOURCES=`와 설명 주석.
- `backend/app/config.py`: `ENABLED_SOURCES`, `resolve_enabled_sources`. 미설정·빈 문자열·공백 문자열은 키가 있는 소스를 선택하며 명시 목록은 이름과 키를 검증하고 중복을 제거한다.
- `backend/app/main.py`: lifespan 시작 시 설정을 검증하며 선택한 소스만 어댑터를 생성한다. 요청 시 lazy 초기화 경로에서도 검증한다.
- `backend/app/services/collection.py`: 어댑터가 있는 소스만 계획하고 실행마다 사용 소스 목록을 저장·조회한다. 소스 0개는 실행 생성 전에 거절하고 잠금을 해제한다. 기존 `InvalidCriteria` 처리로 POST 응답은 422가 된다.
- `backend/app/repositories/collection.py`, `backend/app/repositories/models.py`: 실행의 `enabled_sources` 영속화.
- `backend/migrations/versions/a721bb93c012_collection_run_enabled_sources.py`: 기존 리비전을 수정하지 않고 `text[] NOT NULL DEFAULT '{}'` 추가 및 downgrade 구현.
- `backend/tests/unit/test_settings.py`, `backend/tests/integration/test_collection_service.py`, `backend/tests/integration/test_runs_api.py`, `backend/tests/integration/test_migrations.py`: 아래 회귀 검증.

구조 테스트 규칙에서 `app.config`는 composition root로 취급된다. 따라서 기존 `app.adapters.base.SourceName`을 사용했고 타입의 도메인 이동은 필요하지 않았다. 라우터와 의존성 모듈 수정도 필요하지 않았다.

## RED → GREEN 증거

구현 전 실행:

```text
cd backend && uv run pytest tests/unit/test_settings.py -q
ImportError: cannot import name 'resolve_enabled_sources' from 'app.config'
1 error in 0.24s (exit 2)

cd backend && TEST_DATABASE_URL=postgresql+psycopg://recruitment:recruitment@127.0.0.1:5433/recruitment_test uv run pytest tests/integration/test_collection_service.py tests/integration/test_runs_api.py tests/integration/test_migrations.py -q
10 failed, 17 passed in 4.18s (exit 1)
```

통합 RED: `test_pages` 4개, `test_retry_and_continue` 1개, `test_only_enabled_sources_are_planned_and_recorded`, `test_cancellation_keeps_full_plan_and_releases_lock`, `test_runs_api`, `test_no_sources_returns_422_without_run_and_releases_lock`, `test_enabled_sources_migration_roundtrip_preserves_existing_run`.

구현 후 실행:

```text
uv run pytest tests/unit/test_settings.py -q
14 passed in 0.48s (exit 0; 이후 실제 lifespan 어댑터 선택 테스트 3개 추가)

TEST_DATABASE_URL=postgresql+psycopg://recruitment:recruitment@127.0.0.1:5433/recruitment_test uv run pytest tests/integration/test_collection_service.py tests/integration/test_runs_api.py tests/integration/test_migrations.py -q
27 passed in 4.10s (exit 0)

make check
첫 실행: ruff E501 테스트 SQL 문자열 113자 → 문자열을 나누어 수정 (exit 2)
최종 실행: ruff check/format 통과, mypy 통과, backend 207 passed in 5.63s,
웹 ESLint/tsc 통과, Vitest 1 passed (exit 0)

git diff --check
출력 없음 (exit 0)
```

## 테스트 이름

새 테스트:

- `test_resolve_enabled_sources`: 키 기준 자동 선택, 명시 선택, 양쪽 키가 있어도 제한 가능, 쉼표/공백/중복, 빈 값/공백 값 자동 선택.
- `test_resolve_enabled_sources_rejects_invalid_configuration`: 각 소스 키 누락과 모르는 이름의 ValueError.
- `test_lifespan_rejects_invalid_sources_before_startup`: 실제 lifespan 시작 검증.
- `test_lifespan_builds_only_explicitly_enabled_adapters`: 양쪽 키가 있을 때 사람인 단독/고용24 단독/둘 다 선택. HTTP 호출 없음.
- `test_only_enabled_sources_are_planned_and_recorded`: 기존 키 누락을 error로 기대하던 테스트 대체; 사람인 쿼리만 생성, succeeded, enabled_sources 저장.
- `test_real_errors_still_fail_run`: 실제 PermanentSourceError는 error/failed.
- `test_no_sources_returns_422_without_run_and_releases_lock`: 422, 실행 0개, 소스 설정 후 202.
- `test_enabled_sources_migration_roundtrip_preserves_existing_run`: head→기존 리비전→head, 컬럼 삭제/복원, 기존 행 기본값 빈 목록과 NOT NULL·text[] 확인.

수정된 테스트:

- `test_pages`: 사람인만 있으면 succeeded, 쿼리 1개, enabled_sources=['saramin'].
- `test_retry_and_continue`: 실제 오류가 남으면 partial, 재시도 성공으로 모든 쿼리가 완료되면 succeeded.
- `test_cancellation_keeps_full_plan_and_releases_lock`: 사용하는 소스 쿼리만 남도록 개수 변경.
- `test_runs_api`: GET 응답 succeeded 및 enabled_sources=['saramin'], 고용24 쿼리 없음.

기존 quota/deferred, 예산 및 재시도, partial 페이지, 잠금·취소 테스트도 전체 검사에서 통과했다. 외부 API·LLM 실제 호출, 의존성 변경, commit은 하지 않았다.

## 남은 문제와 다음 할 일

구현상 남은 문제 없음. 코디네이터의 명시적 답변에 따라 `docs/harness/features.json`은 수정하지 않았으며 C-0 passes/evidence 갱신은 코디네이터가 검증 후 수행한다. 기존에 변경되어 있던 문서들은 보존했다.
