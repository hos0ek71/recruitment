from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import Criteria


async def get_approved_criteria(session: AsyncSession, criteria_id: int | None) -> Criteria | None:
    statement = select(Criteria).where(Criteria.status == "approved")
    if criteria_id is not None:
        statement = statement.where(Criteria.id == criteria_id)
    return await session.scalar(
        statement.order_by(Criteria.version.desc(), Criteria.id.desc()).limit(1)
    )
