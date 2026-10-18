from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import ApiUsage


async def get_calls(session: AsyncSession, usage_date: date, source: str) -> int:
    calls = await session.scalar(
        select(ApiUsage.calls).where(
            ApiUsage.usage_date == usage_date,
            ApiUsage.source == source,
        )
    )
    return calls if calls is not None else 0


async def increment_calls(
    session: AsyncSession,
    usage_date: date,
    source: str,
    n: int,
) -> int:
    statement = insert(ApiUsage).values(usage_date=usage_date, source=source, calls=n)
    returning = statement.on_conflict_do_update(
        index_elements=[ApiUsage.usage_date, ApiUsage.source],
        set_={"calls": ApiUsage.calls + n},
    ).returning(ApiUsage.calls)
    return (await session.execute(returning)).scalar_one()
