"""
Module of authentication routes
"""


from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Security,
    BackgroundTasks,
    Request,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session, get_redis_db1
from app.src.database.models import User
from app.src.schemas.users import (
    UserModel,
    UserRequestEmail,
    UserPasswordSetModel,
    UserResponse,
)
from app.src.schemas.tokens import TokenModel, TokenPasswordSetModel
from app.src.repository import users as repository_users
from app.src.services.auth import auth_service
from app.src.services.email import (
    send_email_for_verification,
    send_email_for_password_reset,
)


router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserModel,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a POST-operation to '/signup' auth subroute and creates a new user.

    :param body: The data for the user to create.
    :type body: UserModel
    :param background_tasks: The object for background tasks.
    :type background_tasks: BackgroundTasks
    :param request: The http request object.
    :type request: Request
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with the newly created user and the message.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, session)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="The account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    user = await repository_users.create_user(body, session, cache)
    email_verification_token = await auth_service.create_email_verification_token(
        {"sub": user.email}
    )
    background_tasks.add_task(
        send_email_for_verification,
        user.email,
        user.username,
        email_verification_token,
        request.base_url,
    )
    return {
        "user": user,
        "message": "The user successfully created. Check your email for confirmation",
    }


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a POST-operation to '/login' auth subroute and does login of user.

    :param body: The request body with data of the user to login.
    :type body: OAuth2PasswordRequestForm
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with generated tokens.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.username, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.is_email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The email is not confirmed",
        )
    if not user.is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password reset is not confirmed",
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_refresh_token(user, refresh_token, session, cache)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Security(security),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    token = credentials.credentials
    await auth_service.check_token_in_black_list(token, cache)
    email = await auth_service.decode_access_token(token)
    user = await repository_users.get_user_by_email(email, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    await auth_service.blacklist_token(token, cache)
    return {"message": "Logout is successful"}


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a GET-operation to '/refresh_token' auth subroute and updates a refresh token for a specific user.

    :param credentials: The http authorization credentials of user to update the refresh token for.
    :type credentials: HTTPAuthorizationCredentials
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with generated tokens.
    :rtype: dict
    """
    token = credentials.credentials
    await auth_service.check_token_in_black_list(token, cache)
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    await auth_service.blacklist_token(token, cache)
    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/verification_email")
async def request_verification_email(
    body: UserRequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a POST-operation to '/verification_email' auth subroute and sends an email for verification of the user's email.

    :param body: The request body with an email to verify.
    :type body: UserRequestEmail
    :param background_tasks: The object for background tasks.
    :type background_tasks: BackgroundTasks
    :param request: The http request object.
    :type request: Request
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with a message.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, session)
    if user:
        if user.is_email_confirmed:
            return {"message": "The email is already confirmed"}
        if user.is_password_valid:
            email_verification_token = (
                await auth_service.create_email_verification_token({"sub": user.email})
            )
            background_tasks.add_task(
                send_email_for_verification,
                user.email,
                user.username,
                email_verification_token,
                request.base_url,
            )
    return {"message": "Check your email for confirmation"}


@router.get("/confirm_email/{token}")
async def confirm_email(
    token: str,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a GET-operation to '/confirm_email/{token}' auth subroute and confirms the user's email.

    :param token: The email verification token.
    :type token: str
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with a message.
    :rtype: dict
    """
    email = await auth_service.decode_email_verification_token(token)
    user = await repository_users.get_user_by_email(email, session)
    if user is None or not user.is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.is_email_confirmed:
        return {"message": "The email is already confirmed"}
    await repository_users.confirm_email(email, session, cache)
    return {"message": "Email confirmed"}


@router.post("/password_reset_email")
async def request_password_reset_email(
    body: UserRequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a POST-operation to '/password_reset_email' auth subroute and sends an email for the user's password reset.

    :param body: The request body with an user's email to reset password.
    :type body: UserRequestEmail
    :param background_tasks: The object for background tasks.
    :type background_tasks: BackgroundTasks
    :param request: The http request object.
    :type request: Request
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with a message.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, session)
    if user and user.is_email_confirmed:
        password_reset_token = await auth_service.create_password_reset_token(
            {"sub": user.email}
        )
        background_tasks.add_task(
            send_email_for_password_reset,
            user.email,
            user.username,
            password_reset_token,
            request.base_url,
        )
    return {"message": "Check your email for a password reset"}


@router.get("/reset_password/{token}", response_model=TokenPasswordSetModel)
async def reset_password(
    token: str,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a GET-operation to '/reset_password/{token}' auth subroute and resets the user's password.

    :param token: The password reset token.
    :type token: str
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with the password set token.
    :rtype: dict
    """
    email = await auth_service.decode_password_reset_token(token)
    user = await repository_users.get_user_by_email(email, session)
    if user is None or not user.is_email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Reset password error"
        )
    if user.is_password_valid:
        await repository_users.reset_password(email, session, cache)
    password_set_token = await auth_service.create_password_set_token(
        data={"sub": email}
    )
    return {"password_set_token": password_set_token}


@router.patch("/set_password/{token}")
async def set_password(
    token: str,
    body: UserPasswordSetModel,
    session: AsyncSession = Depends(get_session),
    cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH-operation to '/set_password/{token}' auth subroute and sets the user's new password.

    :param token: The password set token.
    :type token: str
    :param body: The request body with the user's new password.
    :type body: UserPasswordSetModel
    :param session: The database session.
    :type session: AsyncSession
    :return: The dict with a message.
    :rtype: dict
    """
    email = await auth_service.decode_password_set_token(token)
    user = await repository_users.get_user_by_email(email, session)
    if user is None or not user.is_email_confirmed or user.is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set password error",
        )
    body.password = auth_service.get_password_hash(body.password)
    await repository_users.set_password(email, body.password, session, cache)
    return {"message": "The password has been reset"}