"""
Module of users' CRUD
"""

import pickle

from libgravatar import Gravatar
from pydantic import EmailStr
from redis.asyncio.client import Redis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.conf.config import settings
from app.src.database.models import Role, User
from app.src.schemas.users import UserModel, UserUpdateModel
from app.src.services._cloudinary import cloudinary_service

async def set_user_in_cache(user: User, cache: Redis) -> None:
    """
    Sets an user in cache.

    :param user: The user to set in cache.
    :type user: User
    :param cache: The Redis client.
    :type cache: Redis
    :return: None.
    :rtype: None
    """
    await cache.set(f"user: {user.email}", pickle.dumps(user))
    await cache.expire(f"user: {user.email}", settings.redis_expire)


async def get_user_by_email_from_cache(email: EmailStr, cache: Redis) -> User | None:
    """
    Gets an user with the specified email from cache.

    :param email: The email of the user to get.
    :type email: EmailStr
    :param cache: The Redis client.
    :type cache: Redis
    :return: The user with the specified email, or None if it does not exist in cache.
    :rtype: User | None
    """
    user = await cache.get(f"user: {email}")
    if user:
        return pickle.loads(user)


async def get_user_by_email(email: EmailStr, session: AsyncSession) -> User | None:
    """
    Gets an user with the specified email.

    :param email: The email of the user to get.
    :type email: EmailStr
    :param session: The database session.
    :type session: AsyncSession
    :return: The user with the specified email, or None if it does not exist.
    :rtype: User | None
    """
    stmt = select(User).filter(User.email == email)
    user = await session.execute(stmt)
    return user.scalar()


async def create_user(body: UserModel, session: AsyncSession, cache: Redis) -> User:
    """
    Creates a new user.

    :param body: The request body with data for the user to create.
    :type body: UserModel
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The newly created user.
    :rtype: User
    """
    stmt = select(User)
    users = await session.execute(stmt)
    if users.scalars().all():
        role = Role.user
    else:
        role = Role.administrator
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception:
        pass
    user = User(**body.model_dump(), avatar=avatar, role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    await set_user_in_cache(user, cache)
    return user


async def update_user(
    email: EmailStr,
    data: UserUpdateModel,
    session: AsyncSession,
    cache: Redis,
) -> User:
    """
    Updates an user's profile.

    :param data: The data for the user to update.
    :type data: UserUpdateModel
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: The updated user's profile.
    :rtype: User
    """
    user = await get_user_by_email(email, session)
    user.first_name = data.first_name
    user.last_name = data.last_name
    user.phone = data.phone
    user.birthday = data.birthday
    if data.avatar:
        user.avatar = await cloudinary_service.upload_avatar(
            data.avatar.file, user.username, data.avatar.filename
        )
    await session.commit()
    await set_user_in_cache(user, cache)
    return user


async def confirm_email(email: EmailStr, session: AsyncSession, cache: Redis) -> None:
    """
    Confirms an email of user.

    :param email: The email of user to confirm.
    :type email: EmailStr
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.is_email_confirmed = True
    await session.commit()
    await set_user_in_cache(user, cache)


async def reset_password(email: EmailStr, session: AsyncSession, cache: Redis) -> None:
    """
    Resets a password of user with specified email.

    :param email: The email of user to resets a password for.
    :type email: EmailStr
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.is_password_valid = False
    await session.commit()
    await set_user_in_cache(user, cache)


async def set_password(
    email: EmailStr, password: str, session: AsyncSession, cache: Redis
) -> None:
    """
    Sets a password of user with specified email.

    :param email: The email of user to set a password for.
    :type email: EmailStr
    :param password: The new password.
    :type password: str
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.password = password
    user.is_password_valid = True
    await session.commit()
    await set_user_in_cache(user, cache)


async def update_avatar(
    email: EmailStr, url: str, session: AsyncSession, cache: Redis
) -> User:
    """
    Updates an avatar of user with specified email.

    :param email: The email of user to update an avatar for.
    :type email: EmailStr
    :param url: The url of a new avatar.
    :type url: str
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, session)
    user.avatar = url
    await session.commit()
    await set_user_in_cache(user, cache)
    return user