"""
Module of commentss' routes
"""

from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status
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
allowed_operation_non_user = RoleAccess([Role.administrator, Role.moderator])

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get(
    "/{image_id}",
    response_model=List[CommentResponse],
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])
async def read_all_comments_to_photo(
        image_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of comments for the specified image.

    :param image_id: UUID4 | int: Specify the image id of the photo to which we want to add a comment
    :param offset: int: Specify the offset from which to start returning comments
    :param ge: Set a minimum value for the parameter
    :param limit: int: Limit the amount of comments that are returned
    :param ge: Specify the minimum value for a parameter
    :param le: Limit the number of comments returned
    :param user: User: Get the current user
    :param session: AsyncSession: Create a new session to the database
    :param : Get the user who is logged in
    :return: A list of comments to the photo
    """
    return await repository_comments.read_all_comments_to_photo(image_id, offset, limit, session)


@router.get(
    "/comments/{comment_id}",
    response_model=List[CommentResponse],
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])
async def read_all_comments_to_comment(
        comment_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of comments that are replies to the comment with the given id.
    The offset and limit parameters can be used to paginate through all comments.


    :param comment_id: UUID4 | int: Specify the comment id to which we want to add a new comment
    :param offset: int: Skip the first n comments
    :param ge: Set the minimum value for a parameter
    :param limit: int: Limit the number of comments returned
    :param ge: Set the minimum value of a parameter
    :param le: Limit the number of comments that can be returned
    :param user: User: Get the current user and check if they are authenticated
    :param session: AsyncSession: Get the database session
    :param : Get the user who is currently logged in
    :return: A list of comments to the comment with id = comment_id
    """
    return await repository_comments.read_all_comments_to_comment(comment_id, offset, limit, session)


@router.get(
    "/my/comments",
    response_model=List[CommentResponse],
    dependencies=[Depends(allowed_operation_get)]
)
async def read_all_my_comments(
        current_user: User = Depends(auth_service.get_current_user),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of all comments made by the current user.

    :param current_user: User: Get the current user from the auth_service
    :param offset: int: Skip the first offset comments
    :param ge: Specify a minimum value for the parameter
    :param limit: int: Limit the number of comments returned
    :param ge: Specify that the value must be greater than or equal to a given number
    :param le: Limit the number of comments returned
    :param session: AsyncSession: Create a new database session
    :param : Get the current user
    :return: A list of comments
    """
    return await repository_comments.read_all_my_comments(current_user, offset, limit, session)


@router.get(
    "/user/comments",
    response_model=List[CommentResponse],
    dependencies=[Depends(allowed_operation_non_user)]
)
async def read_all_user_comments(
        user_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of comments for the specified user.

    :param user_id: UUID4 | int: Specify the user id of the comments to be returned
    :param offset: int: Specify the number of comments to skip
    :param ge: Specify the minimum value that can be accepted
    :param limit: int: Limit the number of comments returned
    :param ge: Specify that the value must be greater than or equal to a given number
    :param le: Limit the number of comments returned
    :param session: AsyncSession: Pass the database session to the repository layer
    :param : Get the comments of a specific user
    :return: A list of comments
    """
    return await repository_comments.read_all_user_comments(user_id, offset, limit, session)


@router.post(
    "/{image_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)]
)
async def create_comment_to_photo(
        image_id: UUID4 | int,
        body: CommentModel,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session)
):
    """
    Creates a comment to an image.

    :param image_id: UUID4 | int: Specify the image id that the comment will be added to
    :param body: CommentModel: Create a comment to the photo
    :param current_user: User: Get the current user from the auth_service
    :param session: AsyncSession: Pass the session to the repository layer
    :return: A comment
    """
    return await repository_comments.create_comment_to_photo(image_id, body, current_user, session)


@router.post(
    "/comment/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)])
async def create_comment_to_comment(comment_id: UUID4 | int, body: CommentModel,
                                    current_user: User = Depends(auth_service.get_current_user),
                                    session: AsyncSession = Depends(get_session)):
    """
    Creates a new comment to the comment with id = {comment_id}

    :param comment_id: UUID4 | int: Specify the comment id to which we want to add a comment
    :param body: CommentModel: Get the data from the request body
    :param current_user: User: Get the current user who is logged in
    :param session: AsyncSession: Create a new database session
    :return: The created comment, but it is not used anywhere
    """
    comment = await repository_comments.create_comment_to_comment(comment_id, body, current_user, session)
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
        """
        Updates a comment in the database.

        :param comment_id: UUID4 | int: Get the comment id from the url
        :param body: CommentModel: Get the data from the request body
        :param current_user: User: Get the user who is currently logged in
        :param session: AsyncSession: Get the database session
        :param : Get the comment id
        :return: A commentmodel object
        """
        comment = await repository_comments.update_comment(comment_id, body, current_user, session)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or forbiden to change for you"
            )
        return comment


@router.delete("/{comment_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(allowed_operation_remove),
                             Depends(auth_service.get_current_user)]
               )
async def delete_comment(
        comment_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
):
        """
        Deletes a comment from the database.

        :param comment_id: UUID4 | int: Specify the id of the comment to be deleted
        :param session: AsyncSession: Pass the database session to the repository layer
        :param : Get the current user
        :return: None, so the response will be empty
        """
        comment = await repository_comments.delete_comment(comment_id, session)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        return None