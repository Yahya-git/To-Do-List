import secrets
from datetime import datetime, timedelta
from random import randint
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_mail.errors import ConnectionErrors
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.config import settings
from src.dtos import dto_users
from src.handler import utils

from ..database import get_db
from ..models import users

local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)

router = APIRouter(prefix="/users", tags=["Users"])

get_db_session = Depends(get_db)
validate_user = Depends(utils.validate_user)


# Check Conditions
def is_email_same(user: dto_users.UserResponse, db: Session = get_db_session):
    usercheck = db.query(users.User).filter(users.User.email == user.email).first()
    if usercheck:
        return True


def does_user_exist(id: int, db: Session = get_db_session):
    usercheck = db.query(users.User).filter(users.User.id == id).first()
    if usercheck:
        return True


def false_token(token: int, db: Session = get_db_session):
    verification_token = (
        db.query(users.Verification).filter(users.Verification.token == token).first()
    )
    if not verification_token or verification_token.expires_at < now_local:
        return True


def add_to_database(record, db: Session = get_db_session):
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_from_database(record, db: Session = get_db_session):
    db.delete(record)
    db.commit()


def update_in_database(record, db: Session = get_db_session):
    db.commit()
    db.refresh(record)


def create_new_user(user: dto_users.CreateUserRequest, db: Session = get_db_session):
    password = utils.hash(user.password)
    user.password = password
    new_user = users.User(**user.dict())
    add_to_database(new_user, db)
    return new_user


def create_new_token(user: dto_users.UserResponse, db: Session = get_db_session):
    verification_token = (
        db.query(users.Verification)
        .filter(users.Verification.user_id == user.id)
        .first()
    )
    if verification_token:
        delete_from_database(verification_token, db)
    token = randint(100000, 999999)
    verification_token = users.Verification(
        user_id=user.id,
        token=token,
        expires_at=datetime.now() + timedelta(hours=24),
    )
    add_to_database(verification_token, db)
    return token


def delete_used_token(token: int, db: Session = get_db_session):
    verification_token = (
        db.query(users.Verification).filter(users.Verification.token == token).first()
    )
    user_id = verification_token.user_id
    delete_from_database(verification_token, db)
    return user_id


def verify_user(user_id, db: Session = get_db_session):
    user = db.query(users.User).filter(users.User.id == user_id).first()
    user.is_verified = True
    update_in_database(user, db)


async def send_verification_mail(user: dto_users.UserResponse, token: int):
    verification_url = f"{settings.url}/users/verify-email?token={token}"
    await utils.send_mail(
        email=user.email,
        subject_template="Verify Email",
        template=f"Click the following link to verify your email: {verification_url}",
    )


async def send_reset_password_mail(user: dto_users.UserResponse, token: int):
    reset_password_url = f"{settings.url}/users/{user.id}/reset-password?token={token}"
    await utils.send_mail(
        email=user.email,
        subject_template="Reset Password",
        template=f"Click the following link to reset your password: {reset_password_url}",
    )


# User Registration Endpoint
@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=dto_users.UserResponse
)
async def create_user(user: dto_users.CreateUserRequest, db: Session = get_db_session):
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


# User Updation Endpoint
@router.put(
    "/{id}", status_code=status.HTTP_200_OK, response_model=dto_users.UserResponse
)
async def update_user(
    id: int,
    user: dto_users.UpdateUserRequest,
    db: Session = get_db_session,
    current_user: int = validate_user,
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
        password = utils.hash(user.password)
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


# User Email Verification Endpoint
@router.get("/verify-email", status_code=status.HTTP_202_ACCEPTED)
def verify_email(token: int, db: Session = get_db_session):
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


# User Password Reset Request Endpoint
@router.get("/{id}/reset-password-request", status_code=status.HTTP_201_CREATED)
async def reset_password_request(
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


# User Password Reset Endpoint
@router.get("/{id}/reset-password", status_code=status.HTTP_202_ACCEPTED)
def reset_password(id: int, token: int, db: Session = get_db_session):
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
    hashed_password = utils.hash(password)
    user.password = hashed_password
    update_in_database(user, db)
    delete_used_token(token, db)
    return {
        "message": f"password successfully reset, use this temporary password to login and change your password: {password}"
    }
