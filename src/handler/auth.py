from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos import dto_users
from src.handler import utils
from src.models import users
from src.repository import checks
from src.repository import users as repository

local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)


async def login(
    user_credentials: OAuth2PasswordRequestForm,
    db: Session,
):
    user = repository.get_user(db, user_id=None, email=user_credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f'{"invalid credentials"}'
        )
    if not user.is_verified:
        try:
            token = repository.create_verification_token(db, user.id)
        except IntegrityError as e:
            print(f"Caught an exception while creating a token: {e}")
        try:
            await utils.send_verification_mail(user, token.token)
        except IntegrityError as e:
            print(f"Caught an exception while sending the email: {e}")
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to login"}',
        )
    if not utils.verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f'{"invalid credentials"}'
        )
    try:
        access_token = utils.create_access_token(data={"user_email": user.email})
    except IntegrityError as e:
        print(f"Caught an exception while creating the access token: {e}")
    return {"access_token": access_token, "token_type": "bearer"}


def oauth_login(
    user_credentials: dict,
    db: Session,
):
    user = (
        db.query(users.User)
        .filter(users.User.email == user_credentials["email"])
        .first()
    )
    try:
        access_token = utils.create_access_token(data={"user_email": user.email})
    except IntegrityError as e:
        print(f"Caught an exception while creating the access token: {e}")
    return {"access_token": access_token, "token_type": "bearer"}


async def login_google():
    return await utils.google_sso.get_login_redirect()


async def callback_google(request: Request, db: Session):
    user = await utils.google_sso.verify_and_process(request)
    user_data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user.id,
    }
    oauth_user = dto_users.CreateUserRequest(**user_data)
    oauth_check = repository.get_user(db, user.email)
    if checks.is_email_same(oauth_user, db) and oauth_check.is_oauth is True:
        data: dict = {"email": oauth_user.email, "password": oauth_user.password}
        access_token = oauth_login(data, db)
        return access_token
    try:
        new_oauth_user = repository.create_user(oauth_user, db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
    user_data = dto_users.UpdateUserRestricted(is_verified=True, is_oauth=True)
    repository.update_user_restricted(new_oauth_user.id, user_data, db)
    return {"message": "login again to get access token"}
