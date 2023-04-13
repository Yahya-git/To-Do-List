# Controller will call handler methods
# Handler will consume models and query methods
# Repository will contain query methods
# Controller -> Handler -> Repository


import secrets

from fastapi import HTTPException, status
from fastapi_mail.errors import ConnectionErrors
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.dtos import dto_users
from src.handler import utils
from src.repository import checks
from src.repository import users as repository


async def create_user(user: dto_users.CreateUserRequest, db: Session):
    try:
        new_user = repository.create_user(user, db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
    try:
        token = repository.create_verification_token(new_user.id, db)
    except IntegrityError as e:
        print(f"Caught an exception while creating a token: {e}")
    try:
        await utils.send_verification_mail(new_user, token.token)
    except ConnectionErrors as e:
        print(f"Caught an exception while sending the email: {e}")
    return new_user


async def update_user(
    id: int,
    user: dto_users.UpdateUserRequest,
    db: Session,
    current_user: int,
):
    if id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authorized to perform action",
        )
    if user.email:
        if checks.is_email_same(user, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'{"the new email address cannot be the same as the current email address"}',
            )
        user_restricted = dto_users.UpdateUserRestricted(is_verified=False)
        repository.update_user_restricted(id, user_restricted, db)
        try:
            token = repository.create_verification_token(id, db)
        except IntegrityError as e:
            print(f"Caught an exception while creating a token: {e}")
        try:
            await utils.send_verification_mail(user, token.token)
        except ConnectionErrors as e:
            print(f"Caught an exception while sending the email: {e}")
    if user.password:
        user.password = utils.hash_password(user.password)
    updated_user = repository.update_user(id, user, db)
    return updated_user


def verify_email(token: int, db: Session):
    if checks.false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired verification token",
        )
    try:
        token_data = repository.delete_verification_token(token, db)
    except IntegrityError as e:
        print(f"Caught an exception while deleting a token: {e}")
    try:
        user_data = dto_users.UpdateUserRestricted(is_verified=True)
        repository.update_user_restricted(token_data.user_id, user_data, db)
    except IntegrityError as e:
        print(f"Caught an exception while verifying a user: {e}")
    return {"message": "email verified"}


async def reset_password_request(id: int, db: Session):
    user = repository.get_user(id, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        )
    if user.is_verified is False:
        token = repository.create_verification_token(user.id, db)
        await utils.send_verification_mail(user, token.token)
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
    except IntegrityError as e:
        print(f"Caught an exception while creating a token: {e}")
    try:
        await utils.send_reset_password_mail(user, token.token)
    except ConnectionErrors as e:
        print(f"Caught an exception while sending the email: {e}")
    return {"message": "check your email to proceed further"}


def reset_password(id: int, token: int, db: Session):
    if checks.false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired verification token",
        )
    repository.delete_verification_token(token, db)
    password = "".join(
        secrets.choice(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_-+={}[]|;:<>,.?/~`"
        )
        for i in range(8)
    )
    user_data = dto_users.UpdateUserRequest(password=utils.hash_password(password))
    repository.update_user(id, user_data, db)
    return {
        "message": f"password successfully reset, use this temporary password to login and change your password: {password}"
    }
