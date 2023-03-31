import secrets
from datetime import datetime, timedelta
from random import randint
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import utils
from app.config import settings
from app.schemas import schemas_users

from ..database.database import get_db
from ..database.models import users

local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)


router = APIRouter(prefix="/users", tags=["Users"])

get_db_session = Depends(get_db)
get_current_user = Depends(utils.get_current_user)


# Check Conditions
def check_email(user: schemas_users.User, db: Session = get_db_session):
    usercheck = db.query(users.User).filter(users.User.email == user.email).first()
    if usercheck:
        return True


def is_email_same(user: schemas_users.User, db: Session = get_db_session):
    usercheck = db.query(users.User).filter(users.User.email == user.email).first()
    if usercheck:
        return True


def user_exists(id: int, db: Session = get_db_session):
    usercheck = db.query(users.User).filter(users.User.id == id).first()
    if usercheck:
        return True


def check_token(token: int, db: Session = get_db_session):
    verification_token = (
        db.query(users.Verification).filter(users.Verification.token == token).first()
    )
    if not verification_token or verification_token.expires_at < now_local:
        return False


def create_new_user(user: schemas_users.UserCreate, db: Session = get_db_session):
    password = utils.hash(user.password)
    user.password = password
    new_user = users.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def create_new_token(user: schemas_users.User, db: Session = get_db_session):
    try:
        verification_token = (
            db.query(users.Verification)
            .filter(users.Verification.user_id == user.id)
            .first()
        )
        if verification_token:
            db.delete(verification_token)
            db.commit()
        token = randint(100000, 999999)
        verification_token = users.Verification(
            user_id=user.id,
            token=token,
            expires_at=datetime.now() + timedelta(hours=24),
        )
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)
        return token
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while creating a token"}',
        ) from None


def delete_used_token(token: int, db: Session = get_db_session):
    try:
        verification_token = (
            db.query(users.Verification)
            .filter(users.Verification.token == token)
            .first()
        )
        user = (
            db.query(users.User)
            .filter(users.User.id == verification_token.user_id)
            .first()
        )
        user.is_verified = True
        db.delete(verification_token)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while deleting a token"}',
        ) from None


async def send_verification_mail(user: schemas_users.User, token: int):
    try:
        verification_url = f"{settings.url}/users/verify-email?token={token}"
        await utils.send_mail(
            email=user.email,
            link=verification_url,
            subject_template="Verify Email",
            template=f"Click the following link to verify your email: {verification_url}",
        )
    except Exception as e:
        print(f"something went wrong while sending the verification email: {e}")


async def send_reset_mail(user: schemas_users.User, token: int):
    try:
        reset_password_url = (
            f"{settings.url}/users/{user.id}/reset-password?token={token}"
        )
        await utils.send_mail(
            email=user.email,
            link=reset_password_url,
            subject_template="Reset Password",
            template=f"Click the following link to reset your password: {reset_password_url}",
        )
    except Exception as e:
        print(f"something went wrong while sending the reset email: {e}")


# User Registration Endpoint
@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas_users.User
)
async def create_user(user: schemas_users.UserCreate, db: Session = get_db_session):
    try:
        new_user = create_new_user(user, db)
        token = create_new_token(new_user, db)
        await send_verification_mail(new_user, token)
        return new_user
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        ) from None


# User Updation Endpoint
@router.patch(
    "/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_users.User
)
async def update_user(
    id: int,
    user: schemas_users.UserUpdate,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    if id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authorized to perform action",
        )
    if not user_exists(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
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
        token = create_new_token(to_update_user, db)
        await send_verification_mail(user, token)
    if user.password:
        password = utils.hash(user.password)
        user.password = password
    user_query.update(user.dict(exclude_unset=True), synchronize_session=False)
    db.commit()
    db.refresh(to_update_user)
    return to_update_user


# User Email Verification Endpoint
@router.get("/verify-email", status_code=status.HTTP_202_ACCEPTED)
def verify_email(token: int, db: Session = get_db_session):
    if not check_token(token, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expired verification token",
        )
    delete_used_token(token, db)
    return {"message": "email verified"}


# User Password Reset Request Endpoint
@router.get("/{id}/reset-password-request", status_code=status.HTTP_201_CREATED)
async def reset_password_request(
    id: int, db: Session = get_db_session, current_user: int = get_current_user
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
    token = create_new_token(user, db)
    await send_reset_mail(user, token)
    return {"message": "check your email to proceed further"}


# User Password Reset Endpoint
@router.get("/{id}/reset-password", status_code=status.HTTP_202_ACCEPTED)
def reset_password(id: int, token: int, db: Session = get_db_session):
    if not check_token(token, db):
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
    db.commit()
    db.refresh(user)
    delete_used_token(token, db)
    return {
        "message": f"password successfully reset, use this temporary password to login and change your password: {password}"
    }
