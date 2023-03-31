from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import utils
from app.dtos import dto_misc, dto_users

from ..database.database import get_db
from ..database.models import users
from .users import (
    check_email,
    create_new_token,
    create_new_user,
    send_verification_mail,
)

local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)


router = APIRouter(tags=["Auth"])

get_db_session = Depends(get_db)
Depend = Depends()


# User Login Endpoint
@router.post(
    "/login", status_code=status.HTTP_202_ACCEPTED, response_model=dto_misc.Token
)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depend,
    db: Session = get_db_session,
):
    user = (
        db.query(users.User)
        .filter(users.User.email == user_credentials.username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    if not user.is_verified:
        token = create_new_token(user, db)
        await send_verification_mail(user, token)
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to login"}',
        )
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    access_token = utils.create_access_token(data={"user_email": user.email})
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
    access_token = utils.create_access_token(data={"user_email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# User Google Login Endpoint
@router.get("/login/oauth")
async def login_google():
    return await utils.google_sso.get_login_redirect()


@router.get("/login/google/callback", status_code=status.HTTP_202_ACCEPTED)
async def callback_google(request: Request, db: Session = get_db_session):
    user = await utils.google_sso.verify_and_process(request)
    user_data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user.id,
    }
    oauth_user = dto_users.CreateUserRequest(**user_data)
    oauth_check = (
        db.query(users.User).filter(users.User.email == oauth_user.email).first()
    )
    if check_email(oauth_user, db=db) and oauth_check.is_oauth is True:
        data: dict = {"email": oauth_user.email, "password": oauth_user.password}
        access_token = oauth_login(user_credentials=data, db=db)
        return access_token
    try:
        new_oauth_user = create_new_user(oauth_user, db=db)
        new_oauth_user.is_verified = True
        new_oauth_user.is_oauth = True
        db.commit()
        return {"message": "login again to get access token"}
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
