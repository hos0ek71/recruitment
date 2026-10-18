from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.raw import RawItem
from app.repositories.models import CollectionQuery, CollectionRun, QueryHit, RawPosting


async def create_run(
    session: AsyncSession, criteria_id: int, trigger: str, enabled_sources: Sequence[str] = ()
) -> CollectionRun:
    run = CollectionRun(
        criteria_id=criteria_id, trigger=trigger, enabled_sources=list(enabled_sources)
    )
    session.add(run)
    await session.flush()
    return run


async def finish_run(
    session: AsyncSession, run_id: int, status: str, api_calls_used: int
) -> CollectionRun:
    statement = (
        update(CollectionRun)
        .where(CollectionRun.id == run_id)
        .values(status=status, api_calls_used=api_calls_used, finished_at=func.now())
        .returning(CollectionRun)
    )
    return (await session.execute(statement)).scalar_one()


async def create_query(
    session: AsyncSession,
    run_id: int,
    source: str,
    keyword: str,
    region: str,
    published_since: datetime | None = None,
) -> CollectionQuery:
    query = CollectionQuery(
        run_id=run_id,
        source=source,
        keyword=keyword,
        region=region,
        published_since=published_since,
    )
    session.add(query)
    await session.flush()
    return query


async def update_query(
    session: AsyncSession,
    query_id: int,
    *,
    status: str,
    pages_fetched: int,
    items_received: int,
    total_reported: int | None = None,
    error: str | None = None,
) -> CollectionQuery:
    statement = (
        update(CollectionQuery)
        .where(CollectionQuery.id == query_id)
        .values(
            status=status,
            pages_fetched=pages_fetched,
            items_received=items_received,
            total_reported=total_reported,
            error=error,
        )
        .returning(CollectionQuery)
    )
    return (await session.execute(statement)).scalar_one()


async def upsert_raw_postings(
    session: AsyncSession,
    source: str,
    items: Sequence[RawItem],
    run_id: int,
) -> dict[str, int]:
    # Repeated IDs within a page must also be safe for PostgreSQL's bulk upsert.
    unique = {item.source_posting_id: item for item in items}
    if not unique:
        return {}
    now = datetime.now(UTC)
    statement = insert(RawPosting).values(
        [
            {
                "source": source,
                "source_posting_id": item.source_posting_id,
                "payload": item.payload,
                "run_id": run_id,
                "fetched_at": now,
            }
            for item in unique.values()
        ]
    )
    returning = statement.on_conflict_do_update(
        index_elements=[RawPosting.source, RawPosting.source_posting_id],
        set_={
            "payload": statement.excluded.payload,
            "fetched_at": statement.excluded.fetched_at,
            "run_id": statement.excluded.run_id,
        },
    ).returning(RawPosting.source_posting_id, RawPosting.id)
    rows = (await session.execute(returning)).all()
    return {row.source_posting_id: row.id for row in rows}


async def add_query_hits(
    session: AsyncSession,
    query_id: int,
    raw_posting_ids: Sequence[int],
) -> None:
    if not raw_posting_ids:
        return
    statement = (
        insert(QueryHit)
        .values(
            [
                {"collection_query_id": query_id, "raw_posting_id": raw_id}
                for raw_id in set(raw_posting_ids)
            ]
        )
        .on_conflict_do_nothing()
    )
    await session.execute(statement)


# The lock session must keep its connection until explicit unlock. Work is committed
# through separate sessions so page checkpoints survive later failures.
COLLECTION_LOCK_KEY = 742019031


async def try_execution_lock(session: AsyncSession) -> bool:
    from sqlalchemy import text

    return bool(
        await session.scalar(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": COLLECTION_LOCK_KEY}
        )
    )


async def release_execution_lock(session: AsyncSession) -> None:
    from sqlalchemy import text

    await session.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": COLLECTION_LOCK_KEY})


async def previous_total(
    session: AsyncSession, source: str, keyword: str, region: str
) -> int | None:
    from sqlalchemy import select

    return await session.scalar(
        select(CollectionQuery.total_reported)
        .where(
            CollectionQuery.source == source,
            CollectionQuery.keyword == keyword,
            CollectionQuery.region == region,
        )
        .order_by(CollectionQuery.id.desc())
        .limit(1)
    )


async def record_call(session: AsyncSession, run_id: int) -> None:
    await session.execute(
        update(CollectionRun)
        .where(CollectionRun.id == run_id)
        .values(api_calls_used=CollectionRun.api_calls_used + 1)
    )


async def get_run(session: AsyncSession, run_id: int) -> CollectionRun | None:
    return await session.get(CollectionRun, run_id)


async def get_queries(session: AsyncSession, run_id: int) -> list[CollectionQuery]:
    from sqlalchemy import select

    return list(
        (
            await session.scalars(
                select(CollectionQuery)
                .where(CollectionQuery.run_id == run_id)
                .order_by(CollectionQuery.id)
            )
        ).all()
    )
