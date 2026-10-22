import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from app.adapters.base import (
    PermanentSourceError,
    QuotaExceeded,
    SourceAdapter,
    SourceQuery,
    TransientSourceError,
)
from app.adapters.saramin import SaraminAdapter
from app.adapters.saramin_codes import to_loc_mcd

FIXTURES = Path(__file__).parents[2] / "fixtures" / "saramin"
URL = "https://oapi.saramin.co.kr/job-search"
QUERY = SourceQuery(source="saramin", keyword="파이썬 개발", region=None)


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_contract() -> None:
    adapter: SourceAdapter = SaraminAdapter(httpx.AsyncClient(), "dummy-key")
    assert (adapter.source, adapter.first_page, adapter.max_page_size, adapter.max_page) == (
        "saramin",
        0,
        110,
        None,
    )


@pytest.mark.parametrize(
    ("filename", "page", "total", "count"),
    [
        ("list_ok.json", 0, 5, 3),
        ("list_counts.json", 0, 1, 1),
        ("list_page2.json", 1, 5, 2),
        ("list_empty.json", 0, 0, 0),
        ("list_missing_fields.json", 0, 1, 1),
    ],
)
async def test_preserves_raw_items(filename: str, page: int, total: int, count: int) -> None:
    raw = fixture_text(filename)
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(URL).respond(text=raw)
        async with httpx.AsyncClient() as client:
            result = await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, page, 3)
    assert (result.page, result.total, result.raw_text) == (page, total, raw)
    assert len(result.items) == count
    jobs = json.loads(raw)["jobs"]["job"]
    assert [item.payload for item in result.items] == jobs
    assert [item.source_posting_id for item in result.items] == [str(job["id"]) for job in jobs]


async def test_last_page_completes_reported_total() -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(URL)
        route.side_effect = [
            httpx.Response(200, text=fixture_text("list_ok.json")),
            httpx.Response(200, text=fixture_text("list_page2.json")),
        ]
        async with httpx.AsyncClient() as client:
            adapter = SaraminAdapter(client, "dummy-key")
            first = await adapter.fetch_page(QUERY, 0, 3)
            last = await adapter.fetch_page(QUERY, 1, 3)
    assert len(first.items) + len(last.items) == first.total == last.total == 5
    assert len({item.source_posting_id for item in first.items + last.items}) == 5


async def test_request_parameters() -> None:
    since = datetime(2026, 10, 17, 1, 2, 3, tzinfo=UTC)
    query = SourceQuery(source="saramin", keyword="파이썬 개발", region="41", since=since)
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get("https://example.test/jobs").respond(text=fixture_text("list_empty.json"))
        async with httpx.AsyncClient() as client:
            await SaraminAdapter(client, "dummy-key", url="https://example.test/jobs").fetch_page(
                query, 2, 110
            )
        request = route.calls.last.request
        assert dict(request.url.params) == {
            "access-key": "dummy-key",
            "keywords": "파이썬 개발",
            "loc_mcd": "102000",
            "sr": "directhire",
            "start": "2",
            "count": "110",
            "published_min": str(int(since.timestamp())),
            "sort": "pa",
        }
        assert request.headers["Accept"] == "application/json"


async def test_omits_optional_parameters() -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(URL).respond(text=fixture_text("list_empty.json"))
        async with httpx.AsyncClient() as client:
            await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)
        assert "loc_mcd" not in route.calls.last.request.url.params
        assert "published_min" not in route.calls.last.request.url.params


@pytest.mark.parametrize(
    ("filename", "error"),
    [
        ("error_quota.json", QuotaExceeded),
        ("error_auth.json", PermanentSourceError),
        ("error_missing_key.json", PermanentSourceError),
    ],
)
async def test_error_fixtures(filename: str, error: type[Exception]) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(URL).respond(text=fixture_text(filename))
        async with httpx.AsyncClient() as client:
            with pytest.raises(error):
                await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)
        assert route.call_count == 1


@pytest.mark.parametrize("code", [3, 99, "4", 777])
async def test_other_api_error_codes(code: int | str) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(URL).respond(json={"code": code, "message": "source error"})
        async with httpx.AsyncClient() as client:
            with pytest.raises(QuotaExceeded if str(code) == "4" else PermanentSourceError):
                await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 502, 503])
async def test_http_errors(status: int) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(URL).respond(status, text="error")
        async with httpx.AsyncClient() as client:
            error = TransientSourceError if status >= 500 else PermanentSourceError
            with pytest.raises(error):
                await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)
        assert route.call_count == 1


@pytest.mark.parametrize("error", [httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError])
async def test_transport_errors(error: type[httpx.RequestError]) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(URL).mock(side_effect=error("network failed"))
        async with httpx.AsyncClient() as client:
            with pytest.raises(TransientSourceError):
                await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)
        assert route.call_count == 1


@pytest.mark.parametrize(
    "body",
    ["invalid json", "[]", "{}", '{"jobs": null}', '{"jobs": {"job": {}}}'],
)
async def test_invalid_responses(body: str) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(URL).respond(text=body)
        async with httpx.AsyncClient() as client:
            with pytest.raises(PermanentSourceError):
                await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)


@pytest.mark.parametrize("jobs", [{"job": [{}]}, {"job": [None]}, {"total": "bad", "job": []}])
async def test_malformed_jobs(jobs: dict[str, Any]) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(URL).respond(json={"jobs": jobs})
        async with httpx.AsyncClient() as client:
            with pytest.raises(PermanentSourceError):
                await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)


async def test_missing_total_is_unknown_and_numeric_id_is_string() -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(URL).respond(json={"jobs": {"job": [{"id": 123}]}})
        async with httpx.AsyncClient() as client:
            result = await SaraminAdapter(client, "dummy-key").fetch_page(QUERY, 0, 10)
    assert result.total is None
    assert result.items[0].source_posting_id == "123"
    assert result.items[0].payload == {"id": 123}


@pytest.mark.parametrize(
    ("region", "expected"),
    [
        ("11", "101000"),
        ("26", "106000"),
        ("27", "104000"),
        ("28", "108000"),
        ("29", "103000"),
        ("30", "105000"),
        ("31", "107000"),
        ("36", "118000"),
        ("41", "102000"),
        ("43", "114000"),
        ("44", "115000"),
        ("46", "112000"),
        ("47", "111000"),
        ("48", "110000"),
        ("50", "116000"),
        ("51", "109000"),
        ("52", "113000"),
    ],
)
def test_all_region_codes(region: str, expected: str) -> None:
    assert to_loc_mcd(region) == expected


@pytest.mark.parametrize("region", ["00", "42", "45", "101000", "서울", ""])
def test_unknown_region(region: str) -> None:
    with pytest.raises(ValueError):
        to_loc_mcd(region)


async def test_updated_parameters():
    from app.adapters.work24 import Work24Adapter

    since = datetime(2026, 10, 17, tzinfo=UTC)
    query = SourceQuery(
        source="saramin", keyword="python", region=None, since=since, mode="updated"
    )
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(URL).respond(text=fixture_text("list_empty.json"))
        async with httpx.AsyncClient() as client:
            adapter = SaraminAdapter(client, "dummy-key")
            assert adapter.supports_updated
            assert not Work24Adapter.supports_updated
            await adapter.fetch_page(query, 0, 110)
        params = route.calls.last.request.url.params
        assert params["updated_min"] == str(int(since.timestamp()))
        assert "published_min" not in params
        assert params["sort"] == "ua"
