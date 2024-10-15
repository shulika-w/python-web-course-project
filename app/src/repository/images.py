"""
Module of images' CRUD
"""

from enum import Enum
import pickle

from fastapi import HTTPException, status
from redis.asyncio.client import Redis
from sqlalchemy import select, UUID, and_
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.conf.config import settings
from app.src.database.models import User, Image
import app.src.repository.tags as repository_tags
from app.src.schemas.images import (
    ImageModel,
    ImageDescriptionModel,
    CloudinaryTransformations,
    MAX_NUMBER_OF_TAGS_PER_IMAGE,
)
from app.src.services._cloudinary import cloudinary_service


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
        body: ImageModel, user: User, session: AsyncSession, cache: Redis
) -> Image:
    """
    Creates a new image.

    :param file: The uploaded file to create from.
    :type file: UploadFile
    :param body: The body for the image to create.
    :type body: ImageModel
    :param user: The user who creates the image.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The newly created image.
    :rtype: Image
    """
    result = await cloudinary_service.upload_image(
        body.file.file, user.username, body.file.filename
    )
    image_url = await cloudinary_service.get_image_url(result)
    image = Image(description=body.description, url=image_url, user_id=user.id)
    if body.tags:
        tags = []
        for tag_title in body.tags:
            tag = await repository_tags.read_tag(tag_title, session)
            if not tag:
                tag = await repository_tags.create_tag(tag_title, user, session)
            tags.append(tag)
        image.tags = tags
    session.add(image)
    await session.commit()
    await session.refresh(image)
    await set_image_in_cache(image, cache)
    return image


async def read_images(user_id: UUID | int, session: AsyncSession) -> ScalarResult:
    """
    Gets an image with the specified id.

    :param image_id: The ID of the image to get.
    :type image_id: UUID | int
    :param session: The database session.
    :type session: AsyncSession
    :return: The ScalarResult with list of images.
    :rtype: ScalarResult
    """
    stmt = select(Image).filter(Image.user_id == user_id)
    images = await session.execute(stmt)
    return images.scalars()


async def read_image(
        image_id: UUID | int,
        session: AsyncSession,
        cache: Redis,
) -> Image | None:
    """
    Gets an image with the specified id.

    :param image_id: The ID of the image to get.
    :type image_id: UUID | int
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The image with the specified ID, or None if it does not exist.
    :rtype: Image | None
    """
    image = await cache.get(f"image: {image_id}")
    if image:
        return pickle.loads(image)

    stmt = select(Image).filter(Image.id == image_id)
    image = await session.execute(stmt)
    return image.scalar()


async def update_image(
        image_id: UUID | int,
        transformations: Enum,
        user_id: UUID | int,
        session: AsyncSession,
        cache: Redis,
) -> Image | None:
    """
    Updates existing image

    :param image_id: Find the image to update
    :type image_id: UUID | int
    :param transformations: Image file transformation parameters.
    :type transformations: Enum
    :param user_id: Check if the user is allowed to update the image
    :type user_id: UUID | int
    :param session: Pass the current session to the function
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The Image object that was updated
    :rtype: Image | None
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        if transformations:
            for i in CloudinaryTransformations:
                if i.value in transformations:
                    image_url = await cloudinary_service.image_transformations(
                        image.url,
                        i.value,
                    )
        image.url = image_url
        await session.commit()
        await set_image_in_cache(image, cache)
    return image


async def patch_image(
        image_id: UUID | int,
        body: ImageDescriptionModel,
        user_id: UUID | int,
        session: AsyncSession,
        cache: Redis,
) -> Image | None:
    """
    Updates existing image

    :param image_id: Find the image to update
    :type image_id: UUID | int
    :param body: Get the fields from the request body
    :type body: ImageModel
    :param user_id: Id of the user to update the image
    :type user_id: UUID | int
    :param session: Pass the current session to the function
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The Image object that was patched
    :rtype: Image | None
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        image.description = body.description
        await session.commit()
        await set_image_in_cache(image, cache)
    return image


async def delete_image(
        image_id: UUID | int, user_id: UUID | int, session: AsyncSession
) -> Image | None:
    """
    Deletes an image from the database.

    :param image_id: Specify the id of the image to delete
    :type image_id: UUID | int
    :param user_id: Id of the user to delete the image
    :type user_id: UUID | int
    :param session: Pass the session to the function
    :type session: AsyncSession
    :return: The Image object that was deleted
    :rtype: Image | None
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        public_id = await cloudinary_service.get_public_id_from_url(image.url)
        await cloudinary_service.delete_image(public_id)
        await session.delete(image)
        await session.commit()
    return image


async def add_tag_to_image(
        image_id: UUID | int,
        tag_title: str,
        user_id: UUID | int,
        user: User,
        session: AsyncSession,
        cache: Redis,
) -> Image | None:
    """
    Add tag to the image.

    :param image_id: Specify the id of the image to add tag.
    :type image_id: UUID | int
    :param tag_title: The tag added to the image.
    :type tag_title: str
    :param user_id: Id of the user who tagged the image.
    :type user_id: UUID | int
    :param user: User who add tag.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The image with tag.
    :rtype: Image | None
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        if len(image.tags) == MAX_NUMBER_OF_TAGS_PER_IMAGE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can't exceeded the maximum number ({MAX_NUMBER_OF_TAGS_PER_IMAGE}) of tags per image",
            )
        tag = await repository_tags.read_tag(tag_title, session)
        if not tag:
            tag = await repository_tags.create_tag(tag_title, user, session)
        if tag not in image.tags:
            image.tags.append(tag)
            await session.commit()
            await set_image_in_cache(image, cache)
    return image


async def delete_tag_from_image(
        image_id: UUID | int,
        tag_title: str,
        user_id: UUID | int,
        session: AsyncSession,
        cache: Redis,
) -> Image | None:
    """
    Delete tag from the image.

    :param image_id: Specify the id of the image to delete tag.
    :type image_id: UUID | int
    :param tag_title: The tag deleted from the image.
    :type tag_title: str
    :param user_id: Id of the user who delete tag from the image.
    :type user_id: UUID | int
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The image without tag.
    :rtype: Image | None
    """
    stmt = select(Image).filter(and_(Image.id == image_id, Image.user_id == user_id))
    image = await session.execute(stmt)
    image = image.scalar()
    if image:
        tag = await repository_tags.read_tag(tag_title, session)
        if tag is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found",
            )
        if image.tags and tag in image.tags:
            image.tags.remove(tag)
            await session.commit()
            await set_image_in_cache(image, cache)
    return image
