# C-3 · 사람인 수정 공고 재수집과 원본 버전 보관

작업일: 2026-10-22. 기준 커밋: `94cac21`. 실제 채용 API 호출·의존성/락파일 변경·git commit 없음.

## 구현과 결정

- `SourceQuery.mode`는 `published`(기본)/`updated`이며, 기존 위치 인자 `extra`와 호환되도록 뒤에 추가했다. 사람인은 `supports_updated=True`, 고용24는 False다.
- 사람인 수정 모드는 `updated_min=<Unix timestamp>`, `sort=ua`를 사용하고 `published_min`은 보내지 않는다. 기존 published 경로는 `published_min`, `sort=pa`를 유지한다.
- 근거: [사람인 공식 채용 공고 명세](https://oapi.saramin.co.kr/guide/job-search), 2026-10-22 문서만 열람. 요청 변수표의 `ua`는 수정일 정순이고 `updated_min`은 수정일시 최소값이다. API 엔드포인트는 호출하지 않았다.
- 쿼리 계획은 전체 소스의 published를 먼저 실행하고 사람인 updated를 뒤에 둔다. updated는 해당 published 전체 수집 워터마크가 있을 때만 계획한다. 각 모드 워터마크에서 1일을 겹친다.
- 코디네이터 최종 승인: 최초 published 전체 수집 완료 시 updated 워터마크도 같은 실행 시작 시각으로 1회 초기화한다. 이미 존재하는 updated 워터마크는 published 실행이 건드리지 않는다. 기존 DB에서 published만 있으면 첫 계획 중 해당 published 값을 updated 워터마크로 1회 저장해 고정하고, 수집 실행 준비 트랜잭션과 함께 커밋한다. 이후 updated 쿼리 완료 시에만 전진한다.
- 이 초기화가 없으면 updated가 여러 날 deferred일 때 published의 최근 기준점을 매번 가져와 수정분을 놓칠 수 있음을 검토 중 발견했다. 3일 연속 published 완료/updated deferred 회귀 테스트와 기존 DB 기준점 고정 테스트를 추가했다.
- `query_watermark` 기본키는 `(source, keyword, region, mode)`다. `collection_query.mode`도 기본 published이며 기존 행을 유지한다. 이전 호출량 추정도 모드별로 조회한다. `/runs/{id}` 쿼리 응답에 mode가 나온다.
- `UpsertResult(ids: dict[str, int], changed_ids: frozenset[int])`로 전체 ID 매핑과 신규/변경 ID 집합을 반환한다(코디네이터가 명시적 반환 타입 승인).
- 신규 raw는 v1, 내용 해시 변경은 다음 버전을 추가하고 최신 raw payload를 갱신한다. 동일 해시는 fetched_at/run_id만 갱신한다. 기존 payload를 변환하거나 무시 필드를 제거하여 저장하지 않는다.
- 동일 페이지의 중복 ID는 마지막 항목을 사용한다(기존 동작). raw 행 잠금으로 버전 번호 할당을 직렬화하며 여러 ID는 정렬하여 잠근다.
- `payload_changes()`는 순수 함수로 JSON Pointer 경로와 이전/새 값을 반환한다. 딕셔너리는 재귀 비교, 리스트는 값 전체 비교, 추가/삭제의 없는 값은 None이다. 이 함수 자체는 카운트 필드도 비교한다.

## 해시 무시 목록과 근거

SHA-256, UTF-8, `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"))`를 사용한다. 중첩 객체도 키가 정렬된다.

| 소스 | 제외하는 최상위 필드 | 근거 |
| --- | --- | --- |
| 사람인 | `read-cnt`, `apply-cnt` | 공식 응답 필드표: fields=count 선택 시 조회수·지원자수. 채용 내용 수정 없이 변하는 활동 카운트다. 공식 JSON 예시에도 같은 이름으로 나온다. |
| 고용24 | 없음 | 변동성 필드라는 공식 근거를 확인한 항목이 없어 임의 제외하지 않는다. |

`modification-timestamp`는 해시에 포함하며, 있으면 Unix timestamp를 UTC `source_modified_at`으로 저장한다. 누락/잘못된 시각은 원본은 그대로 두고 파생 열만 NULL이다. `list_counts.json`은 기존 합성 공고에 공식 카운트 필드와 합성값을 더한 픽스처이고 SOURCES.md에 기록했다.

## 변경 파일

- `backend/app/adapters/{base,saramin,work24}.py`: 모드·지원 여부·사람인 요청 인자.
- `backend/app/services/collection.py`: 수정 쿼리 계획·모드별 기준점·실행 기록·runs 응답.
- `backend/app/repositories/{models,collection,watermark}.py`: 모드별 워터마크, 버전 모델·upsert·해시·비교 함수.
- `backend/migrations/versions/c3b491fe8820_updated_queries_raw_versions.py`: 호환 업그레이드, 기존 raw 해시/v1 이행, downgrade.
- `backend/tests/unit/adapters/test_saramin.py`, `backend/tests/unit/test_payload_changes.py`: 요청 인자·원본 보존·해시·차이 비교.
- `backend/tests/integration/{test_collection_repository,test_collection_service,test_migrations,test_runs_api}.py`: 버전·메타데이터·워터마크·예산·API·데이터 이행 검증.
- `backend/tests/fixtures/saramin/list_counts.json`, `backend/tests/fixtures/SOURCES.md`: 선택 필드 픽스처와 출처.
- 이 보고서. 기존 작업 트리의 다른 문서 변경은 수정하지 않았다.

## 테스트 먼저: 실패 → 구현 → 통과

실제 실행한 출력 요약이다. raw 로그는 `/tmp/c3-red.log`, `/tmp/c3-red-behavior.log`, `/tmp/c3-red-migration.log`, `/tmp/c3-green.log`, `/tmp/c3-make-check.log`, `/tmp/c3-make-check-final.log`, `/tmp/c3-red-baseline.log`, `/tmp/c3-green-baseline.log`, `/tmp/c3-make-check-complete.log`에 있다.

1. 구현 전 해시·비교 테스트:

```text
uv run pytest tests/unit/test_payload_changes.py ... -q
ImportError: cannot import name 'content_hash' from 'app.repositories.collection'
1 error in 0.18s
```

2. 구현 전 신규 동작 5개를 따로 실행(같은 테스트 DB 환경변수 지정):

```text
uv run pytest tests/unit/adapters/test_saramin.py::test_updated_parameters \
 tests/integration/test_collection_repository.py::test_version_history_and_changed_ids \
 tests/integration/test_collection_repository.py::test_mode_watermarks_are_independent \
 tests/integration/test_collection_service.py::test_updated_plan_order_fallback_and_own_watermark \
 tests/integration/test_collection_service.py::test_updated_completes_own_watermark -q
FAILED ...test_updated_parameters - TypeError [mode 없음]
FAILED ...test_version_history_and_changed_ids [RawPostingVersion 없음]
FAILED ...test_mode_watermarks_are_independent [mode 인자 없음]
FAILED ...test_updated_plan_order_fallback_and_own_watermark [supports_updated 없음]
FAILED ...test_updated_completes_own_watermark [CollectionQuery.mode 없음]
5 failed in 0.45s
```

3. 데이터 이행 테스트도 구현 전 실행:

```text
uv run pytest tests/integration/test_migrations.py::test_version_migration_backfills_original_and_modes -q
ImportError: cannot import name 'content_hash' ...
1 failed in 0.07s
```

4. 구현 후 어댑터·비교·저장소·서비스·migration·runs 관련 묶음:

```text
97 passed in 5.85s
```

마이그레이션 테스트는 실제 테스트 PostgreSQL에서 upgrade → downgrade → upgrade를 실행한다. 기존 스키마에 raw 행을 넣은 뒤 v1/payload/hash/source_modified_at 이행과 기본 published 모드를 검사하고, updated 워터마크도 넣어 downgrade 기본키 충돌이 없음을 검증한다.

5. 첫 전체 검사 `make check`: 종료 코드 **2**, backend `1 failed, 217 passed in 6.42s`. 기존 `test_regdate_override_and_month_end`가 SourceQuery의 위치 인자 extra 호환성 회귀를 검출했다. 새 mode를 extra 뒤로 이동하여 수정했다. 초기 lint의 줄 길이·suppress 지적도 수정했다.


6. 위치 인자 호환성 수정 후 전체 검사: 종료 코드 **0**, backend `218 passed in 5.20s`, 웹 1개 통과. 이후 deferred 기준점 검토에서 추가 보완이 필요해 아래 테스트를 먼저 추가했다.

```text
uv run pytest tests/integration/test_collection_service.py::test_deferred_updates_keep_initial_baseline_across_days \
 tests/integration/test_collection_service.py::test_legacy_watermark_is_frozen_on_first_plan -q
assert None == datetime.datetime(2026, 10, 17, 0, 0, tzinfo=datetime.timezone.utc)
2 failed in 0.44s
```

보완 구현 후 서비스 테스트 묶음: `26 passed in 3.46s`. 3일 연속 published 기준점이 전진하고 updated는 deferred여도 updated 기준점과 since가 최초 값을 유지함을 확인했다.

7. **최종 `make check`: 종료 코드 0.** Docker DB healthy, 아래 모든 검사 완료:

```text
All checks passed!
57 files already formatted
Success: no issues found in 24 source files
220 passed in 6.18s
pnpm lint: success
pnpm typecheck: success
Test Files  1 passed (1)
Tests       1 passed (1)
```

`git diff --check`도 종료 코드 0이다. DB 검증 환경변수는 모든 해당 실행에 프로젝트 지정값 `postgresql+psycopg://recruitment:recruitment@127.0.0.1:5433/recruitment_test`를 사용했다(`make`는 자동 주입).

## 남은 위험과 다음 할 일

- 실제 사람인 API 응답으로는 검증하지 않았다. 명세·합성 픽스처·respx 기반이며 게이트 1의 승인된 실연동 검증이 남아 있다.
- raw payload는 수신 딕셔너리 그대로 JSONB에 저장한다. 카운트만 바뀐 경우에는 요구대로 fetched_at/run_id만 갱신하므로 raw payload와 마지막 버전의 카운트는 이전 원본 값이다.
- 버전 할당 안전성을 위해 공고별 행 잠금과 쿼리를 사용한다. 단일 사용자·페이지 최대 110건 범위이며 대량 성능 부하는 측정하지 않았다.
- downgrade는 새 버전 테이블과 updated 워터마크를 제거한다. 최신 raw payload와 published 워터마크는 남지만, 이전 버전 이력은 rollback 대상이다.
- N-1/F-1은 후속 단계에서 `UpsertResult.changed_ids`를 재판정 대상으로 연결해야 한다. 이번에는 반환 계약까지 구현했다.
- C-3 feature 통과 표시와 최종 리뷰/커밋은 코디네이터가 처리한다. 이 워커는 `features.json`과 gate를 수정하지 않았다.
