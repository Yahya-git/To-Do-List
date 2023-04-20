# Controller will call handler methods
# Handler will consume models and query methods
# Repository will contain query methods
# Controller -> Handler -> Repository


import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.dtos import dto_users
from src.exceptions import (
    CreateError,
    DeleteError,
    DuplicateEmailError,
    GetError,
    SendEmailError,
    UpdateError,
)
from src.handler import utils
from src.models.users import User
from src.repository import checks
from src.repository import users as repository


async def create_user(user_data: dto_users.CreateUserRequest, db: Session):
    try:
        user_data.password = utils.hash_password(user_data.password)
        user = User(**user_data.dict())
        new_user = repository.create_user(user, db)
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
    except CreateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while creating a user"}',
        ) from None
    try:
        token = repository.create_verification_token(new_user.id, db)
    except CreateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while creating a token"}',
        ) from None
    try:
        await utils.send_verification_mail(new_user, token.token)
    except SendEmailError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while sending an email"}',
        ) from None
    return new_user


async def update_user(
    id: int,
    user_data: dto_users.UpdateUserRequest,
    db: Session,
    current_user: int,
):
    if id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authorized to perform action",
        )
    if user_data.email:
        if checks.is_email_same(user_data, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'{"this email is already used"}',
            )
        try:
            token = repository.create_verification_token(id, db)
        except CreateError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'{"message: something went wrong while creating a token"}',
            ) from None
        try:
            await utils.send_verification_mail(user_data, token.token)
        except SendEmailError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'{"message: something went wrong while sending an email"}',
            ) from None
        user_restricted = User(is_verified=False)
        try:
            repository.update_user_restricted(id, user_restricted, db)
        except UpdateError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'{"message: something went wrong while updating a user"}',
            ) from None
    if user_data.password:
        user_data.password = utils.hash_password(user_data.password)
    try:
        user = User(**user_data.dict())
        updated_user = repository.update_user(id, user, db)
    except UpdateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while updating a user"}',
        ) from None
    return updated_user


def verify_email(token: int, db: Session):
    if checks.false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired verification token",
        )
    try:
        token_data = repository.delete_verification_token(token, db)
    except DeleteError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while deleting a token"}',
        ) from None
    user_data = dto_users.UpdateUserRestricted(is_verified=True)
    try:
        repository.update_user_restricted(token_data.user_id, user_data, db)
    except UpdateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while updating a user"}',
        ) from None
    return {"message": "email verified"}


async def reset_password_request(id: int, db: Session):
    try:
        user = repository.get_user(db, user_id=id, email=None)
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        ) from None
    if user.is_verified is False:
        try:
            token = repository.create_verification_token(user.id, db)
        except CreateError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'{"message: something went wrong while creating a token"}',
            ) from None
        try:
            await utils.send_verification_mail(user, token.token)
        except SendEmailError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'{"message: something went wrong while sending an email"}',
            ) from None
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to reset password, verification email has been sent"}',
        )
    if user.is_oauth is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"change your google account password instead"}',
        )
    try:
        token = repository.create_verification_token(user.id, db)
    except CreateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while creating a token"}',
        ) from None
    try:
        await utils.send_reset_password_mail(user, token.token)
    except SendEmailError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while sending an email"}',
        ) from None
    return {"message": "check your email to proceed further"}


def reset_password(id: int, token: int, db: Session):
    if checks.false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired verification token",
        )
    try:
        repository.delete_verification_token(token, db)
    except DeleteError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while deleting a token"}',
        ) from None
    password = "".join(
        secrets.choice(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_-+={}[]|;:<>,.?/~`"
        )
        for i in range(8)
    )
    user_data = dto_users.UpdateUserRequest(password=utils.hash_password(password))
    try:
        repository.update_user(id, user_data, db)
    except UpdateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while updating a user"}',
        ) from None
    return {
        "message": f"password successfully reset, use this temporary password to login and change your password: {password}"
    }
