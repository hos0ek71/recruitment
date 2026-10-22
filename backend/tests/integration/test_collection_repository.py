from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.domain.raw import RawItem
from app.repositories import api_usage, collection, criteria, watermark
from app.repositories.models import Criteria, Profile, QueryHit, RawPosting

pytestmark = pytest.mark.db


@pytest.fixture
async def approved(session):
    profile = Profile(raw_text="synthetic profile")
    session.add(profile)
    await session.flush()
    criterion = Criteria(profile_id=profile.id, version=1, status="approved")
    session.add(criterion)
    await session.flush()
    return criterion


async def test_raw_upsert_and_duplicate_query_hits(session, approved):
    run = await collection.create_run(session, approved.id, "manual")
    query = await collection.create_query(session, run.id, "saramin", "서버", "11")
    ids = await collection.upsert_raw_postings(
        session, "saramin", [RawItem("123", {"title": "before"})], run.id
    )
    newer_run = await collection.create_run(session, approved.id, "manual")
    newer = await collection.upsert_raw_postings(
        session, "saramin", [RawItem("123", {"title": "after"})], newer_run.id
    )
    assert newer.ids == ids.ids
    assert await session.scalar(select(func.count()).select_from(RawPosting)) == 1
    raw = await session.get(RawPosting, ids.ids["123"], populate_existing=True)
    assert raw.payload == {"title": "after"}
    assert raw.run_id == newer_run.id
    await collection.add_query_hits(session, query.id, list(ids.ids.values()) * 2)
    await collection.add_query_hits(session, query.id, list(ids.ids.values()))
    assert await session.scalar(select(func.count()).select_from(QueryHit)) == 1
    await collection.update_query(
        session,
        query.id,
        status="completed",
        pages_fetched=1,
        items_received=1,
        total_reported=1,
        error=None,
    )
    await collection.finish_run(session, run.id, "succeeded", 2)
    await session.refresh(query)
    await session.refresh(run)
    assert (query.status, query.pages_fetched, query.items_received) == ("completed", 1, 1)
    assert (run.status, run.api_calls_used) == ("succeeded", 2)
    assert run.finished_at is not None


async def test_usage_and_watermark(session):
    today = date(2026, 10, 17)
    assert await api_usage.get_calls(session, today, "saramin") == 0
    assert await api_usage.increment_calls(session, today, "saramin", 2) == 2
    assert await api_usage.increment_calls(session, today, "saramin", 3) == 5
    assert await api_usage.get_calls(session, today, "saramin") == 5
    assert await api_usage.get_calls(session, today, "work24") == 0
    assert await watermark.get_watermark(session, "saramin", "서버", "11") is None
    moment = datetime(2026, 10, 17, tzinfo=UTC)
    await watermark.set_watermark(session, "saramin", "서버", "11", moment)
    assert await watermark.get_watermark(session, "saramin", "서버", "11") == moment
    later = datetime(2026, 10, 18, tzinfo=UTC)
    await watermark.set_watermark(session, "saramin", "서버", "11", later)
    assert await watermark.get_watermark(session, "saramin", "서버", "11") == later


async def test_only_approved_criteria(session, approved):
    draft = Criteria(profile_id=approved.profile_id, version=2, status="draft")
    session.add(draft)
    await session.flush()
    assert await criteria.get_approved_criteria(session, approved.id) is approved
    assert await criteria.get_approved_criteria(session, draft.id) is None
    assert await criteria.get_approved_criteria(session, None) is approved


async def test_invalid_status_rejected(session, approved):
    with pytest.raises(IntegrityError):
        await session.execute(
            text("UPDATE criteria SET status = :status WHERE id = :id"),
            {"status": "x", "id": approved.id},
        )


async def test_version_history_and_changed_ids(session, approved):
    from app.repositories.models import RawPostingVersion

    run = await collection.create_run(session, approved.id, "manual")
    original = {
        "id": "v",
        "expiration-timestamp": "1",
        "modification-timestamp": "1700000000",
        "read-cnt": "1",
    }
    first = await collection.upsert_raw_postings(
        session, "saramin", [RawItem("v", original)] * 2, run.id
    )
    raw_id = first.ids["v"]
    assert first.changed_ids == {raw_id}
    same = await collection.upsert_raw_postings(
        session, "saramin", [RawItem("v", original)], run.id
    )
    assert same.changed_ids == set()
    counts = {**original, "read-cnt": "99", "apply-cnt": "5"}
    seen_run = await collection.create_run(session, approved.id, "manual")
    old_fetch = datetime(2020, 1, 1, tzinfo=UTC)
    await session.execute(
        text("UPDATE raw_posting SET fetched_at=:old WHERE id=:id"),
        {"old": old_fetch, "id": raw_id},
    )
    same = await collection.upsert_raw_postings(
        session, "saramin", [RawItem("v", counts)], seen_run.id
    )
    assert same.changed_ids == set()
    raw = await session.get(RawPosting, raw_id, populate_existing=True)
    assert raw.run_id == seen_run.id
    assert raw.fetched_at > old_fetch
    assert raw.payload == original
    assert await session.scalar(select(func.count()).select_from(RawPostingVersion)) == 1
    changed = {**counts, "expiration-timestamp": "2"}
    newer = await collection.create_run(session, approved.id, "manual")
    updated = await collection.upsert_raw_postings(
        session, "saramin", [RawItem("v", changed)] * 2, newer.id
    )
    assert updated.changed_ids == {raw_id}
    versions = list(
        (
            await session.scalars(
                select(RawPostingVersion)
                .where(RawPostingVersion.raw_posting_id == raw_id)
                .order_by(RawPostingVersion.version)
            )
        ).all()
    )
    assert [v.version for v in versions] == [1, 2]
    assert [v.payload for v in versions] == [original, changed]
    assert versions[0].source_modified_at == datetime.fromtimestamp(1700000000, UTC)
    assert versions[1].run_id == newer.id
    raw = await session.get(RawPosting, raw_id, populate_existing=True)
    assert raw.payload == changed
    assert raw.content_hash == versions[1].content_hash


async def test_mode_watermarks_are_independent(session):
    published = datetime(2026, 10, 17, tzinfo=UTC)
    updated = datetime(2026, 10, 18, tzinfo=UTC)
    await watermark.set_watermark(session, "saramin", "python", "*", published)
    await watermark.set_watermark(session, "saramin", "python", "*", updated, mode="updated")
    assert await watermark.get_watermark(session, "saramin", "python", "*") == published
    assert (
        await watermark.get_watermark(session, "saramin", "python", "*", mode="updated") == updated
    )


async def test_previous_totals_are_mode_specific(session, approved):
    run = await collection.create_run(session, approved.id, "manual")
    for mode, total in [("published", 10), ("updated", 2)]:
        query = await collection.create_query(session, run.id, "saramin", "python", "*", mode=mode)
        await collection.update_query(
            session,
            query.id,
            status="completed",
            pages_fetched=1,
            items_received=total,
            total_reported=total,
        )
    assert await collection.previous_total(session, "saramin", "python", "*") == 10
    assert await collection.previous_total(session, "saramin", "python", "*", mode="updated") == 2
    empty = await collection.upsert_raw_postings(session, "saramin", [], run.id)
    assert empty.ids == {} and empty.changed_ids == frozenset()
