"""사람인 JSON 목록 어댑터. 재시도와 호출 예산은 수집 엔진이 관리한다.

명세: https://oapi.saramin.co.kr/guide/job-search
sort=pa는 게시일 오름차순, published_min은 Unix timestamp를 사용한다.
start × count 상한은 공개 명세에서 확인되지 않아 max_page는 None이다.
"""

from typing import Any

import httpx

from app.adapters.base import (
    PermanentSourceError,
    QuotaExceeded,
    RawItem,
    SourceName,
    SourcePage,
    SourceQuery,
    TransientSourceError,
)
from app.adapters.saramin_codes import to_loc_mcd


class SaraminAdapter:
    source: SourceName = "saramin"
    first_page = 0
    max_page_size = 110
    max_page: int | None = None

    def __init__(
        self,
        client: httpx.AsyncClient,
        access_key: str,
        url: str = "https://oapi.saramin.co.kr/job-search",
    ) -> None:
        self._client = client
        self._access_key = access_key
        self._url = url

    async def fetch_page(self, query: SourceQuery, page: int, page_size: int) -> SourcePage:
        params = {
            "access-key": self._access_key,
            "keywords": query.keyword,
            "sr": "directhire",
            "start": str(page),
            "count": str(page_size),
            "sort": "pa",
        }
        if query.region is not None:
            params["loc_mcd"] = to_loc_mcd(query.region)
        if query.since is not None:
            params["published_min"] = str(int(query.since.timestamp()))
        try:
            response = await self._client.get(
                self._url, params=params, headers={"Accept": "application/json"}
            )
        except httpx.TimeoutException, httpx.NetworkError:
            # httpx 예외에는 인증키를 담은 요청 URL이 들어갈 수 있다.
            raise TransientSourceError("Saramin connection or timeout failure") from None

        if response.status_code >= 500:
            raise TransientSourceError(f"Saramin HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError:
            raise PermanentSourceError("Invalid Saramin JSON response") from None
        if isinstance(payload, dict) and "code" in payload:
            if str(payload["code"]) == "4":
                raise QuotaExceeded("Saramin daily request quota exceeded")
            raise PermanentSourceError("Saramin API error")
        if not response.is_success:
            raise PermanentSourceError(f"Saramin HTTP {response.status_code}")
        total, items = _parse_jobs(payload)
        return SourcePage(page=page, total=total, items=items, raw_text=response.text)


def _parse_jobs(payload: Any) -> tuple[int | None, list[RawItem]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), dict):
        raise PermanentSourceError("Missing Saramin jobs object")
    jobs = payload["jobs"]
    total_value = jobs.get("total")
    total: int | None = None
    if total_value is not None:
        if isinstance(total_value, bool) or not isinstance(total_value, (int, str)):
            raise PermanentSourceError("Invalid Saramin total")
        try:
            total = int(total_value)
        except ValueError:
            raise PermanentSourceError("Invalid Saramin total") from None
        if total < 0:
            raise PermanentSourceError("Invalid Saramin total")
    postings = jobs.get("job")
    if not isinstance(postings, list):
        raise PermanentSourceError("Invalid Saramin job list")
    items = []
    for posting in postings:
        if not isinstance(posting, dict):
            raise PermanentSourceError("Invalid Saramin job object")
        posting_id = posting.get("id")
        if isinstance(posting_id, bool) or not isinstance(posting_id, (str, int)):
            raise PermanentSourceError("Missing Saramin posting ID")
        if str(posting_id) == "":
            raise PermanentSourceError("Missing Saramin posting ID")
        items.append(RawItem(source_posting_id=str(posting_id), payload=posting))
    return total, items
