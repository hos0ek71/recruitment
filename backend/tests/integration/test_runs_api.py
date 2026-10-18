import asyncio

import httpx
import pytest

from app.api.deps import get_collection_controller
from app.main import create_app
from app.services.collection import CollectionController
from tests.integration.test_collection_service import FakeAdapter, seed
from tests.integration.test_collection_service import factory as factory  # noqa: F401

pytestmark = pytest.mark.db


async def test_runs_api(factory):
    criteria = await seed(factory)
    release = asyncio.Event()
    adapter = FakeAdapter(block=release)
    controller = CollectionController(factory, {"saramin": adapter})
    app = create_app()
    app.dependency_overrides[get_collection_controller] = lambda: controller
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/runs", json={"criteria_id": criteria.id})
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        await asyncio.wait_for(adapter.entered.wait(), 5)
        try:
            active = await client.get(f"/runs/{run_id}")
            assert active.status_code == 200
            assert active.json()["status"] == "running"
            assert (
                await client.post("/runs", json={"criteria_id": criteria.id})
            ).status_code == 409
        finally:
            release.set()
            await controller.wait()
        response = await client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "succeeded"
        assert body["enabled_sources"] == ["saramin"]
        assert {q["source"] for q in body["queries"]} == {"saramin"}
        assert {
            "source",
            "keyword",
            "region",
            "status",
            "pages_fetched",
            "total_reported",
            "items_received",
            "error",
        } <= body["queries"][0].keys()
        assert (await client.get("/runs/999999")).status_code == 404
        assert (await client.post("/runs", json={"criteria_id": 999999})).status_code == 422


async def test_unsupported_region_returns_422_and_releases_lock(factory):
    invalid = await seed(factory, regions=("42",))
    valid = await seed(factory, regions=("11",))
    controller = CollectionController(factory, {"saramin": FakeAdapter()})
    app = create_app()
    app.dependency_overrides[get_collection_controller] = lambda: controller
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        invalid_response = await client.post("/runs", json={"criteria_id": invalid.id})
        try:
            valid_response = await client.post("/runs", json={"criteria_id": valid.id})
        finally:
            await controller.wait()
    assert invalid_response.status_code == 422
    assert invalid_response.json()["detail"] == "지원하지 않는 지역 코드: 42"
    assert valid_response.status_code == 202


async def test_no_sources_returns_422_without_run_and_releases_lock(factory):
    from sqlalchemy import func, select

    from app.repositories.models import CollectionRun

    criteria = await seed(factory)
    controller = CollectionController(factory, {})
    app = create_app()
    app.dependency_overrides[get_collection_controller] = lambda: controller
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/runs", json={"criteria_id": criteria.id})
        await controller.wait()
        async with factory() as session:
            count = await session.scalar(select(func.count()).select_from(CollectionRun))
        controller.adapters = {"saramin": FakeAdapter()}
        try:
            next_response = await client.post("/runs", json={"criteria_id": criteria.id})
        finally:
            await controller.wait()
    assert response.status_code == 422
    assert response.json()["detail"] == "사용할 수 있는 소스가 없다(키 설정 필요)"
    assert count == 0
    assert next_response.status_code == 202
