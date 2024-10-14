"""
Module of users' routes
"""


from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session, get_redis_db1
from app.src.database.models import User, Role
from app.src.repository import users as repository_users
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess
from app.src.schemas.users import UserDb, UserUpdateModel, UserSetRoleModel, UserUpdateForm


router = APIRouter(prefix="/users", tags=["users"])

allowed_operations_read_update = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operations_activate_inactivate_set_role = RoleAccess([Role.administrator])


@router.get(
    "/me",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def read_me(user: User = Depends(auth_service.get_current_user)):
    """
    Handles a GET-operation to '/me' users subroute and gets the current user.

    :param user: The current user.
    :type user: User
    :return: The current user.
    :rtype: User
    """
    return user


@router.get(
    "/{username}",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def read_user(username: str, session: AsyncSession = Depends(get_session)):
    """
    Handles a GET-operation to '/{username}' users subroute and gets the user's profile with specified username.

    :param username: The username of the user to read.
    :type username: str
    :param session: The database session.
    :type session: AsyncSession
    :return: The user's profile with specified username.
    :rtype: User
    """
    user = await repository_users.get_user_by_username(username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.put(
    "/me",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def update_me(
    data: UserUpdateForm = Depends(),
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PUT-operation to '/me' users subroute and updates the current user's profile.

    :param data: The data for the user to update.
    :type data: UserUpdateModel
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The updated user.
    :rtype: User
    """
    try:
        data = UserUpdateModel(**asdict(data))
    except Exception as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error_message),
        )
    return await repository_users.update_user(user.email, data, session, cache)


@router.patch(
    "/{username}/set_role",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_activate_inactivate_set_role)],
)
async def set_role_for_user(
    username: str,
    body: UserSetRoleModel,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH-operation to '/{username}/set_role' users subroute and sets an user's role.

    :param username: The username of the user to set role.
    :type username: str
    :param body: The request body with data for an user's role to set.
    :type body: UserSetRoleModel
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The user for whom the role is set.
    :rtype: User
    """
    user = await repository_users.get_user_by_username(username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return await repository_users.set_role_for_user(username, body.role, session, cache)


@router.patch(
    "/{username}",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_activate_inactivate_set_role)],
)
async def activate_user(
    username: str,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH-operation to '/{username}' users subroute and activates the user with specified username.

    :param username: The username of the user to activate.
    :type username: str
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The activated user.
    :rtype: User
    """
    user = await repository_users.get_user_by_username(username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return await repository_users.activate_user(username, session, cache)


@router.delete(
    "/{username}",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_activate_inactivate_set_role)],
)
async def inactivate_user(
    username: str,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """

    Handles a DELETE-operation to '/{username}' users subroute and inactivates the user with specified username.
    :param username: The username of the user to inactivate.
    :type username: str
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The inactivated user.
    :rtype: User
    """
    user = await repository_users.get_user_by_username(username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return await repository_users.inactivate_user(username, session, cache)