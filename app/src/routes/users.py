"""
Module of users' routes
"""

from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Query
from redis.asyncio.client import Redis
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session, get_redis_db1
from app.src.database.models import User, Role
from app.src.repository import comments as repository_comments
from app.src.repository import images as repository_images
from app.src.repository import rates as repository_rates
from app.src.repository import users as repository_users
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess
from app.src.schemas.comments import CommentResponse
from app.src.schemas.images import (
    ImageDb,
    ImageDescriptionModel,
    CloudinaryTransformations,
)
from app.src.schemas.rates import RateResponse
from app.src.schemas.users import UserDb, UserUpdateModel, UserSetRoleModel

router = APIRouter(prefix="/users", tags=["users"])

allowed_operations_for_self = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operations_for_moderate = RoleAccess([Role.administrator, Role.moderator])
allowed_operations_for_all = RoleAccess([Role.administrator])


@router.get(
    "/me",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_for_self)],
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
    dependencies=[Depends(allowed_operations_for_self)],
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
    dependencies=[Depends(allowed_operations_for_self)],
)
async def update_me(
        data: UserUpdateModel = Depends(UserUpdateModel.as_form),
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PUT-operation to '/me' users subroute and updates the current user's profile.

    :param data: The data for the user to update.
    :type data: UserUpdateModel
    :param file: The uploaded file to update avatar from.
    :type file: UploadFile
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The updated user.
    :rtype: User
    """
    return await repository_users.update_user(user.email, data, session, cache)


@router.patch(
    "/{username}/set_role",
    response_model=UserDb,
    dependencies=[Depends(allowed_operations_for_all)],
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
    dependencies=[Depends(allowed_operations_for_all)],
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
    dependencies=[Depends(allowed_operations_for_all)],
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


@router.get(
    "/{user_id}/images",
    response_model=List[ImageDb],
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_user_images(
        user_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
) -> ScalarResult:
    """
    Handles a GET-operation to images subroute '/{user_id}/images'.
        Gets of the user's images

    :param user_id: The Id of the current user.
    :type user_id: UUID | int
    :param session: Get the database session
    :type AsyncSession: The current session.
    :return: List of the user's images.
    :rtype: List
    """
    images = await repository_images.read_images(user_id, session)
    return images


@router.put(
    "/{user_id}/images/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def update_user_image(
        image_id: UUID4 | int,
        user_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
        transformations: List[CloudinaryTransformations] = Query(
            ...,
            description="""List of Cloudinary image transformations:

        none = "",
        crop (make avatar with face)= "c_thumb,g_face,h_200,w_200,z_1/f_auto/r_max/",
        resize (downscaling)= "ar_1.0,c_fill,h_250",
        rotate (turn 10 degrees clockwise [0-360])= "a_10/",
        improve = "e_improve:outdoor:29/",
        brightness = "e_brightness:80/",
        blackwhite = "e_blackwhite:49/",
        saturation = "e_saturation:50/",
        border = "bo_10px_solid_lightblue/",
        rounded_corners = "r_100/"
        """,
        ),
):
    """
    Handles a PUT operation for the images subroute '/{user_id}/images/{image_id}'.
        Updates the user's image.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :param transformations: The Enum list of the image file transformation parameters.
    :type transformations: List
    :return: The updated image object.
    :rtype: Image
    """
    image = await repository_images.update_image(
        image_id,
        transformations,
        user_id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.patch(
    "/{user_id}/images/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def patch_user_image(
        image_id: UUID4 | int,
        body: ImageDescriptionModel,
        user_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{user_id}/images/{image_id}'.
        Patches the image of the user.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param body: The data for the image to update.
    :type body: ImageDescriptionModel
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The patched image.
    :rtype: Image
    """
    image = await repository_images.patch_image(
        image_id,
        body,
        user_id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.delete(
    "/{user_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def delete_user_image(
        image_id: UUID4 | int,
        user_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
):
    """
    Handles a DELETE operation for the images subroute '/{user_id}/images/{image_id}'.
        Delete the image of the user.

    :param image_id: The Id of the image to delete.
    :type image_id: UUID4 | int
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param session: The database session.
    :type session: AsyncSession
    :return: None
    :type: None
    """
    image = await repository_images.delete_image(image_id, user_id, session)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return None


@router.patch(
    "/{user_id}/images/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def add_tag_to_user_image(
        image_id: UUID4 | int,
        tag_title: str,
        user_id: UUID4 | int,
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{user_id}/images{image_id}/tags/{tag_title}'.
        Patches the current user's image tag.

    :param image_id: The Id of the image to patch the tag.
    :type image_id: UUID4 | int
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: An image object.
    :rtype: Image
    """
    image = await repository_images.add_tag_to_image(
        image_id,
        tag_title,
        user_id,
        user,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.delete(
    "/{user_id}/images/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_all)],
)
async def delete_tag_from_user_image(
        image_id: UUID4 | int,
        tag_title: str,
        user_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a DELETE operation for the images subroute '/{user_id}/images{image_id}/tags/{tag_title}'.
        Deleted the current user's image tag.

    :param image_id: The Id of the image to delete the tag.
    :type image_id: UUID4 | int
    :param tag_title: The tag title for the image.
    :type tag_title: str
    :param user_id: The Id of the user.
    :type user_id: UUID4 | int
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: An image object.
    :rtype: Image
    """
    image = await repository_images.delete_tag_from_image(
        image_id,
        tag_title,
        user_id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.get(
    "/{user_id}/comments",
    response_model=List[CommentResponse],
    dependencies=[Depends(allowed_operations_for_moderate)],
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
    return await repository_comments.read_all_user_comments(
        user_id, offset, limit, session
    )


@router.get(
    "/{user_id}/rates",
    response_model=List[RateResponse],
    dependencies=[Depends(allowed_operations_for_moderate)],
)
async def read_all_user_rates(
        user_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of all rates for the user with the given id.

    :param user_id: UUID4 | int: Identify the user
    :param offset: int: Determine the starting point of the query
    :param ge: Check if the value is greater than or equal to a certain number
    :param limit: int: Limit the number of results returned
    :param ge: Specify that the value must be greater than or equal to the given value
    :param le: Limit the number of results returned
    :param session: AsyncSession: Get the session from the dependency injection
    :param : Get the user_id from the path
    :return: A list of rates
    """

    return await repository_rates.read_all_user_rates(user_id, offset, limit, session)
