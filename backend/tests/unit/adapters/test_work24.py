from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx

from app.adapters.base import PermanentSourceError, SourceAdapter, SourceQuery, TransientSourceError
from app.adapters.work24 import Work24Adapter
from app.adapters.work24_codes import region_code

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "work24"
LIST = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"
DETAIL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do"
QUERY = SourceQuery(source="work24", keyword="개발자", region="11")


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


async def test_list_and_request() -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(LIST).respond(text=fixture("list_ok.xml"))
        async with httpx.AsyncClient() as client:
            adapter: SourceAdapter = Work24Adapter(client, "test-only")
            result = await adapter.fetch_page(QUERY, 2, 3)
        assert (adapter.source, adapter.first_page, adapter.max_page_size, adapter.max_page) == (
            "work24",
            1,
            100,
            1000,
        )
        assert result.page == 2
        assert result.total == 5
        assert len(result.items) == 3
        assert result.items[0].source_posting_id == "K000002610170001"
        assert result.items[0].payload["company"] == "가상채용기업1"
        assert result.raw_text == fixture("list_ok.xml")
        assert dict(route.calls.last.request.url.params) == {
            "authKey": "test-only",
            "callTp": "L",
            "returnType": "XML",
            "startPage": "2",
            "display": "3",
            "keyword": "개발자",
            "region": "11000",
        }


@pytest.mark.parametrize(
    "name,total,count",
    [
        ("list_empty.xml", 0, 0),
        ("list_missing_fields.xml", 1, 1),
    ],
)
async def test_optional_list_fields(name: str, total: int, count: int) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(LIST).respond(text=fixture(name))
        async with httpx.AsyncClient() as client:
            result = await Work24Adapter(client, "test-only").fetch_page(QUERY, 1, 3)
        assert result.total == total
        assert len(result.items) == count
        if count:
            assert "career" not in result.items[0].payload


@pytest.mark.parametrize("name", ["detail_ok.xml", "detail_missing_fields.xml"])
async def test_detail(name: str) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(DETAIL).respond(text=fixture(name))
        async with httpx.AsyncClient() as client:
            result = await Work24Adapter(client, "test-only").fetch_detail("K000002610170001")
        assert result["corpInfo"]["corpNm"] == "가상채용기업1"
        if name == "detail_ok.xml":
            assert result["corpInfo"]["totPsncnt"] == "120"
            assert "Python API" in result["wantedInfo"]["jobCont"]
            assert result["empchargeInfo"]["empChargerDpt"] == "채용팀"
        else:
            assert "totPsncnt" not in result["corpInfo"]
            assert "jobCont" not in result["wantedInfo"]
        assert dict(route.calls.last.request.url.params) == {
            "authKey": "test-only",
            "callTp": "D",
            "returnType": "XML",
            "wantedAuthNo": "K000002610170001",
            "infoSvc": "VALIDATION",
        }


async def test_nested_repeated_elements() -> None:
    xml = (
        "<wantedRoot><total>1</total><wanted><wantedAuthNo>x</wantedAuthNo>"
        "<nested><value>a</value><value>b</value></nested></wanted></wantedRoot>"
    )
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(LIST).respond(text=xml)
        async with httpx.AsyncClient() as client:
            result = await Work24Adapter(client, "test-only").fetch_page(QUERY, 1, 3)
        assert result.items[0].payload["nested"] == {"value": ["a", "b"]}


@pytest.mark.parametrize("detail", [False, True])
@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 503])
async def test_http_errors(detail: bool, status: int) -> None:
    error = TransientSourceError if status >= 500 else PermanentSourceError
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(DETAIL if detail else LIST).respond(status)
        async with httpx.AsyncClient() as client:
            adapter = Work24Adapter(client, "test-only")
            with pytest.raises(error):
                if detail:
                    await adapter.fetch_detail("x")
                else:
                    await adapter.fetch_page(QUERY, 1, 3)
        assert route.call_count == 1


@pytest.mark.parametrize("error", [httpx.ReadTimeout, httpx.ConnectError])
@pytest.mark.parametrize("detail", [False, True])
async def test_transport_errors(error: type[httpx.TransportError], detail: bool) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(DETAIL if detail else LIST).mock(side_effect=error("test failure"))
        async with httpx.AsyncClient() as client:
            adapter = Work24Adapter(client, "test-only")
            with pytest.raises(TransientSourceError):
                if detail:
                    await adapter.fetch_detail("x")
                else:
                    await adapter.fetch_page(QUERY, 1, 3)
        assert route.call_count == 1


@pytest.mark.parametrize(
    "xml",
    [
        "<broken",
        "<wantedRoot/>",
        "<wantedRoot><total>oops</total></wantedRoot>",
        "<wantedRoot><total>-1</total></wantedRoot>",
        "<wantedRoot><total>1</total><wanted/></wantedRoot>",
        fixture("error.xml"),
        '<!DOCTYPE x [<!ENTITY x "expanded">]><wantedRoot><total>&x;</total></wantedRoot>',
    ],
)
async def test_invalid_list(xml: str) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(LIST).respond(text=xml)
        async with httpx.AsyncClient() as client:
            with pytest.raises(PermanentSourceError):
                await Work24Adapter(client, "test-only").fetch_page(QUERY, 1, 3)


@pytest.mark.parametrize("xml", ["<broken", "<wantedDtl/>", fixture("error.xml")])
async def test_invalid_detail(xml: str) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        mock.get(DETAIL).respond(text=xml)
        async with httpx.AsyncClient() as client:
            with pytest.raises(PermanentSourceError):
                await Work24Adapter(client, "test-only").fetch_detail("x")


async def test_custom_urls_and_omitted_region() -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get("https://example.com/list").respond(text=fixture("list_empty.xml"))
        mock.get("https://example.com/detail").respond(text=fixture("detail_ok.xml"))
        async with httpx.AsyncClient() as client:
            adapter = Work24Adapter(
                client, "test-only", "https://example.com/list", "https://example.com/detail"
            )
            await adapter.fetch_page(SourceQuery("work24", "Python", None), 1, 100)
            await adapter.fetch_detail("K000002610170001")
        assert "region" not in route.calls.last.request.url.params
        assert "regDate" not in route.calls.last.request.url.params


def test_unknown_region() -> None:
    with pytest.raises(ValueError):
        region_code("99")


@pytest.mark.parametrize(
    "since,expected",
    [
        (datetime(2026, 10, 17, 0), "D-0"),
        (datetime(2026, 10, 16), "D-3"),
        (datetime(2026, 10, 14), "D-3"),
        (datetime(2026, 10, 13), "W-1"),
        (datetime(2026, 10, 10), "W-1"),
        (datetime(2026, 10, 9), "W-2"),
        (datetime(2026, 10, 3), "W-2"),
        (datetime(2026, 10, 2), "M-1"),
        (datetime(2026, 9, 17), "M-1"),
        (datetime(2026, 9, 16, 23, 59), None),
        (datetime(2026, 10, 16, 15, tzinfo=ZoneInfo("UTC")), "D-0"),
        (None, None),
    ],
)
async def test_regdate(since: datetime | None, expected: str | None) -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(LIST).respond(text=fixture("list_empty.xml"))
        async with httpx.AsyncClient() as client:
            adapter = Work24Adapter(client, "test-only", today=lambda: date(2026, 10, 17))
            await adapter.fetch_page(SourceQuery("work24", "Python", None, since), 1, 100)
        assert route.calls.last.request.url.params.get("regDate") == expected


async def test_regdate_override_and_month_end() -> None:
    with respx.mock(assert_all_mocked=True) as mock:
        route = mock.get(LIST).respond(text=fixture("list_empty.xml"))
        async with httpx.AsyncClient() as client:
            adapter = Work24Adapter(client, "test-only", today=lambda: date(2026, 3, 31))
            await adapter.fetch_page(SourceQuery("work24", "", None, datetime(2026, 2, 28)), 1, 3)
            assert route.calls.last.request.url.params["regDate"] == "M-1"
            await adapter.fetch_page(SourceQuery("work24", "", None, datetime(2026, 2, 27)), 1, 3)
            assert "regDate" not in route.calls.last.request.url.params
            await adapter.fetch_page(
                SourceQuery("work24", "", None, datetime(2020, 1, 1), {"regDate": "W-1"}), 1, 3
            )
            assert route.calls.last.request.url.params["regDate"] == "W-1"


@pytest.mark.parametrize(
    "administrative,work24",
    [
        ("11", "11000"),
        ("26", "26000"),
        ("27", "27000"),
        ("28", "28000"),
        ("29", "12000"),
        ("30", "30000"),
        ("31", "31000"),
        ("36", "36110"),
        ("41", "41000"),
        ("43", "43000"),
        ("44", "44000"),
        ("46", "12000"),
        ("47", "47000"),
        ("48", "48000"),
        ("50", "50000"),
        ("51", "51000"),
        ("52", "52000"),
    ],
)
def test_all_region_codes(administrative: str, work24: str) -> None:
    assert region_code(administrative) == work24
