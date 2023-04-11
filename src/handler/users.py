# Controller will call handler methods
# Handler will consume models and query methods
# Repository will contain query methods
# Controller -> Handler -> Repository


import secrets

from fastapi import Depends, HTTPException, status
from fastapi_mail.errors import ConnectionErrors
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_users
from src.handler.checks import does_user_exist, false_token, is_email_same
from src.handler.utils import (
    hash_password,
    send_reset_password_mail,
    send_verification_mail,
    validate_user,
)
from src.repository.database_queries import (
    create_user,
    create_verification_token_by_user_id,
    delete_verification_token,
    get_user_by_id,
    update_user_by_id,
    update_user_by_id_restricted,
)

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


async def create_user_handler(
    user: dto_users.CreateUserRequest, db: Session = get_db_session
):
    try:
        new_user = create_user(user, db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
    try:
        token = create_verification_token_by_user_id(new_user.id, db)
    except IntegrityError as e:
        print(f"Caught an exception while creating a token: {e}")
    try:
        await send_verification_mail(new_user, token.token)
    except ConnectionErrors as e:
        print(f"Caught an exception while sending the email: {e}")
    return new_user


async def update_user_handler(
    id: int,
    user: dto_users.UpdateUserRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    if id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authorized to perform action",
        )
    try:
        to_update_user = get_user_by_id(id, db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        ) from None
    if user.email:
        if is_email_same(user, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'{"the new email address cannot be the same as the current email address"}',
            )
        to_update_user.is_verified = False
        try:
            token = create_verification_token_by_user_id(to_update_user.id, db)
        except IntegrityError as e:
            print(f"Caught an exception while creating a token: {e}")
        try:
            await send_verification_mail(user, token.token)
        except ConnectionErrors as e:
            print(f"Caught an exception while sending the email: {e}")
    if user.password:
        user.password = hash_password(user.password)
    update_user_by_id(id, user, db)
    return to_update_user


def verify_email_handler(token: int, db: Session = get_db_session):
    if false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired verification token",
        )
    try:
        token_data = delete_verification_token(token, db)
    except IntegrityError as e:
        print(f"Caught an exception while deleting a token: {e}")
    try:
        user_data = dto_users.UpdateUserRestricted(is_verified=True)
        update_user_by_id_restricted(token_data.user_id, user_data, db)
    except IntegrityError as e:
        print(f"Caught an exception while verifying a user: {e}")
    return {"message": "email verified"}


async def reset_password_request_handler(id: int, db: Session = get_db_session):
    if not does_user_exist(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        ) from None
    user = get_user_by_id(id, db)
    if user.is_verified is False:
        token = create_verification_token_by_user_id(user.id, db)
        await send_verification_mail(user, token.token)
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to reset password"}',
        )
    if user.is_oauth is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"change your google account password instead"}',
        )
    try:
        token = create_verification_token_by_user_id(user.id, db)
    except IntegrityError as e:
        print(f"Caught an exception while creating a token: {e}")
    try:
        await send_reset_password_mail(user, token.token)
    except ConnectionErrors as e:
        print(f"Caught an exception while sending the email: {e}")
    return {"message": "check your email to proceed further"}


def reset_password_handler(id: int, token: int, db: Session = get_db_session):
    if false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired verification token",
        )
    token_data = delete_verification_token(token, db)
    if token_data.user_id == id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="id and user id from token mismatch",
        )
    password = "".join(
        secrets.choice(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_-+={}[]|;:<>,.?/~`"
        )
        for i in range(8)
    )
    user_data = dto_users.UpdateUserRequest(password=hash_password(password))
    update_user_by_id(token_data.user_id, user_data, db)
    return {
        "message": f"password successfully reset, use this temporary password to login and change your password: {password}"
    }
