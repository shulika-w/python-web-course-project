"""
Module of commentss' routes
"""

from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session
from app.src.database.models import User, Role
from app.src.repository import comments as repository_comments
from app.src.schemas.comments import CommentModel, CommentResponse
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess


allowed_operation_get = RoleAccess([Role.administrator, Role.moderator, Role.user])
allowed_operation_create = RoleAccess(
    [Role.administrator, Role.moderator, Role.user])
allowed_operation_update = RoleAccess(
    [Role.administrator, Role.moderator, Role.user])
allowed_operation_remove = RoleAccess([Role.administrator, Role.moderator])

router = APIRouter(prefix="/comments", tags=["comments"])

@router.get("/{image_id}", response_model=list[CommentResponse], dependencies=[Depends(allowed_operation_get)])
async def read_all_comments_to_photo(
    image_id: UUID4 | int,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await repository_comments.read_all_comments_to_photo(image_id, session)


@router.post(
    "/{image_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)])
async def create_comment(image_id: UUID4 | int, body: CommentModel, current_user: User = Depends(auth_service.get_current_user), session: AsyncSession = Depends(get_session)):
    return await repository_comments.create_comment(image_id, body, current_user, session)


@router.post(
    "/comment/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)])
async def create_comment_to_comment(comment_id: UUID4 | int, body: CommentModel, current_user: User = Depends(auth_service.get_current_user), session: AsyncSession = Depends(get_session)):
    comment = await repository_comments.create_to_comment(comment_id, body, current_user, session)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or forbiden to comment for comment"
        )
    return comment


@router.patch("/{comment_id}", response_model=CommentResponse, dependencies=[Depends(allowed_operation_update)])
async def update_comment(
    comment_id: UUID4 | int,
    body: CommentModel,
    current_user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comment = await repository_comments.update_comment(comment_id, body, current_user, session)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or forbiden to change for you"
        )
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allowed_operation_remove)])
async def delete_comment(
    comment_id: UUID4 | int,
    current_user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comment = await repository_comments.delete_comment(comment_id, current_user, session)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    return None