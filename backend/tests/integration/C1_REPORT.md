# C-1 완료 보고

## 변경 파일

- `backend/app/db.py`: Settings를 받는 비동기 엔진 생성과 세션 팩토리. import 시 설정이나 DB 연결을 강제하지 않는다.
- `backend/app/domain/raw.py`: 공유 원본 입력 타입 `RawItem` (frozen dataclass).
- `backend/app/repositories/models.py`: SQLAlchemy 2 Mapped 모델 16개, text + CHECK, timestamptz, JSONB, text 배열, bigint identity.
- `backend/app/repositories/{criteria,collection,watermark,api_usage}.py`: 수집 단계 저장소.
- `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/script.py.mako`, `backend/migrations/versions/e98f227b8d6e_initial_schema.py`: 환경변수 DATABASE_URL 기반 동기 psycopg 마이그레이션.
- `backend/tests/integration/conftest.py`, `test_migrations.py`, `test_collection_repository.py`, `test_trgm_korean.py`: 테스트 DB 전용 마이그레이션/트랜잭션 롤백 테스트.
- 이 보고서. pyproject.toml/uv.lock은 워커가 변경하지 않았다. 코디네이터가 비동기 SQLAlchemy 필수 greenlet 의존성을 추가했다.

## 테이블

`profile`, `criteria`, `explore_keyword`, `collection_run`, `collection_query`,
`raw_posting`, `query_hit`, `query_watermark`, `api_usage`, `posting`,
`posting_source`, `filter_result`, `evaluation`, `user_mark`, `excluded_company`, `tool_call_log`.

posting의 회사명 정규화/최초 발견 시각 인덱스와 제목 GIN gin_trgm_ops 인덱스, raw_posting.run_id 인덱스를 포함한다.
첫 리비전은 pg_trgm 확장을 생성하고 모든 테이블을 생성한다. downgrade는 역순으로 테이블을 제거하고 DB 공용 확장은 유지한다.

## 저장소 함수 시그니처

모든 저장소 함수는 async이며 첫 인자는 `session: AsyncSession`이다. 저장소는 flush/execute만 하고 commit하지 않으므로 호출자가 트랜잭션 경계를 관리한다.

| 모듈 | 함수 (첫 session 인자 생략) | 반환 |
| --- | --- | --- |
| criteria | get_approved_criteria(criteria_id: int \| None) | Criteria \| None |
| collection | create_run(criteria_id: int, trigger: str) | CollectionRun |
| collection | finish_run(run_id: int, status: str, api_calls_used: int) | CollectionRun |
| collection | create_query(run_id: int, source: str, keyword: str, region: str, published_since: datetime \| None = None) | CollectionQuery |
| collection | update_query(query_id: int, *, status: str, pages_fetched: int, items_received: int, total_reported: int \| None = None, error: str \| None = None) | CollectionQuery |
| collection | upsert_raw_postings(source: str, items: Sequence[RawItem], run_id: int) | dict[str, int] (source_posting_id → raw_posting_id) |
| collection | add_query_hits(query_id: int, raw_posting_ids: Sequence[int]) | None |
| watermark | get_watermark(source: str, keyword: str, region: str) | datetime \| None |
| watermark | set_watermark(source: str, keyword: str, region: str, last_completed_at: datetime) | None |
| api_usage | get_calls(usage_date: date, source: str) | int |
| api_usage | increment_calls(usage_date: date, source: str, n: int) | int |

`get_approved_criteria`는 지정한 ID가 승인 상태일 때만 반환하며, None이면 version/id 내림차순의 최신 승인 조건을 반환한다.
RawItem은 `source_posting_id: str`, `payload: dict[str, Any]` 필드를 갖는다.
원본 upsert는 입력 배치 내부 중복 ID도 허용하고 마지막 항목을 저장한다. api_usage의 날짜는 호출자가 KST 기준 date로 전달한다.
`db.create_engine(settings: Settings) -> AsyncEngine`, `db.create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]`를 제공한다.

## 검증: 실패 → 통과

1. 테스트 먼저 작성 후 `uv run pytest tests/integration/test_migrations.py tests/integration/test_trgm_korean.py -q`: **1 failed, 1 passed**. 마이그레이션 미구현으로 `Path doesn't exist: .../backend/migrations` 실패를 확인했다.
2. 저장소 테스트 추가 후 최초 실행: SQLAlchemy asyncio import가 **greenlet 미설치로 exit 4**. 코디네이터가 sqlalchemy[asyncio] 의존성을 추가했다.
3. 첫 리비전 작성 전 저장소 테스트 실행: **1 failed, 3 errors**. `relation "api_usage" does not exist` 및 profile 테이블 부재로 실패했다.
4. 구현 후 strict mypy에서 RETURNING Insert의 변수 타입 오류 **3건**을 확인하고 수정했다.
5. `TEST_DATABASE_URL=<Makefile 기본 테스트 DB URL> uv run pytest tests/integration -q -s`: **7 passed**. 한글 pg_trgm 출력: **title=0.5, Korean-only=0.25**.
6. `make db-up && make check-backend`: **exit 0**, ruff check/format 통과, mypy 17개 소스 통과, **45 passed in 0.98s**. 아키텍처 검사 포함.
7. `DATABASE_URL=<같은 테스트 DB URL> uv run alembic check`: **exit 0**, `No new upgrade operations detected.`

테스트는 TEST_DATABASE_URL만 연결했으며 운영 DB 및 외부 API/LLM은 호출하지 않았다. upgrade → downgrade base → upgrade head가 성공했고 criteria.status='x'에서 IntegrityError를 검증했다.

## 남은 문제 / 다음 작업

C-1 범위의 미해결 사항은 없다. 어댑터 쪽에서 `app.domain.raw.RawItem`을 다시 내보내고, 수집 서비스에서 저장소를 조합하는 작업은 코디네이터의 후속 C-2~C-4 범위다.
커밋과 push는 실행하지 않았다.
