from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import create_email_token
from src.conf.config import config

conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=config.MAIL_STARTTLS,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    USE_CREDENTIALS=config.USE_CREDENTIALS,
    VALIDATE_CERTS=config.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)

async def send_email_for_confirm(email: EmailStr, username: str, host: str):
    """
       Send an email to the user with a verification link for confirming their email address.

       Args:
           email (EmailStr): Recipient's email address.
           username (str): Username of the recipient.
           host (str): Host URL to generate verification link.
       """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)

async def send_email_for_reset_password(email: EmailStr, username: str, host: str):
    """
       Send an email to the user with a token link to reset their password.

       Args:
           email (EmailStr): Recipient's email address.
           username (str): Username of the recipient.
           host (str): Host URL to generate password reset link.
       """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as err:
        print(err)
