"""Collection planning, execution and background task ownership without HTTP dependencies."""

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential
from tenacity.wait import wait_base

from app.adapters.base import (
    PermanentSourceError,
    QuotaExceeded,
    SourceAdapter,
    SourceName,
    SourceQuery,
    TransientSourceError,
)
from app.adapters.saramin_codes import to_loc_mcd as saramin_region
from app.adapters.work24_codes import region_code as work24_region
from app.repositories import api_usage, collection, watermark
from app.repositories import criteria as criteria_repository
from app.repositories.models import Criteria

SessionFactory = async_sessionmaker[AsyncSession]
DEFAULT_BUDGETS: Mapping[SourceName, int] = {"saramin": 400, "work24": 1000}
KST = ZoneInfo("Asia/Seoul")


class RunAlreadyActive(Exception):
    pass


class InvalidCriteria(ValueError):
    pass


class CriteriaNotApproved(InvalidCriteria):
    pass


@dataclass(frozen=True)
class PlannedQuery(SourceQuery):
    estimated_calls: int = 1


async def plan_queries(
    criteria: Criteria, adapters: Mapping[SourceName, SourceAdapter], session: AsyncSession
) -> list[PlannedQuery]:
    planned: list[PlannedQuery] = []
    seen: set[tuple[str, str, str | None]] = set()
    for source, adapter in adapters.items():
        page_size = adapter.max_page_size
        mapping = saramin_region if source == "saramin" else work24_region
        regions: list[str | None] = list(criteria.regions) if criteria.regions else [None]
        for keyword in criteria.keywords:
            for region in regions:
                try:
                    source_region = mapping(region) if region is not None else None
                except ValueError as exc:
                    raise InvalidCriteria(f"지원하지 않는 지역 코드: {region}") from exc
                key = (source, keyword, source_region)
                if key in seen:
                    continue
                seen.add(key)
                stored_region = region or "*"
                stamp = await watermark.get_watermark(session, source, keyword, stored_region)
                # TIMESTAMPTZ should always be aware; normalize defensively for callers.
                since = (
                    (
                        (
                            stamp.replace(tzinfo=UTC)
                            if stamp.tzinfo is None
                            else stamp.astimezone(UTC)
                        )
                        - timedelta(days=1)
                    )
                    if stamp
                    else None
                )
                total = await collection.previous_total(session, source, keyword, stored_region)
                planned.append(
                    PlannedQuery(
                        source=source,
                        keyword=keyword,
                        region=region,
                        since=since,
                        estimated_calls=(ceil(total / page_size) if total is not None else 1),
                    )
                )
    return planned


@dataclass
class PreparedRun:
    run_id: int
    started_at: datetime
    queries: list[PlannedQuery]
    query_ids: list[int]
    lock_session: AsyncSession

    async def release(self) -> None:
        try:
            await collection.release_execution_lock(self.lock_session)
        finally:
            await self.lock_session.close()


async def _prepare(
    factory: SessionFactory,
    adapters: Mapping[SourceName, SourceAdapter],
    criteria_id: int | None,
    trigger: str,
) -> PreparedRun:
    lock_session = factory()
    try:
        if not await collection.try_execution_lock(lock_session):
            raise RunAlreadyActive("수집이 이미 실행 중입니다")
        if not adapters:
            raise InvalidCriteria("사용할 수 있는 소스가 없다(키 설정 필요)")
        async with factory() as session:
            criteria = await criteria_repository.get_approved_criteria(session, criteria_id)
            if criteria is None:
                raise CriteriaNotApproved("존재하는 승인된 조건이 필요합니다")
            queries = await plan_queries(criteria, adapters, session)
            run = await collection.create_run(session, criteria.id, trigger, list(adapters))
            query_ids = []
            for planned in queries:
                row = await collection.create_query(
                    session,
                    run.id,
                    planned.source,
                    planned.keyword,
                    planned.region or "*",
                    planned.since,
                )
                query_ids.append(row.id)
            await session.commit()
            return PreparedRun(
                run.id, run.started_at.astimezone(UTC), queries, query_ids, lock_session
            )
    except BaseException:
        # Unlock even when planning or persistence fails, before returning to pool.
        try:
            await collection.release_execution_lock(lock_session)
        finally:
            await lock_session.close()
        raise


async def _execute(
    factory: SessionFactory,
    adapters: Mapping[SourceName, SourceAdapter],
    prepared: PreparedRun,
    budgets: Mapping[SourceName, int],
    retry_wait: wait_base | None,
) -> int:
    calls = 0
    statuses: list[str] = []
    deferred: set[SourceName] = set()
    try:
        async with factory() as session:
            for planned, query_id in zip(prepared.queries, prepared.query_ids, strict=True):
                adapter = adapters[planned.source]
                status, error = "pending", None
                pages, total = 0, None
                received: set[str] = set()
                pages_without_progress = 0
                if planned.source in deferred:
                    status = "deferred"
                else:
                    page = adapter.first_page
                    while status == "pending":
                        if adapter.max_page is not None and page > adapter.max_page:
                            status = "partial"
                            break
                        try:
                            async for attempt in AsyncRetrying(
                                stop=stop_after_attempt(3),
                                wait=retry_wait if retry_wait is not None else wait_exponential(),
                                retry=retry_if_exception_type(TransientSourceError),
                                reraise=True,
                            ):
                                with attempt:
                                    today = datetime.now(KST).date()
                                    used = await api_usage.get_calls(session, today, planned.source)
                                    if used + 1 > budgets.get(
                                        planned.source, DEFAULT_BUDGETS[planned.source]
                                    ):
                                        raise QuotaExceeded("일일 호출 예산 초과")
                                    await api_usage.increment_calls(
                                        session, today, planned.source, 1
                                    )
                                    await collection.record_call(session, prepared.run_id)
                                    await session.commit()
                                    calls += 1
                                    response = await adapter.fetch_page(
                                        planned, page, adapter.max_page_size
                                    )
                            ids = await collection.upsert_raw_postings(
                                session, planned.source, response.items, prepared.run_id
                            )
                            await collection.add_query_hits(session, query_id, list(ids.values()))
                            if response.items and not (ids.keys() - received):
                                pages_without_progress += 1
                            else:
                                pages_without_progress = 0
                            received.update(ids)
                            pages += 1
                            total = response.total
                            if pages_without_progress >= 2:
                                status = "partial"
                                error = f"페이지가 새 공고를 주지 않음(page={page})"
                            elif not response.items or (
                                total is not None and len(received) >= total
                            ):
                                status = "completed"
                            await collection.update_query(
                                session,
                                query_id,
                                status=status,
                                pages_fetched=pages,
                                total_reported=total,
                                items_received=len(received),
                            )
                            await session.commit()
                            page += 1
                        except QuotaExceeded as exc:
                            status, error = "deferred", str(exc)
                            deferred.add(planned.source)
                        except (TransientSourceError, PermanentSourceError) as exc:
                            status, error = "error", str(exc)
                await collection.update_query(
                    session,
                    query_id,
                    status=status,
                    pages_fetched=pages,
                    total_reported=total,
                    items_received=len(received),
                    error=error,
                )
                if status == "completed":
                    await watermark.set_watermark(
                        session,
                        planned.source,
                        planned.keyword,
                        planned.region or "*",
                        prepared.started_at,
                    )
                await session.commit()
                statuses.append(status)
            status = (
                "succeeded"
                if all(s == "completed" for s in statuses)
                else "failed"
                if all(s == "error" for s in statuses)
                else "partial"
            )
            await collection.finish_run(session, prepared.run_id, status, calls)
            await session.commit()
        return prepared.run_id
    except BaseException:
        # Unexpected errors and cancellation must not leave a perpetually running run.
        async with factory() as session:
            rows = await collection.get_queries(session, prepared.run_id)
            for row in rows:
                if row.status == "pending":
                    await collection.update_query(
                        session,
                        row.id,
                        status="error",
                        pages_fetched=row.pages_fetched,
                        total_reported=row.total_reported,
                        items_received=row.items_received,
                        error="수집 실행 중단",
                    )
            status = "partial" if any(row.status == "completed" for row in rows) else "failed"
            await collection.finish_run(session, prepared.run_id, status, calls)
            await session.commit()
        raise
    finally:
        await prepared.release()


async def run_collection(
    session_factory: SessionFactory,
    adapters: Mapping[SourceName, SourceAdapter],
    criteria_id: int | None,
    trigger: str,
    *,
    budgets: Mapping[SourceName, int] | None = None,
    retry_wait: wait_base | None = None,
) -> int:
    prepared = await _prepare(session_factory, adapters, criteria_id, trigger)
    return await _execute(
        session_factory,
        adapters,
        prepared,
        DEFAULT_BUDGETS if budgets is None else budgets,
        retry_wait,
    )


async def get_run(factory: SessionFactory, run_id: int) -> dict[str, Any] | None:
    async with factory() as session:
        run = await collection.get_run(session, run_id)
        if run is None:
            return None
        rows = await collection.get_queries(session, run_id)
        return {
            "run_id": run.id,
            "criteria_id": run.criteria_id,
            "trigger": run.trigger,
            "status": run.status,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "api_calls_used": run.api_calls_used,
            "enabled_sources": run.enabled_sources,
            "queries": [
                {
                    name: getattr(row, name)
                    for name in (
                        "source",
                        "keyword",
                        "region",
                        "status",
                        "pages_fetched",
                        "total_reported",
                        "items_received",
                        "error",
                    )
                }
                for row in rows
            ],
        }


class CollectionController:
    """Own tasks until shutdown; reserve the database lock before returning 202."""

    def __init__(
        self,
        factory: SessionFactory,
        adapters: Mapping[SourceName, SourceAdapter],
        *,
        budgets: Mapping[SourceName, int] | None = None,
    ) -> None:
        self.factory = factory
        self.adapters = adapters
        self.budgets = DEFAULT_BUDGETS if budgets is None else budgets
        self.tasks: set[asyncio.Task[int]] = set()
        self.errors: list[BaseException] = []

    async def start(self, criteria_id: int) -> int:
        prepared = await _prepare(self.factory, self.adapters, criteria_id, "manual")
        task = asyncio.create_task(
            _execute(self.factory, self.adapters, prepared, self.budgets, None)
        )
        self.tasks.add(task)
        task.add_done_callback(self._finished)
        return prepared.run_id

    def _finished(self, task: asyncio.Task[int]) -> None:
        self.tasks.discard(task)
        if not task.cancelled() and (error := task.exception()) is not None:
            self.errors.append(error)

    async def wait(self) -> None:
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

    async def get(self, run_id: int) -> dict[str, Any] | None:
        return await get_run(self.factory, run_id)
