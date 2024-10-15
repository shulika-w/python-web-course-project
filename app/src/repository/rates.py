"""
Module of rates' repository CRUD
"""

from fastapi import HTTPException, status
from pydantic import UUID4
from sqlalchemy import select, and_, desc, func
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.src.database.models import Rate, User, Image
from app.src.schemas.rates import RateModel, RateImageResponse


async def read_all_rates_to_image(
        image_id: UUID4 | int, offset: int, limit: int, session: AsyncSession
) -> list[Rate] | None:
    """
    Returns a list of Rate objects that are associated with the image_id parameter.

    :param image_id: UUID4 | int: Specify the image id
    :param offset: int: Set the offset of the first row to be returned
    :param limit: int: Limit the number of rates returned
    :param session: AsyncSession: Pass the session object to the function
    :return: A list of rate objects
    """
    stmt = select(Rate).filter(Rate.image_id == image_id)
    stmt = stmt.order_by(desc(Rate.created_at))
    stmt = stmt.offset(offset).limit(limit)
    rates = await session.execute(stmt)
    return rates.scalars()


async def read_all_my_rates(
        user: User, offset: int, limit: int, session: AsyncSession
) -> ScalarResult:
    """
    Returns a list of all the rates that belong to a user.

    :param user: User: Identify the user who is requesting their rates
    :param offset: int: Specify the number of rows to skip
    :param limit: int: Limit the number of results returned
    :param session: AsyncSession: Pass the database session to the function
    :return: A list of rate objects
    """
    stmt = select(Rate).filter(Rate.user_id == user.id)
    stmt = stmt.order_by(desc(Rate.created_at))
    stmt = stmt.offset(offset).limit(limit)
    rates = await session.execute(stmt)
    return rates.scalars()


async def read_all_user_rates(
        user_id: UUID4 | int,
        offset: int,
        limit: int,
        session: AsyncSession,
) -> ScalarResult:
    """
    Returns a list of all the rates that a user has made.

    :param user_id: UUID4 | int: Filter the rates by user_id
    :param offset: int: Skip the first offset rows in the result set
    :param limit: int: Limit the number of results returned
    :param session: AsyncSession: Pass the database session to the function
    :return: A list of rate objects
    """
    stmt = select(Rate).filter(Rate.user_id == user_id)
    stmt = stmt.order_by(desc(Rate.created_at))
    stmt = stmt.offset(offset).limit(limit)
    rates = await session.execute(stmt)
    return rates.scalars()


async def read_avg_rate_to_image(
        image_id: UUID4 | int,
        session: AsyncSession,
) -> RateImageResponse | None:
    """
    Returns the average rate to an image.

    :param image_id: UUID4 | int: Identify the image that is being rated
    :param session: AsyncSession: Create a connection to the database
    :param : Get the average rate of an image
    :return: A rateimageresponse object with the image and avg_rate fields
    :doc-author: Trelent
    """
    stmt = select(func.avg(Rate.rate)).where(Rate.image_id == image_id)
    avg_rate_result = await session.execute(stmt)
    avg_rate = avg_rate_result.scalar()
    stmt = select(Image).filter(Image.id == image_id)
    image = await session.execute(stmt)
    image = image.scalar()
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    return RateImageResponse(image=image, avg_rate=avg_rate)


async def read_all_avg_rates(
        offset: int, limit: int, session: AsyncSession
) -> List[RateImageResponse] | None:
    """
    Returns a list of Image objects by average rate rating.
    Each object contains an image and its average rate.

    :param offset: int: Specify the number of rows to skip
    :param limit: int: Limit the number of results returned
    :param session: AsyncSession: Pass the session to the function
    :return: A list of image objects and rates
    """
    stmt = select(Image.id)
    stmt = stmt.offset(offset).limit(limit)
    all_image_id = await session.execute(stmt)
    all_image_id = all_image_id.scalars().all()
    table_rates = [
        await read_avg_rate_to_image(image_id, session) for image_id in all_image_id
    ]
    sort_table_rates = sorted(
        table_rates,
        key=lambda x: (
            x.avg_rate is None,
            -x.avg_rate if x.avg_rate is not None else None,
        ),
        reverse=False,
    )
    return sort_table_rates


async def create_rate_to_image(
        image_id: UUID4 | int, body: RateModel, user: User, session: AsyncSession
) -> Rate | None:
    """
    Creates a rate to image.

    :param image_id: UUID4 | int: Get the image from the database
    :param body: RateModel: Get the rate value from the request body
    :param user: User: Get the id of the user who is logged in
    :param session: AsyncSession: Create a database session
    :return: A rate object if the image exists,
    """
    image = await session.get(Image, image_id)
    if image and image.user_id != user.id:
        stmt = select(Rate).filter(
            and_(Rate.image_id == image_id, Rate.user_id == user.id)
        )
        rate = await session.execute(stmt)
        rate = rate.scalar()
        if not rate:
            rate_image = Rate(image_id=image_id, rate=body.rate, user_id=user.id)
            session.add(rate_image)
            await session.commit()
            await session.refresh(rate_image)
            return rate_image
    return None


async def delete_rate_to_image(
        rate_id: UUID4 | int, session: AsyncSession
) -> Rate | None:
    """
    Deletes a rate to image.

    :param rate_id: UUID4 | int: Specify which rate to delete
    :param session: AsyncSession: Pass the session to the function
    :return: The rate object if the rate was deleted,
    """
    stmt = select(Rate).filter(Rate.id == rate_id)
    rate = await session.execute(stmt)
    rate = rate.scalar()
    if rate:
        await session.delete(rate)
        await session.commit()
    return rate
