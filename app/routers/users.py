from datetime import datetime, timedelta
from random import randint
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import oauth2

from .. import schemas_users, utils
from ..config import settings
from ..database import models
from ..database.database import get_db
from ..email import send_mail

local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)


router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas_users.User
)
# trunk-ignore(ruff/B008)
async def create_user(user: schemas_users.UserCreate, db: Session = Depends(get_db)):
    usercheck = db.query(models.User).filter(models.User.email == user.email).first()
    if usercheck:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        )
    else:
        password = utils.hash(user.password)
        user.password = password
        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    token = randint(100000, 999999)
    verification_token = models.Verification(
        user_id=new_user.id,
        token=token,
        expires_at=datetime.now() + timedelta(hours=24),
    )

    db.add(verification_token)
    db.commit()
    db.refresh(verification_token)

    verification_url = f"{settings.url}/users/verify-email?token={token}"
    await send_mail(
        email=user.email,
        link=verification_url,
        subject_template="Verify Email",
        template=f"Click the following link to verify your email: {verification_url}",
    )

    return new_user


@router.patch(
    "/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_users.User
)
async def update_user(
    id: int,
    user: schemas_users.UserUpdate,
    # trunk-ignore(ruff/B008)
    db: Session = Depends(get_db),
):
    user_query = db.query(models.User).filter(models.User.id == id)
    update_user = user_query.first()
    if not update_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        )
    else:
        update_data = {"updated_at": datetime.now()}
        if user.email:
            if user.email == update_user.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f'{"the new email address cannot be the same as the current email address"}',
                )
            update_data["email"] = user.email

            token = randint(100000, 999999)
            verification_token = models.Verification(
                user_id=update_user.id,
                token=token,
                expires_at=datetime.now() + timedelta(hours=24),
            )

            db.add(verification_token)
            db.commit()
            db.refresh(verification_token)

            verification_url = f"{settings.url}/users/verify-email?token={token}"
            await send_mail(
                email=user.email,
                link=verification_url,
                subject_template="Verify Email",
                template=f"Click the following link to verify your email: {verification_url}",
            )

        if user.first_name:
            update_data["first_name"] = user.first_name
        if user.last_name:
            update_data["last_name"] = user.last_name
        if user.password:
            password = utils.hash(user.password)
            user.password = password
        user_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(update_user)
        return update_user


@router.get("/verify-email", status_code=status.HTTP_202_ACCEPTED)
# trunk-ignore(ruff/B008)
def verify_email(token: int, db: Session = Depends(get_db)):
    verification_token = (
        db.query(models.Verification).filter(models.Verification.token == token).first()
    )
    if not verification_token or verification_token.expires_at < now_local:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expired verification token",
        )
    else:
        user = (
            db.query(models.User)
            .filter(models.User.id == verification_token.user_id)
            .first()
        )
        user.is_verified = True
        db.delete(verification_token)
        db.commit()
        db.refresh(user)
    return {"message": "email verified"}


@router.post("/login")
def login(
    # trunk-ignore(ruff/B008)
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    # trunk-ignore(ruff/B008)
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.email == user_credentials.username)
        .first()
    )
    if user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to login"}',
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}
