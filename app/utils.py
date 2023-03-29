from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from fastapi_sso.sso.google import GoogleSSO
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import database, models

from .config import settings
from .schemas import schemas_misc

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_TIME)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = decoded_jwt.get("user_email")
        if email is None:
            raise credentials_exception
        token_data = schemas_misc.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    return token_data


def get_current_user(
    # trunk-ignore(ruff/B008)
    token: str = Depends(oauth2_scheme),
    # trunk-ignore(ruff/B008)
    db: Session = Depends(database.get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f'{"could not validate credentials"}',
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.email == token.email).first()
    return user


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)


def verify(attempted_password, hashed_password):
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


async def send_mail(
    email: schemas_misc.Email, link: str, subject_template: str, template: str
):
    message = MessageSchema(
        subject=subject_template, recipients=[email], body=template, subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
