"""
Module of images' CRUD
"""

import pickle

from fastapi import UploadFile
from redis.asyncio.client import Redis

from sqlalchemy import select, UUID
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import Tag, User, Image, image_tag_m2m
from app.src.schemas.images import ImageModel, ImageDb
from app.src.conf.config import settings
from app.src.services._cloudinary import upload_avatar


async def set_image_in_cache(image: Image, cache: Redis) -> None:
    """
    Sets an image in cache.

    :param image: The image to set in cache.
    :type image: Image
    :param cache: The Redis client.
    :type cache: Redis
    :return: None.
    :rtype: None
    """
    await cache.set(f"image: {image.id}", pickle.dumps(image))
    await cache.expire(f"image: {image.id}", settings.redis_expire)


async def create_image(
    body: ImageModel, file: UploadFile, user: User, session: AsyncSession, cache: Redis
) -> Image:
    """
    Creates a new image.

    :param body: The body for the image to create.
    :type body: ImageModel
    :param file: The uploaded file to create from.
    :type file: UploadFile
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The newly created image.
    :rtype: Image
    """
    if file:
        r = await upload_avatar(file, user.username)
    image = Image(**body.model_dump(), url=r.get("secure_url"))
    session.add(image)
    await session.commit()
    await session.refresh(image)
    await set_image_in_cache(image, cache)
    return image


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