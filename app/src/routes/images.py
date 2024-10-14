"""
Module of images' routes
"""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.responses import FileResponse
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session, get_redis_db1
from app.src.database.models import User, Role, Image
from app.src.repository import images as repository_images
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess
from app.src.services.qr_code import generate_qr_code
from app.src.schemas.images import ImageModel, ImageCreateForm, ImageDb
from app.src.schemas.users import UserDb, UserUpdateModel, UserSetRoleModel, UserUpdateForm
from app.src.conf.config import settings


URL = f"{settings.api_protocol}://{settings.api_host}:{settings.api_port}/api/images/"
router = APIRouter(prefix="/images", tags=["images"])

allowed_operations_read_update = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operations_activate_inactivate_set_role = RoleAccess([Role.administrator])


@router.post(
    "/",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def create_image(
    data: ImageCreateForm = Depends(),
    file: Annotated[UploadFile, File()] = None,
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
    image = await repository_images.create_image(data, file, user, session, cache)
    return image


@router.get(
    "/{image_id}/get_qr_code",
    response_class=FileResponse,
    dependencies=[Depends(allowed_operations_read_update)],
)
async def get_qr_code(
    image_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to '/api/images/{image_id}/get_qr_code' images subroute and gets FileResponse.

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
    url_image = URL + "{image_id}"
    qr_code_bytes = generate_qr_code(url_image)
    return FileResponse(
        qr_code_bytes,
        media_type="image/png",
        filename="qrcode.png",
        status_code=200,
    )