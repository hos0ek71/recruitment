import asyncio
import os
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from tenacity import wait_none

from app.adapters.base import (
    PermanentSourceError,
    QuotaExceeded,
    RawItem,
    SourcePage,
    TransientSourceError,
)
from app.repositories import api_usage, collection, watermark
from app.repositories.models import (
    Base,
    CollectionQuery,
    CollectionRun,
    Criteria,
    Profile,
    QueryHit,
)
from app.services.collection import RunAlreadyActive, plan_queries, run_collection

pytestmark = pytest.mark.db


class FakeAdapter:
    source = "saramin"
    first_page = 0
    max_page_size = 2
    max_page = None

    def __init__(self, responses=(), *, block=None):
        self.responses = list(responses)
        self.calls = []
        self.block = block
        self.entered = asyncio.Event()

    async def fetch_page(self, query, page, page_size):
        self.calls.append((query, page, page_size))
        self.entered.set()
        if self.block is not None:
            await self.block.wait()
        response = self.responses.pop(0) if self.responses else (0, [])
        if isinstance(response, Exception):
            raise response
        total, ids = response
        return SourcePage(page, total, [RawItem(i, {"id": i}) for i in ids], "")


@pytest.fixture
async def factory(monkeypatch):
    url = os.environ["TEST_DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config("alembic.ini"), "head")
    engine = create_async_engine(url)
    tables = ", ".join('"' + table.name + '"' for table in Base.metadata.sorted_tables)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        async with engine.begin() as connection:
            await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        await engine.dispose()


async def seed(factory, keywords=("python",), regions=()):
    async with factory() as session:
        profile = Profile(raw_text="test")
        session.add(profile)
        await session.flush()
        criteria = Criteria(
            profile_id=profile.id,
            version=1,
            status="approved",
            keywords=list(keywords),
            regions=list(regions),
        )
        session.add(criteria)
        await session.commit()
        return criteria


async def execute(factory, adapter, criteria, **kwargs):
    return await run_collection(
        factory, {"saramin": adapter}, criteria.id, "manual", retry_wait=wait_none(), **kwargs
    )


async def result(factory, run_id):
    async with factory() as session:
        run = await session.get(CollectionRun, run_id)
        queries = list(
            (
                await session.scalars(
                    select(CollectionQuery)
                    .where(CollectionQuery.run_id == run_id)
                    .order_by(CollectionQuery.id)
                )
            ).all()
        )
        return run, queries


@pytest.mark.parametrize(
    ("responses", "status", "pages", "count"),
    [
        ([(3, ["1", "2"]), (3, ["3"])], "completed", 2, 3),
        ([(None, ["1"]), (None, [])], "completed", 2, 1),
        ([(3, ["1", "2"]), (3, ["2"]), (3, ["3"])], "completed", 3, 3),
        ([(0, [])], "completed", 1, 0),
    ],
)
async def test_pages(factory, responses, status, pages, count):
    criteria = await seed(factory)
    adapter = FakeAdapter(responses)
    run, queries = await result(factory, await execute(factory, adapter, criteria))
    query = queries[0]
    assert (query.status, query.pages_fetched, query.items_received) == (status, pages, count)
    assert run.status == "partial"  # work24 without a key remains visible
    assert run.api_calls_used == pages
    assert all(call[2] == 2 for call in adapter.calls)
    if query.total_reported is not None:
        assert query.total_reported == count
    async with factory() as session:
        hits = list(
            (
                await session.scalars(
                    select(QueryHit).where(QueryHit.collection_query_id == query.id)
                )
            ).all()
        )
        assert len(hits) == count


async def test_max_page_partial(factory):
    criteria = await seed(factory)
    adapter = FakeAdapter([(3, ["1", "2"])])
    adapter.max_page = 0
    _, queries = await result(factory, await execute(factory, adapter, criteria))
    assert queries[0].status == "partial"
    async with factory() as session:
        assert await watermark.get_watermark(session, "saramin", "python", "*") is None


@pytest.mark.parametrize(
    ("errors", "status", "calls"),
    [
        ([TransientSourceError("a"), TransientSourceError("b")], "completed", 3),
        ([TransientSourceError("a")] * 3, "error", 4),
        ([PermanentSourceError("bad")], "error", 2),
    ],
)
async def test_retry_and_continue(factory, errors, status, calls):
    criteria = await seed(factory, ("python", "java"))
    adapter = FakeAdapter([*errors, (0, [])])
    run, queries = await result(factory, await execute(factory, adapter, criteria))
    saramin = [q for q in queries if q.source == "saramin"]
    assert saramin[0].status == status
    assert saramin[1].status == "completed"
    assert run.api_calls_used == calls + (1 if status == "completed" else 0)
    async with factory() as session:
        assert (
            await api_usage.get_calls(
                session, datetime.now(ZoneInfo("Asia/Seoul")).date(), "saramin"
            )
            == run.api_calls_used
        )


@pytest.mark.parametrize("quota", [True, False])
async def test_deferred_source(factory, quota):
    criteria = await seed(factory, ("python", "java"))
    adapter = FakeAdapter([QuotaExceeded("quota")])
    run_id = await execute(factory, adapter, criteria, budgets={"saramin": 400 if quota else 0})
    run, queries = await result(factory, run_id)
    assert [q.status for q in queries if q.source == "saramin"] == ["deferred", "deferred"]
    assert run.status == "partial"
    assert run.api_calls_used == int(quota)
    assert len(adapter.calls) == int(quota)


async def test_completed_watermark_and_plan(factory):
    criteria = await seed(factory, ("python", "java"))
    adapter = FakeAdapter([(0, []), PermanentSourceError("bad")])
    run, _ = await result(factory, await execute(factory, adapter, criteria))
    async with factory() as session:
        stamp = await watermark.get_watermark(session, "saramin", "python", "*")
        assert stamp == run.started_at
        assert await watermark.get_watermark(session, "saramin", "java", "*") is None
        planned = await plan_queries(criteria, {"saramin": adapter}, session)
    query = next(p for p in planned if p.source == "saramin" and p.keyword == "python")
    assert query.since == stamp - timedelta(days=1)
    assert query.since.tzinfo is not None


async def test_missing_keys_and_failed_status(factory):
    criteria = await seed(factory)
    run_id = await run_collection(factory, {}, criteria.id, "manual")
    run, queries = await result(factory, run_id)
    assert run.status == "failed"
    assert len(queries) == 2
    assert all(q.status == "error" and q.error == "API 키 없음" for q in queries)
    assert run.finished_at is not None


async def test_lock_and_release(factory):
    criteria = await seed(factory)
    release = asyncio.Event()
    adapter = FakeAdapter(block=release)
    first = asyncio.create_task(execute(factory, adapter, criteria))
    await asyncio.wait_for(adapter.entered.wait(), 5)
    try:
        with pytest.raises(RunAlreadyActive):
            await execute(factory, FakeAdapter(), criteria)
    finally:
        release.set()
        await first
    await execute(factory, FakeAdapter(), criteria)


async def test_plan_deduplicates_source_region_and_estimates(factory):
    criteria = await seed(factory, regions=("29", "46"))
    saramin, work24 = FakeAdapter(), FakeAdapter()
    work24.source = "work24"
    async with factory() as session:
        previous = await collection.create_run(session, criteria.id, "manual")
        query = await collection.create_query(session, previous.id, "work24", "python", "29")
        await collection.update_query(
            session,
            query.id,
            status="completed",
            pages_fetched=3,
            items_received=5,
            total_reported=5,
        )
        stamp = datetime(2026, 10, 16, tzinfo=UTC)
        await watermark.set_watermark(session, "work24", "python", "29", stamp)
        await session.commit()
        planned = await plan_queries(criteria, {"saramin": saramin, "work24": work24}, session)
    work = [p for p in planned if p.source == "work24"]
    assert len(work) == 1
    assert work[0].estimated_calls == 3
    assert work[0].since == stamp - timedelta(days=1)
    assert len([p for p in planned if p.source == "saramin"]) == 2


async def test_all_sources_succeeded_and_work24_first_page(factory):
    criteria = await seed(factory)
    saramin, work24 = FakeAdapter(), FakeAdapter()
    work24.source, work24.first_page = "work24", 1
    run_id = await run_collection(
        factory, {"saramin": saramin, "work24": work24}, criteria.id, "schedule"
    )
    run, queries = await result(factory, run_id)
    assert run.status == "succeeded"
    assert all(q.status == "completed" for q in queries)
    assert work24.calls[0][1] == 1
    assert all(call[0].region is None for call in saramin.calls + work24.calls)


async def test_budget_includes_retries_and_does_not_block_other_source(factory):
    criteria = await seed(factory, ("python", "java"))
    saramin = FakeAdapter([TransientSourceError("retry")])
    work24 = FakeAdapter()
    work24.source = "work24"
    run_id = await run_collection(
        factory,
        {"saramin": saramin, "work24": work24},
        criteria.id,
        "manual",
        budgets={"saramin": 1, "work24": 2},
        retry_wait=wait_none(),
    )
    run, queries = await result(factory, run_id)
    assert [q.status for q in queries] == ["deferred", "deferred", "completed", "completed"]
    assert run.status == "partial"
    assert run.api_calls_used == 3
    assert len(saramin.calls) == 1


async def test_budget_uses_kst_calendar_day(factory, monkeypatch):
    from app.services import collection as service

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 10, 17, 15, 1, tzinfo=UTC)
            return value.astimezone(tz) if tz else value.replace(tzinfo=None)

    monkeypatch.setattr(service, "datetime", FrozenDatetime)
    criteria = await seed(factory)
    async with factory() as session:
        await api_usage.increment_calls(session, datetime(2026, 10, 17).date(), "saramin", 400)
        await session.commit()
    run_id = await execute(factory, FakeAdapter(), criteria)
    run, _ = await result(factory, run_id)
    assert run.api_calls_used == 1
    async with factory() as session:
        assert await api_usage.get_calls(session, datetime(2026, 10, 18).date(), "saramin") == 1


async def test_cancellation_keeps_full_plan_and_releases_lock(factory):
    criteria = await seed(factory, ("python", "java"))
    adapter = FakeAdapter(block=asyncio.Event())
    task = asyncio.create_task(execute(factory, adapter, criteria))
    await asyncio.wait_for(adapter.entered.wait(), 5)
    try:
        async with factory() as session:
            run = await session.scalar(select(CollectionRun))
        _, queries = await result(factory, run.id)
        assert len(queries) == 4  # every planned query is observable while running
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    run, queries = await result(factory, run.id)
    assert run.status == "failed"
    assert run.api_calls_used == 1
    assert all(q.status == "error" for q in queries)
    await execute(factory, FakeAdapter(), criteria)


async def test_unapproved_criteria_rejected_and_lock_released(factory):
    from app.services.collection import CriteriaNotApproved

    criteria = await seed(factory)
    async with factory() as session:
        row = await session.get(Criteria, criteria.id)
        row.status = "draft"
        await session.commit()
    with pytest.raises(CriteriaNotApproved):
        await execute(factory, FakeAdapter(), criteria)
    async with factory() as session:
        row = await session.get(Criteria, criteria.id)
        row.status = "approved"
        await session.commit()
    await execute(factory, FakeAdapter(), criteria)


async def test_repeated_page_without_new_ids_stops_partial(factory):
    criteria = await seed(factory)
    adapter = FakeAdapter([(5, ["1", "2", "3"])] * 3)
    adapter.max_page_size = 3
    run, queries = await result(factory, await execute(factory, adapter, criteria))
    query = queries[0]
    assert query.status == "partial"
    assert query.error == "페이지가 새 공고를 주지 않음(page=2)"
    assert query.pages_fetched == 3
    assert query.items_received == 3
    assert query.total_reported == 5
    assert run.api_calls_used == len(adapter.calls) == 3
    async with factory() as session:
        assert await watermark.get_watermark(session, "saramin", "python", "*") is None


async def test_new_ids_reset_consecutive_pages_without_progress(factory):
    criteria = await seed(factory)
    adapter = FakeAdapter(
        [
            (5, ["1"]),
            (5, ["1"]),
            (5, ["1", "2"]),
            (5, ["2"]),
            (5, ["2", "3", "4", "5"]),
        ]
    )
    run, queries = await result(factory, await execute(factory, adapter, criteria))
    query = queries[0]
    assert query.status == "completed"
    assert query.error is None
    assert query.items_received == query.total_reported == 5
    assert run.api_calls_used == len(adapter.calls) == 5
    async with factory() as session:
        assert await watermark.get_watermark(session, "saramin", "python", "*") == run.started_at
