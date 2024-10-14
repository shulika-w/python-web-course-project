"""
Module of tags' routes
"""
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session
from app.src.database.models import User, Role
from app.src.repository import tags as repository_tags
from app.src.schemas.tags import TagModel, TagResponse
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess

router = APIRouter(prefix="/tags", tags=["tags"])

allowed_operations_read_create = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operation_delete = RoleAccess([Role.administrator])


@router.get(
    "",
    response_model=List[TagResponse],
    dependencies=[Depends(allowed_operations_read_create)],
)
async def read_tags(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        tag_title: str = Query(default=None),
        session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to tags route and reads a list of tags with specified pagination parameters and search by title.

    :param offset: The number of tags to skip (default = 0, min value = 0).
    :type offset: int
    :param limit: The maximum number of tags to return (default = 10, min value = 1, max value = 1000).
    :type limit: int
    :param title: The string to search by title.
    :type title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: A list of tags or None.
    :rtype: ScalarResult
    """
    return await repository_tags.read_tags(offset, limit, tag_title, session)


@router.get(
    "/{tag_title}",
    response_model=TagResponse,
    dependencies=[Depends(allowed_operations_read_create)],
)
async def read_or_create_tag(
        tag_title: str,
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to '/{tag_title}' tags subroute and reads a single tag with the specified title or creates a new one.

    :param tag_title: The title of the tag to retrieve or create.
    :type tag_title: str
    :param user: The authenticated user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The tag with the specified title.
    :rtype: Tag
    """
    try:
        tag_model = TagModel(title=tag_title)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag's title shouldn't be less than 2 and more than 25 symbols and include #",
        )
    tag = await repository_tags.read_tag(tag_model.title, session)
    if tag is None:
        tag = await repository_tags.create_tag(tag_model.title, user, session)
    return tag


@router.delete(
    "/{tag_title}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allowed_operation_delete)],
)
async def delete_tag(
        tag_title: str,
        session: AsyncSession = Depends(get_session),
):
    """
    Handles a DELETE-operation to '/{tag_title}' tags subroute and deletes a single tag with the specified title.

    :param tag_title: The title of the tag to delete.
    :type tag_title: str
    :param session: The database session.
    :type session: AsyncSession
    :return: None.
    :rtype: None
    """
    try:
        tag_model = TagModel(title=tag_title)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag's title shouldn't be less than 2 and more than 25 symbols and include #",
        )
    tag = await repository_tags.delete_tag(tag_model.title, session)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    return None
