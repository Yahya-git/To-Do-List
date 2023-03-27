from typing import List

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(attempted_password, hashed_password):
    return pwd_context.verify(attempted_password, hashed_password)


class Email(BaseModel):
    email: List[EmailStr]


conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_tls,
    MAIL_SSL_TLS=settings.mail_ssl,
    USE_CREDENTIALS=settings.use_credentials,
)


async def send_mail(email: Email, link: str, subject_template: str, template: str):
    message = MessageSchema(
        subject=subject_template, recipients=[email], body=template, subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
