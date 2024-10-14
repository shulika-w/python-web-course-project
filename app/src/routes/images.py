"""
Module of images' routes
"""

from dataclasses import asdict
from typing import List, Annotated

from pydantic import UUID4
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status, Query
from fastapi.responses import FileResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session, get_redis_db1
from app.src.database.models import User, Role, Image
from app.src.repository import images as repository_images
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess
from app.src.services.qr_code import generate_qr_code
from app.src.schemas.images import (
    ImageModel,
    ImageCreateForm,
    ImageDb,
    ImageUrlModel,
    CloudinaryTransformations,
)

from app.src.schemas.users import UserDb, UserUpdateModel, UserSetRoleModel, UserUpdateForm
from app.src.conf.config import settings


router = APIRouter(prefix="/images", tags=["images"])

allowed_operations_read_update = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operation_remove = RoleAccess([Role.administrator])
allowed_operations_activate_inactivate_set_role = RoleAccess([Role.administrator])


@router.post(
    "/",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def create_image(
    file: Annotated[UploadFile, File()],
    data: ImageCreateForm = Depends(),
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a POST-operation to '/api/images/' images subroute and create image.

    :param data: The data for the image to create.
    :type data: ImageCreateForm
    :param file: The uploaded file to create avatar from.
    :type file: UploadFile
    :param session: Get the database session
    :type AsyncSession: The current session.
    :param cache: The Redis client.
    :type cache: Redis
    :return: The FileResponse.
    :rtype FileResponse: Reply with a file in image/png format.
    """
    try:
        data = ImageModel(**asdict(data))
    except Exception as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error_message),
        )
    image = await repository_images.create_image(file, data, user, session, cache)
    return image


@router.get(
    "/get_qr_code/{image_id}",
    response_class=FileResponse,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def get_qr_code(
    image_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to '/api/images/get_qr_code/{image_id}' images subroute and gets FileResponse.

    :param image_id: UUID of the image.
    :type image_id: str
    :param session: Get the database session
    :type AsyncSession: The current session.
    :return: The FileResponse.
    :rtype FileResponse: Reply with a file in image/png format.
    """
    image = await repository_images.get_image_by_id(image_id, session)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    image_url = image.url
    generate_qr_code(image_url)
    return FileResponse(
        "static/qrcode.png",
        media_type="image/png",
        filename="qrcode.png",
        status_code=200,
    )


@router.get(
    "/my_images",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def get_my_images(
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> List:
    """
    Handles a GET-operation to '/my_images' images subroute and gets images of current user.

    :param user: The current user.
    :type user: User
    :return: Images of the current user.
    :rtype: Images
    """
    images = await repository_images.get_my_images(user.id, session)
    return images


@router.get(
    "/user_images/{user_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def get_user_images(
    user_id,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> List:
    """
    Handles a GET-operation to '/{username}' users subroute and gets the current user.

    :param user: The current user.
    :type user: User
    :return: The current user.
    :rtype: User
    """
    images = await repository_images.get_user_images(user.id, session)
    return images


@router.patch(
    "/update_image/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def update_image(
    image_id: UUID4 | int,
    body: ImageModel,
    current_user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    The update_image function updates a image in the database.
        The function takes an image_id, and a body of type ImageModel.
        It returns the updated image.

    :param image_id: UUID4 | int: The image id from the database
    :param body: ImageModel: The data from the request body
    :param current_user: User: The user who is currently logged in
    :param session: AsyncSession: The database session
    :return ImageDb: A ImageDb object
    """
    image = await repository_images.update_image(image_id, body, current_user, session)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or forbiden to change for you",
        )
    return image


@router.put(
    "/patch_image/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def patch_image(
    image_id: UUID4 | int,
    body: ImageUrlModel,
    current_user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    transformations: List[CloudinaryTransformations] = Query(
        ...,
        description="List of Cloudinary image transformations",
        example=["crop", "resize"],
    ),
):
    """
    The update_image function patch a image in the database.
        The function takes an image_id, and a body of type ImageModel.
        It returns the updated image.

    :param image_id: UUID4 | int: The image id from the database
    :param body: ImageModel: The data from the request body
    :param current_user: User: The user who is currently logged in
    :param session: AsyncSession: The database session
    :param transformations: Enum: Image file transformation parameters.
    :return ImageDb: An image model object
    """
    image = await repository_images.patch_image(
        image_id,
        body,
        current_user,
        session,
        transformations,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or forbiden to change for you",
        )
    return image


@router.delete(
    "/delete_image/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(allowed_operation_remove),
        Depends(auth_service.get_current_user),
    ],
)
async def delete_image(
    image_id: UUID4 | int,
    session: AsyncSession = Depends(get_session),
):
    """
    Deletes an image from the database.

    :param image_id: UUID4 | int: Specify the id of the image to be deleted
    :param current_user: User: Get the current user from the auth_service
    :param session: AsyncSession: Pass the database session to the repository layer
    :return: None, so the response will be empty
    """
    image = await repository_images.delete_image(image_id, session)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return None