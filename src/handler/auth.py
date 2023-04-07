from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_users
from src.handler.checks import is_email_same
from src.handler.utils import (
    create_access_token,
    google_sso,
    send_verification_mail,
    verify_password,
)
from src.models import users
from src.repository.database_queries import (
    create_user,
    create_verification_token_by_user_id,
    get_user_by_email,
    update_user_by_id_restricted,
)

local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)

get_db_session = Depends(get_db)
Depend = Depends()


async def login_handler(
    user_credentials: OAuth2PasswordRequestForm = Depend,
    db: Session = get_db_session,
):
    user = get_user_by_email(user_credentials.username, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    if not user.is_verified:
        try:
            token = create_verification_token_by_user_id(user.id, db)
        except IntegrityError as e:
            print(f"Caught an exception while creating a token: {e}")
        try:
            await send_verification_mail(user, token.token)
        except IntegrityError as e:
            print(f"Caught an exception while sending the email: {e}")
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to login"}',
        )
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    try:
        access_token = create_access_token(data={"user_email": user.email})
    except IntegrityError as e:
        print(f"Caught an exception while creating the access token: {e}")
    return {"access_token": access_token, "token_type": "bearer"}


def oauth_login(
    user_credentials: dict,
    db: Session = get_db_session,
):
    user = (
        db.query(users.User)
        .filter(users.User.email == user_credentials["email"])
        .first()
    )
    try:
        access_token = create_access_token(data={"user_email": user.email})
    except IntegrityError as e:
        print(f"Caught an exception while creating the access token: {e}")
    return {"access_token": access_token, "token_type": "bearer"}


async def login_google_handler():
    return await google_sso.get_login_redirect()


async def callback_google_handler(request: Request, db: Session = get_db_session):
    user = await google_sso.verify_and_process(request)
    user_data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user.id,
    }
    oauth_user = dto_users.CreateUserRequest(**user_data)
    oauth_check = get_user_by_email(user.email, db)
    if is_email_same(oauth_user, db=db) and oauth_check.is_oauth is True:
        data: dict = {"email": oauth_user.email, "password": oauth_user.password}
        access_token = oauth_login(user_credentials=data, db=db)
        return access_token
    try:
        new_oauth_user = create_user(oauth_user, db=db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
    user_data = dto_users.UpdateUserRestricted(is_verified=True, is_oauth=True)
    update_user_by_id_restricted(new_oauth_user.id, user_data, db)
    return {"message": "login again to get access token"}
