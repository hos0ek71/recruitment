from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import QueryWatermark


async def get_watermark(
    session: AsyncSession,
    source: str,
    keyword: str,
    region: str,
    mode: str = "published",
) -> datetime | None:
    return await session.scalar(
        select(QueryWatermark.last_completed_at).where(
            QueryWatermark.source == source,
            QueryWatermark.keyword == keyword,
            QueryWatermark.region == region,
            QueryWatermark.mode == mode,
        )
    )


async def set_watermark(
    session: AsyncSession,
    source: str,
    keyword: str,
    region: str,
    last_completed_at: datetime,
    mode: str = "published",
) -> None:
    statement = insert(QueryWatermark).values(
        source=source,
        keyword=keyword,
        region=region,
        last_completed_at=last_completed_at,
        mode=mode,
    )
    await session.execute(
        statement.on_conflict_do_update(
            index_elements=[
                QueryWatermark.source,
                QueryWatermark.keyword,
                QueryWatermark.region,
                QueryWatermark.mode,
            ],
            set_={"last_completed_at": statement.excluded.last_completed_at},
        )
    )
