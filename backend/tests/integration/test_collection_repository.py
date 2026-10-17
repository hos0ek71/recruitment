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
    assert newer == ids
    assert await session.scalar(select(func.count()).select_from(RawPosting)) == 1
    raw = await session.get(RawPosting, ids["123"], populate_existing=True)
    assert raw.payload == {"title": "after"}
    assert raw.run_id == newer_run.id
    await collection.add_query_hits(session, query.id, list(ids.values()) * 2)
    await collection.add_query_hits(session, query.id, list(ids.values()))
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
