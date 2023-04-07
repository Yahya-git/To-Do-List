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
from src.models import users
from src.repository.database_operations import (
    create_new_token,
    create_new_user,
    delete_used_token,
    update_in_database,
    verify_user,
)

from ..handler.checks import false_token, is_email_same
from ..handler.utils import (
    hash_password,
    send_reset_password_mail,
    send_verification_mail,
    validate_user,
)

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


async def create_user_handler(
    user: dto_users.CreateUserRequest, db: Session = get_db_session
):
    try:
        new_user = create_new_user(user, db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None
    try:
        token = create_new_token(new_user, db)
    except IntegrityError as e:
        print(f"Caught an exception while creating a token: {e}")
    try:
        await send_verification_mail(new_user, token)
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
    user_query = db.query(users.User).filter(users.User.id == id)
    to_update_user = user_query.first()
    if user.email:
        if is_email_same(user, db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'{"the new email address cannot be the same as the current email address"}',
            )
        to_update_user.is_verified = False
        try:
            token = create_new_token(to_update_user, db)
        except IntegrityError as e:
            print(f"Caught an exception while creating a token: {e}")
        try:
            await send_verification_mail(user, token)
        except ConnectionErrors as e:
            print(f"Caught an exception while sending the email: {e}")
    if user.password:
        password = hash_password(user.password)
        user.password = password
    try:
        user_query.update(user.dict(exclude_unset=True), synchronize_session=False)
        update_in_database(to_update_user, db)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        ) from None
    return to_update_user


def verify_email_handler(token: int, db: Session = get_db_session):
    if false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expired verification token",
        )
    try:
        user_id = delete_used_token(token, db)
    except IntegrityError as e:
        print(f"Caught an exception while deleting a token: {e}")
    try:
        verify_user(user_id, db)
    except IntegrityError as e:
        print(f"Caught an exception while verifying a user: {e}")
    return {"message": "email verified"}


async def reset_password_request_handler(
    id: int, db: Session = get_db_session, current_user: int = validate_user
):
    if id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authorized to perform action",
        )
    user = db.query(users.User).filter(users.User.id == id).first()
    if user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to reset password"}',
        )
    try:
        token = create_new_token(user, db)
    except IntegrityError as e:
        print(f"Caught an exception while creating a token: {e}")
    try:
        await send_reset_password_mail(user, token)
    except ConnectionErrors as e:
        print(f"Caught an exception while sending the email: {e}")
    return {"message": "check your email to proceed further"}


def reset_password_handler(id: int, token: int, db: Session = get_db_session):
    if false_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expired verification token",
        )
    user = db.query(users.User).filter(users.User.id == id).first()
    password = "".join(
        secrets.choice(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_-+={}[]|;:<>,.?/~`"
        )
        for i in range(8)
    )
    hashed_password = hash_password(password)
    user.password = hashed_password
    update_in_database(user, db)
    delete_used_token(token, db)
    return {
        "message": f"password successfully reset, use this temporary password to login and change your password: {password}"
    }
