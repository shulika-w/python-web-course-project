"""
Module of users' routes
"""


import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session, get_redis_db1
from app.src.database.models import User
from app.src.repository import users as repository_users
from app.src.services.auth import auth_service
from app.src.conf.config import settings
from app.src.schemas.users import UserDb


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserDb)
async def read_me(user: User = Depends(auth_service.get_current_user)):
    """
    Handles a GET-operation to '/me' users subroute and gets the current user.

    :param user: The current user.
    :type user: User
    :return: The current user.
    :rtype: User
    """
    return user


@router.patch("/avatar", response_model=UserDb)
async def update_avatar(
    file: UploadFile = File(),
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH-operation to '/avatar' users subroute and updates an user's avatar.

    :param file: The uploaded file to update avatar from.
    :type file: UploadFile
    :param user: The user to update avatar.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The updated user.
    :rtype: User
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    api_name = settings.api_name.replace(" ", "_")
    try:
        r = cloudinary.uploader.upload(
            file.file,
            public_id=f"{api_name}/{user.username}",
            overwrite=True,
        )
        src_url = cloudinary.CloudinaryImage(f"{api_name}/{user.username}").build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
    except Exception as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload image error: {str(error_message)}",
        )
    user = await repository_users.update_avatar(user.email, src_url, session, cache)
    return user