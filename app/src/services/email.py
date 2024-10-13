"""
Module of email sending functions
"""


from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr, HttpUrl

from app.src.conf.config import settings


conf = ConnectionConfig(
    MAIL_SERVER=settings.mail_server,
    MAIL_PORT=settings.mail_port,
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email_for_verification(
    email: EmailStr, username: str, email_verification_token: str, host: HttpUrl
):
    """
    Sends an email for verification of the user's email.

    :param email: The email to verify.
    :type email: EmailStr
    :param username: The user's username.
    :type username: User
    :param email_verification_token: The email verification token.
    :type email_verification_token: str
    :param host: The api host.
    :type host: HttpUrl
    :return: None.
    :rtype: None
    """
    try:
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": email_verification_token,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verification_email.html")
    except ConnectionErrors as error_message:
        print(f"Connection error: {str(error_message)}")


async def send_email_for_password_reset(
    email: EmailStr, username: str, password_reset_token: str, host: HttpUrl
):
    """
    Sends an email for the user's password reset.

    :param email: The email to reset password.
    :type email: EmailStr
    :param username: The user's username.
    :type username: User
    :param password_reset_token: The password reset token.
    :type password_reset_token: str
    :param host: The api url.
    :type host: HttpUrl
    :return: None.
    :rtype: None
    """
    try:
        message = MessageSchema(
            subject="Password reset",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": password_reset_token,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="password_reset_email.html")
    except ConnectionErrors as error_message:
        print(f"Connection error: {str(error_message)}")