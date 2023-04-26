from datetime import datetime, timedelta

from aiosmtplib import SMTPDataError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from fastapi_sso.sso.google import GoogleSSO
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import settings
from src.dtos import dto_misc, dto_users
from src.exceptions import CreateError, SendEmailError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
oauth2 = Depends(oauth2_scheme)

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_TIME = settings.access_token_expire_time

google_sso = GoogleSSO(
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    redirect_uri=settings.redirect_url,
    allow_insecure_http=True,
    scope=["openid", "email", "profile"],
)


def create_access_token(data: dict):
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        print(f"Exception: {e}")
        raise CreateError from e


def verify_access_token(token: str, credentials_exception):
    try:
        decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: int = decoded_jwt.get("user_id")
        email: str = decoded_jwt.get("user_email")
        if email is None:
            raise credentials_exception
        token_data = dto_misc.TokenData(email=email, id=id)
    except JWTError:
        raise credentials_exception
    return token_data


def validate_user(token: str = oauth2):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f'{"could not validate credentials"}',
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = verify_access_token(token, credentials_exception)
    return user


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(attempted_password, hashed_password):
    return pwd_context.verify(attempted_password, hashed_password)


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


async def send_mail(email: dto_misc.EmailList, subject_template: str, template: str):
    message = MessageSchema(
        subject=subject_template, recipients=[email], body=template, subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_verification_mail(user: dto_users.UserResponse, token: int):
    verification_url = f"{settings.url}/users/verify-email?token={token}"
    try:
        await send_mail(
            email=user.email,
            subject_template="Verify Email",
            template=f"Click the following link to verify your email: {verification_url}",
        )
    except SMTPDataError as e:
        print(f"Exception: {e}")
        raise SendEmailError from e


async def send_reset_password_mail(user: dto_users.UserResponse, token: int):
    reset_password_url = f"{settings.url}/users/{user.id}/reset-password?token={token}"
    try:
        await send_mail(
            email=user.email,
            subject_template="Reset Password",
            template=f"Click the following link to reset your password: {reset_password_url}",
        )
    except SMTPDataError as e:
        print(f"Exception: {e}")
        raise SendEmailError from e
