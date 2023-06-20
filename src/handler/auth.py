from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.dtos import dto_users
from src.exceptions import (
    CreateError,
    DuplicateEmailError,
    GetError,
    SendEmailError,
    UpdateError,
)
from src.handler import utils
from src.repository import checks
from src.repository import users as repository


async def login(
    user_credentials: OAuth2PasswordRequestForm,
    db: Session,
):
    try:
        user = repository.get_user(db, user_id=None, email=user_credentials.username)
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f'{"invalid credentials"}'
        ) from None
    if not user.is_verified:
        try:
            token = repository.create_verification_token(user.id, db)
        except CreateError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'{"something went wrong while creating a token"}',
            ) from None
        try:
            await utils.send_verification_mail(user, token.token)
        except SendEmailError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'{"something went wrong while sending an email"}',
            ) from None
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to login, verification email has been sent"}',
        )
    if not utils.verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f'{"invalid credentials"}'
        )
    try:
        access_token = utils.create_access_token(
            data={"user_email": user.email, "user_id": user.id}
        )
    except CreateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while creating a token"}',
        ) from None
    return {"access_token": access_token, "token_type": "bearer"}


def oauth_login(
    user_credentials: dict,
    db: Session,
):
    try:
        user = repository.get_user(db, user_id=None, email=user_credentials["email"])
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while retrieving a user"}',
        ) from None
    try:
        access_token = utils.create_access_token(
            data={"user_email": user.email, "user_id": user.id}
        )
    except CreateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while creating a token"}',
        ) from None
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
    try:
        oauth_check = repository.get_user(db, user_id=None, email=user.email)
    except GetError:
        pass
    if checks.is_email_same(oauth_user, db) and oauth_check.is_oauth is True:
        data: dict = {"email": oauth_user.email, "password": oauth_user.password}
        access_token = oauth_login(data, db)
        return access_token
    try:
        new_oauth_user = repository.create_user(oauth_user, db)
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
    except CreateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while creating a user"}',
        ) from None
    user_data = dto_users.UpdateUserRestricted(is_verified=True, is_oauth=True)
    try:
        repository.update_user_restricted(new_oauth_user.id, user_data, db)
    except UpdateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while updating a user"}',
        ) from None
    return {"message": "login again to get access token"}
