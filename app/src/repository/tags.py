"""
Module of tags' CRUD
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import Tag, User
from app.src.schemas.tags import TagModel


async def read_tags(
        offset: int,
        limit: int,
        tag_title: str,
        session: AsyncSession,
) -> ScalarResult:
    """
    Reads a list of tags with specified pagination parameters and search by title.

    :param offset: The number of tags to skip.
    :type offset: int
    :param limit: The maximum number of tags to return.
    :type limit: int
    :param tag_title: The string to search by title.
    :type tag_title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: A list of tags or None.
    :rtype: ScalarResult
    """
    stmt = select(Tag)
    if tag_title:
        stmt = stmt.filter(Tag.title.like(f"%{tag_title}%"))
    stmt = stmt.order_by(Tag.title).offset(offset).limit(limit)
    tags = await session.execute(stmt)
    return tags.scalars()


async def read_tag(tag_title: str, session: AsyncSession) -> Tag | None:
    """
    Reads a single tag with the specified title.

    :param tag_title: The title of the tag to retrieve.
    :type tag_title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: The tag with the specified title, or None if it does not exist.
    :rtype: Tag | None
    """
    stmt = select(Tag).filter(Tag.title == tag_title.lower())
    tag = await session.execute(stmt)
    return tag.scalar()


async def create_tag(tag_title: str, user: User, session: AsyncSession) -> Tag | None:
    """
    Creates a new tag with the specified title.

    :param tag_title: The title of the tag to create.
    :type tag_title: str
    :param user: The user who creates the tag.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The newly created tag or None if creation failed.
    :rtype: Tag | None
    """
    try:
        tag_model = TagModel(title=tag_title)
    except Exception as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error_message),
        )
    tag = Tag(title=tag_model.title.lower(), user_id=user.id)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


async def delete_tag(tag_title: str, session: AsyncSession) -> Tag | None:
    """
    Deletes a single tag with the specified title.

    :param tag_title: The title of the tag to delete.
    :type tag_title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: The deleted tag or None if it did not exist.
    :rtype: Tag | None
    """
    try:
        tag_model = TagModel(title=tag_title)
    except Exception as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error_message),
        )
    stmt = select(Tag).filter(Tag.title == tag_model.title.lower())
    tag = await session.execute(stmt)
    tag = tag.scalar()
    if tag:
        await session.delete(tag)
        await session.commit()
    return tag
