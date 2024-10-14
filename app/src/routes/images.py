"""
Module of images' routes
"""
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
from app.src.schemas.users import UserDb, UserUpdateModel, UserSetRoleModel, UserUpdateForm
from app.src.conf.config import settings
URL = f"{settings.api_protocol}://{settings.api_host}:{settings.api_port}/api/images/"
router = APIRouter(prefix="/images", tags=["images"])
allowed_operations_read_update = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operations_activate_inactivate_set_role = RoleAccess([Role.administrator])
@router.get(
    "/api/images/{image_id}/get_qr_code",
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