"""채용 소스 어댑터 계약.

수집 엔진(C-4)은 이 모듈의 타입만 안다. 소스별 어댑터(C-2 고용24, C-3 사람인)는
`SourceAdapter`를 구현하고, HTTP 응답을 `SourcePage`로 바꾸고, 오류를 아래 예외로 분류한다.
어댑터는 재시도하지 않는다. 재시도와 호출 수 집계는 수집 엔진이 맡는다.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol

from app.domain.raw import RawItem

__all__ = [
    "PermanentSourceError",
    "QuotaExceeded",
    "RawItem",
    "SourceAdapter",
    "SourceError",
    "SourceName",
    "SourcePage",
    "SourceQuery",
    "TransientSourceError",
]

SourceName = Literal["saramin", "work24"]


@dataclass(frozen=True)
class SourceQuery:
    """쿼리 1건: 소스 × 키워드 × 지역."""

    source: SourceName
    keyword: str
    # 행정 시도 코드 2자리(예: "11" 서울, "41" 경기). None이면 지역 조건 없음.
    # 소스별 지역 코드로 바꾸는 일은 어댑터가 한다.
    region: str | None
    # 증분 수집 기준 시각. None이면 기간 조건 없이 전체를 받는다.
    since: datetime | None = None
    # 소스별 추가 파라미터(어댑터가 해석한다).
    extra: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SourcePage:
    """페이지 1장의 응답."""

    # 요청한 페이지 번호. 소스 규칙 그대로 쓴다(사람인 0부터, 고용24 1부터).
    page: int
    # API가 알려준 총건수. 응답에 없으면 None.
    total: int | None
    # 공고 원본(app.domain.raw.RawItem). raw_posting.payload(JSONB)에 그대로 저장된다.
    items: list[RawItem]
    # 응답 본문 원문(디버깅과 픽스처 갱신용).
    raw_text: str


class SourceError(Exception):
    """소스 호출 실패의 공통 부모."""


class QuotaExceeded(SourceError):
    """일일 호출 한도 초과(사람인 code=4 등). 재시도하지 않고 남은 쿼리를 미룬다."""


class TransientSourceError(SourceError):
    """다시 시도하면 될 수 있는 오류(타임아웃, 연결 오류, 5xx)."""


class PermanentSourceError(SourceError):
    """다시 시도해도 안 되는 오류(인증 실패, 잘못된 파라미터, 응답 형식 오류)."""


class SourceAdapter(Protocol):
    source: SourceName
    # 첫 페이지 번호(사람인 0, 고용24 1).
    first_page: int
    # 한 번에 받을 수 있는 최대 건수(사람인 110, 고용24 100).
    max_page_size: int
    # 요청할 수 있는 마지막 페이지 번호. 상한이 확인되지 않았으면 None.
    max_page: int | None

    async def fetch_page(self, query: SourceQuery, page: int, page_size: int) -> SourcePage:
        """페이지 1장을 받는다. 실패는 SourceError 하위 예외로 올린다."""
        ...
