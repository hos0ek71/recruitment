import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.raw import RawItem
from app.repositories.models import (
    CollectionQuery,
    CollectionRun,
    QueryHit,
    RawPosting,
    RawPostingVersion,
)


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
    mode: str = "published",
) -> CollectionQuery:
    query = CollectionQuery(
        run_id=run_id,
        source=source,
        keyword=keyword,
        region=region,
        published_since=published_since,
        mode=mode,
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


# Official Saramin response elements (https://oapi.saramin.co.kr/guide/job-search):
# fields=count adds read-cnt (views), apply-cnt (applicants); these are activity,
# not edits to recruitment content. Fixtures: saramin/list_counts.json.
# No volatile Work24 fields have been verified, so nothing is ignored there.
HASH_IGNORED_FIELDS: dict[str, frozenset[str]] = {
    "saramin": frozenset({"read-cnt", "apply-cnt"}),
    "work24": frozenset(),
}


def content_hash(source: str, payload: dict[str, Any]) -> str:
    content = {k: v for k, v in payload.items() if k not in HASH_IGNORED_FIELDS.get(source, ())}
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def source_modified_at(source: str, payload: dict[str, Any]) -> datetime | None:
    value = payload.get("modification-timestamp") if source == "saramin" else None
    if value is None or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(int(value), UTC)
    except ValueError, TypeError, OverflowError, OSError:
        return None


def payload_changes(before: dict[str, Any], after: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    """Deterministic JSON Pointer paths; additions/removals use None for absent values.

    Lists are compared as complete values; dictionaries are compared recursively.
    The function reports raw differences, including volatile fields, without mutation.
    """
    changes: list[tuple[str, Any, Any]] = []

    def compare(old: Any, new: Any, path: str) -> None:
        if isinstance(old, dict) and isinstance(new, dict):
            for key in sorted(old.keys() | new.keys()):
                child = path + "/" + key.replace("~", "~0").replace("/", "~1")
                if key not in old or key not in new:
                    changes.append((child, old.get(key), new.get(key)))
                else:
                    compare(old[key], new[key], child)
        elif type(old) is not type(new) or old != new:
            changes.append((path, old, new))

    compare(before, after, "")
    return changes


@dataclass(frozen=True)
class UpsertResult:
    ids: dict[str, int]
    changed_ids: frozenset[int]


async def upsert_raw_postings(
    session: AsyncSession,
    source: str,
    items: Sequence[RawItem],
    run_id: int,
) -> UpsertResult:
    # Last occurrence wins within a page, as in the previous bulk upsert.
    # Stable lock order avoids deadlocks when pages share several existing IDs.
    unique = {item.source_posting_id: item for item in items}
    ids: dict[str, int] = {}
    changed: set[int] = set()
    now = datetime.now(UTC)
    for posting_id, item in sorted(unique.items()):
        digest = content_hash(source, item.payload)
        inserted = await session.scalar(
            insert(RawPosting)
            .values(
                source=source,
                source_posting_id=posting_id,
                payload=item.payload,
                content_hash=digest,
                run_id=run_id,
                fetched_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=[RawPosting.source, RawPosting.source_posting_id]
            )
            .returning(RawPosting.id)
        )
        # Serialize version allocation for existing rows; the insert locks new rows.
        raw = (
            await session.scalars(
                select(RawPosting)
                .where(RawPosting.source == source, RawPosting.source_posting_id == posting_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        ).one()
        ids[posting_id] = raw.id
        if inserted is not None or raw.content_hash != digest:
            version = (
                await session.scalar(
                    select(func.max(RawPostingVersion.version)).where(
                        RawPostingVersion.raw_posting_id == raw.id
                    )
                )
            ) or 0
            session.add(
                RawPostingVersion(
                    raw_posting_id=raw.id,
                    version=version + 1,
                    payload=item.payload,
                    content_hash=digest,
                    source_modified_at=source_modified_at(source, item.payload),
                    fetched_at=now,
                    run_id=run_id,
                )
            )
            raw.payload = item.payload
            raw.content_hash = digest
            changed.add(raw.id)
        raw.fetched_at = now
        raw.run_id = run_id
        await session.flush()
    return UpsertResult(ids, frozenset(changed))


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
    session: AsyncSession, source: str, keyword: str, region: str, mode: str = "published"
) -> int | None:
    from sqlalchemy import select

    return await session.scalar(
        select(CollectionQuery.total_reported)
        .where(
            CollectionQuery.source == source,
            CollectionQuery.keyword == keyword,
            CollectionQuery.region == region,
            CollectionQuery.mode == mode,
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
