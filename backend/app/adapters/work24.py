"""고용24 공식 목록·상세 XML 어댑터. 재시도는 수집 엔진이 담당한다."""

from calendar import monthrange
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any
from xml.etree.ElementTree import Element, ParseError
from zoneinfo import ZoneInfo

import httpx
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from app.adapters.base import (
    PermanentSourceError,
    RawItem,
    SourceName,
    SourcePage,
    SourceQuery,
    TransientSourceError,
)
from app.adapters.work24_codes import region_code

LIST_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"
DETAIL_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do"
KST = ZoneInfo("Asia/Seoul")


def _today() -> date:
    return datetime.now(KST).date()


def _reg_date(since: datetime, today: date) -> str | None:
    # 공식 명세는 상대 기간만 명시한다. 프로젝트 합의: KST 날짜 경계,
    # 한달은 전월 동일 일자(말일 보정), naive since도 KST로 해석한다.
    since_date = (
        since.replace(tzinfo=KST).date() if since.tzinfo is None else since.astimezone(KST).date()
    )
    year, month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    previous_month = date(year, month, min(today.day, monthrange(year, month)[1]))
    windows = [
        ("D-0", today),
        ("D-3", today - timedelta(days=3)),
        ("W-1", today - timedelta(days=7)),
        ("W-2", today - timedelta(days=14)),
        ("M-1", previous_month),
    ]
    return next((code for code, start in windows if since_date >= start), None)


def _element_dict(element: Element) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for child in element:
        value: Any = _element_dict(child) if len(child) else (child.text or "")
        if child.tag not in result:
            result[child.tag] = value
        elif isinstance(result[child.tag], list):
            result[child.tag].append(value)
        else:
            result[child.tag] = [result[child.tag], value]
    return result


def _required_text(root: Element, name: str) -> str:
    text = root.findtext(name)
    if text is None or not text.strip():
        raise PermanentSourceError(f"Work24 response is missing {name}")
    return text.strip()


class Work24Adapter:
    supports_updated = False
    source: SourceName = "work24"
    first_page = 1
    max_page_size = 100
    max_page = 1000

    def __init__(
        self,
        client: httpx.AsyncClient,
        auth_key: str,
        list_url: str = LIST_URL,
        detail_url: str = DETAIL_URL,
        *,
        today: Callable[[], date] = _today,
    ) -> None:
        self._client = client
        self._auth_key = auth_key
        self._list_url = list_url
        self._detail_url = detail_url
        self._today = today

    async def _request(self, url: str, params: dict[str, str]) -> tuple[Element, str]:
        params = {"authKey": self._auth_key, "returnType": "XML", **params}
        try:
            response = await self._client.get(url, params=params)
        except httpx.TimeoutException, httpx.NetworkError:
            # 원래 httpx 예외에는 키를 포함한 요청 URL이 담길 수 있다.
            raise TransientSourceError("Work24 transport failure") from None
        if response.status_code >= 500:
            raise TransientSourceError(f"Work24 HTTP {response.status_code}")
        if not 200 <= response.status_code < 300:
            raise PermanentSourceError(f"Work24 HTTP {response.status_code}")
        try:
            root = ElementTree.fromstring(response.content, forbid_dtd=True)
        except ParseError, DefusedXmlException:
            raise PermanentSourceError("Work24 invalid XML") from None
        # W3/W4(2026-10-17)에는 인증·한도 초과 XML 응답 형식이 없다.
        # 확인되지 않은 코드/메시지로 QuotaExceeded를 추정하지 않는다.
        # 오류 본문은 정상 목록/상세 구조 검증에서 PermanentSourceError가 된다.
        return root, response.text

    async def fetch_page(self, query: SourceQuery, page: int, page_size: int) -> SourcePage:
        params = {
            "callTp": "L",
            "startPage": str(page),
            "display": str(page_size),
            "keyword": query.keyword,
        }
        if query.region is not None:
            params["region"] = region_code(query.region)
        if "regDate" in query.extra:
            params["regDate"] = query.extra["regDate"]
        elif query.since is not None:
            reg_date = _reg_date(query.since, self._today())
            if reg_date is not None:
                params["regDate"] = reg_date
        root, raw_text = await self._request(self._list_url, params)
        if root.tag != "wantedRoot":
            raise PermanentSourceError("Work24 invalid list root")
        try:
            total = int(_required_text(root, "total"))
        except ValueError:
            raise PermanentSourceError("Work24 invalid total") from None
        if total < 0:
            raise PermanentSourceError("Work24 negative total")
        items = [
            RawItem(_required_text(item, "wantedAuthNo"), _element_dict(item))
            for item in root.findall("wanted")
        ]
        return SourcePage(page=page, total=total, items=items, raw_text=raw_text)

    async def fetch_detail(self, wanted_auth_no: str) -> dict[str, Any]:
        root, _ = await self._request(
            self._detail_url,
            {"callTp": "D", "wantedAuthNo": wanted_auth_no, "infoSvc": "VALIDATION"},
        )
        if root.tag != "wantedDtl":
            raise PermanentSourceError("Work24 invalid detail root")
        _required_text(root, "wantedAuthNo")
        if root.find("corpInfo") is None or root.find("wantedInfo") is None:
            raise PermanentSourceError("Work24 missing detail sections")
        return _element_dict(root)
