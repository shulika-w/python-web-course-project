"""
Module of authentication class and methods
"""

from datetime import datetime, timedelta, timezone
from os import urandom
import pickle
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.conf.config import settings
from app.src.database.connect_db import get_session, get_redis_db1
from app.src.repository import users as repository_users


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = urandom(settings.secret_key_length)
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    def verify_password(self, plain_password: str, hashed_password: str):
        """
        Veryfies the corresponding between plain password and hashed password.

        :param plain_password: The plain password.
        :type plain_password: str
        :param hashed_password: The hashed password.
        :type hashed_password: str
        :return: the corresponding between plain password and hashed password (True/False).
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Gets the hashed password from the plain password.

        :param password: The plain password.
        :type password: str
        :return: A hashed password.
        :rtype: str
        """
        return self.pwd_context.hash(password)

    async def create_access_token(
            self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Creates the access token.

        :param data: The data to create the access token from.
        :type data: dict
        :param expires_delta: The time to live of the created access token.
        :type expires_delta: Optional[float]
        :return: The access token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.now(timezone.utc), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    async def create_refresh_token(
            self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Creates the refresh token.

        :param data: The data to create the refresh token from.
        :type data: dict
        :param expires_delta: The time to live of the created refresh token.
        :type expires_delta: Optional[float]
        :return: The refresh token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update(
            {
                "iat": datetime.now(timezone.utc),
                "exp": expire,
                "scope": "refresh_token",
            },
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token

    async def create_email_verification_token(
            self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Creates the email verification token.

        :param data: The data to create the email verification token from.
        :type data: dict
        :param expires_delta: The time to live of the created email verification token.
        :type expires_delta: Optional[float]
        :return: The email verification token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update(
            {
                "iat": datetime.now(timezone.utc),
                "exp": expire,
                "scope": "email_verification_token",
            }
        )
        encoded_email_verification_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_email_verification_token

    async def create_password_reset_token(
            self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Creates the password reset token.

        :param data: The data to create the password reset token from.
        :type data: dict
        :param expires_delta: The time to live of the created password reset token.
        :type expires_delta: Optional[float]
        :return: The password reset token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update(
            {
                "iat": datetime.now(timezone.utc),
                "exp": expire,
                "scope": "password_reset_token",
            }
        )
        encoded_password_reset_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_password_reset_token

    async def create_password_set_token(
            self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Creates the password set token.

        :param data: The data to create the password set token from.
        :type data: dict
        :param expires_delta: The time to live of the created password set token.
        :type expires_delta: Optional[float]
        :return: The password set token.
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update(
            {
                "iat": datetime.now(timezone.utc),
                "exp": expire,
                "scope": "password_set_token",
            }
        )
        encoded_password_set_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_password_set_token

    async def decode_access_token(self, access_token: str):
        """
        Decodes the access token.

        :param access_token: The access token to decode.
        :type access_token: str
        :return: The email from the access token.
        :rtype: EmailStr
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        try:
            payload = jwt.decode(
                access_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload.get("scope") == "access_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise credentials_exception

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decodes the refresh token.

        :param refresh_token: The refresh token to decode.
        :type refresh_token: str
        :return: The email from the refresh token.
        :rtype: EmailStr
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload.get("scope") == "refresh_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise credentials_exception

    async def decode_email_verification_token(self, email_verification_token: str):
        """
        Decodes the email verification token.

        :param email_verification_token: The email verification token to decode.
        :type email_verification_token: str
        :return: The email from the email verification token.
        :rtype: EmailStr
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token for email verification",
        )
        try:
            payload = jwt.decode(
                email_verification_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload.get("scope") == "email_verification_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise credentials_exception

    async def decode_password_reset_token(self, password_reset_token: str):
        """
        Decodes the password reset token.

        :param password_reset_token: The password reset token to decode.
        :type password_reset_token: str
        :return: The email from the password reset token.
        :rtype: EmailStr
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token for password reset",
        )
        try:
            payload = jwt.decode(
                password_reset_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload.get("scope") == "password_reset_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise credentials_exception

    async def decode_password_set_token(self, password_set_token: str):
        """
        Decodes the password set token.

        :param password_set_token: The password set token to decode.
        :type password_set_token: str
        :return: The email from the password set token.
        :rtype: EmailStr
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token for password setting",
        )
        try:
            payload = jwt.decode(
                password_set_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload.get("scope") == "password_set_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise credentials_exception

    async def get_expire_from_token(self, token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            expire = payload.get("exp")
            if expire is None:
                raise credentials_exception
            return expire
        except JWTError:
            raise credentials_exception

    async def blacklist_token(self, token: str, cache: Redis):
        expire = (
                round(
                    await auth_service.get_expire_from_token(token)
                    - datetime.now(timezone.utc).timestamp()
                )
                + 600
        )
        if expire > 0:
            await cache.set(f"token: {token}", pickle.dumps(True))
            await cache.expire(f"token: {token}", expire)

    async def check_token_in_black_list(self, token: str, cache: Redis):
        if await cache.get(f"token: {token}"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token",
            )

    async def get_current_user(
            self,
            access_token: str = Depends(oauth2_scheme),
            session: AsyncSession = Depends(get_session),
            cache: Redis = Depends(get_redis_db1),
    ):
        """
        Gets the current user.

        :param access_token: The access token to decode.
        :type access_token: str
        :param session: The database session.
        :type session: AsyncSession
        :param cache: The Redis client.
        :type cache: Redis
        :return: The current user.
        :rtype: User
        """
        await auth_service.check_token_in_black_list(access_token, cache)
        email = await auth_service.decode_access_token(access_token)
        user = await repository_users.get_user_by_email_from_cache(email, cache)
        if user is None:
            user = await repository_users.get_user_by_email(email, session)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            await repository_users.set_user_in_cache(user, cache)
        return user


auth_service = Auth()
