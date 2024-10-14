"""
Module of images' CRUD
"""
from sqlalchemy import select, UUID
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from app.src.database.models import Tag, User, Image, image_tag_m2m
async def get_image_by_id(image_id: UUID, session: AsyncSession) -> Image | None:
    """
    Gets an image with the specified id.
    :param image_id: The ID of the image to get.
    :type image_id: UUID
    :param session: The database session.
    :type session: AsyncSession
    :return: The image with the specified ID, or None if it does not exist.
    :rtype: Image | None
    """
    stmt = select(Image).filter(Image.id == image_id)
    image = await session.execute(stmt)
    return image.scalar()