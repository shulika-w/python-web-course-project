"""
Module of rates' repository CRUD
"""

from pydantic import UUID4
from sqlalchemy import select, and_, desc, func
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.src.database.models import Rate, User
from app.src.schemas.rates import RateModel


async def read_all_rates_to_photo(
    image_id: UUID4 | int,
    offset: int,
    limit: int,
    session: AsyncSession) -> list[Rate] | None:

    stmt = select(Rate).filter(Rate.image_id == image_id)
    stmt = stmt.order_by(desc(Rate.created_at))
    stmt = stmt.offset(offset).limit(limit)
    rates = await session.execute(stmt)

    return rates.scalars()

async def create_rate_to_photo(
    image_id: UUID4 | int,
    body: RateModel,
    user: User,
    session: AsyncSession) -> Rate | None:

    rate_photo = Rate(image_id=image_id,
                      rate=body.rate,
                      user_id=user.id)
    session.add(rate_photo)
    await session.commit()
    await session.refresh(rate_photo)
    return rate_photo