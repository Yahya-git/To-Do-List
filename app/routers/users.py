from datetime import datetime, timedelta
from random import randint
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import utils
from app.config import settings
from app.schemas import schemas_misc, schemas_users

from ..database import models
from ..database.database import get_db

local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)


router = APIRouter(prefix="/users", tags=["Users"])


# check conditions
# trunk-ignore(ruff/B008)
def check_user_email(user: schemas_users.User, db: Session = Depends(get_db)):
    usercheck = db.query(models.User).filter(models.User.email == user.email).first()
    if usercheck:
        return True


# trunk-ignore(ruff/B008)
def is_email_same(user: schemas_users.User, db: Session = Depends(get_db)):
    usercheck = db.query(models.User).filter(models.User.email == user.email).first()
    if usercheck:
        return True


# trunk-ignore(ruff/B008)
def check_user_id(id: int, db: Session = Depends(get_db)):
    usercheck = db.query(models.User).filter(models.User.id == id).first()
    if not usercheck:
        return True


# trunk-ignore(ruff/B008)
def check_token(token: int, db: Session = Depends(get_db)):
    verification_token = (
        db.query(models.Verification).filter(models.Verification.token == token).first()
    )
    if not verification_token or verification_token.expires_at < now_local:
        return True


# trunk-ignore(ruff/B008)
def create_new_user(user: schemas_users.UserCreate, db: Session = Depends(get_db)):
    password = utils.hash(user.password)
    user.password = password
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# trunk-ignore(ruff/B008)
def create_new_token(user: schemas_users.User, db: Session = Depends(get_db)):
    token = randint(100000, 999999)
    verification_token = models.Verification(
        user_id=user.id,
        token=token,
        expires_at=datetime.now() + timedelta(hours=24),
    )
    db.add(verification_token)
    db.commit()
    db.refresh(verification_token)
    return token


# trunk-ignore(ruff/B008)
def delete_used_token(token: int, db: Session = Depends(get_db)):
    verification_token = (
        db.query(models.Verification).filter(models.Verification.token == token).first()
    )
    user = (
        db.query(models.User)
        .filter(models.User.id == verification_token.user_id)
        .first()
    )
    user.is_verified = True
    db.delete(verification_token)
    db.commit()
    db.refresh(user)


async def send_verification_mail(user: schemas_users.User, token: int):
    verification_url = f"{settings.url}/users/verify-email?token={token}"
    await utils.send_mail(
        email=user.email,
        link=verification_url,
        subject_template="Verify Email",
        template=f"Click the following link to verify your email: {verification_url}",
    )


# User Registration Endpoint
@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas_users.User
)
# trunk-ignore(ruff/B008)
async def create_user(user: schemas_users.UserCreate, db: Session = Depends(get_db)):
    if check_user_email(user, db=db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        )
    new_user = create_new_user(user, db=db)
    token = create_new_token(new_user, db=db)
    await send_verification_mail(new_user, token)
    return new_user


# User Updation Endpoint
@router.patch(
    "/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_users.User
)
async def update_user(
    id: int,
    user: schemas_users.UserUpdate,
    # trunk-ignore(ruff/B008)
    db: Session = Depends(get_db),
):
    if check_user_id(id=id, db=db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        )
    user_query = db.query(models.User).filter(models.User.id == id)
    to_update_user = user_query.first()
    if user.email:
        if is_email_same(user, db=db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'{"the new email address cannot be the same as the current email address"}',
            )
        to_update_user.is_verified = False
        token = create_new_token(to_update_user, db=db)
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
# trunk-ignore(ruff/B008)
def verify_email(token: int, db: Session = Depends(get_db)):
    if check_token(token, db=db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid or expired verification token",
        )
    delete_used_token(token, db=db)
    return {"message": "email verified"}


# User Login Endpoint
@router.post(
    "/login", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_misc.Token
)
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
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    if user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to login"}',
        )
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    access_token = utils.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


def login_app_google(
    user_credentials: dict,
    # trunk-ignore(ruff/B008)
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.email == user_credentials["email"])
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    if user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f'{"kindly verify your email before trying to login"}',
        )
    if not utils.verify(user_credentials["password"], user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f'{"invalid credentials"}'
        )
    access_token = utils.create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# User Google Login Endpoint
@router.get("/google/login")
async def login_google():
    return await utils.google_sso.get_login_redirect()


@router.get("/google/callback", status_code=status.HTTP_202_ACCEPTED)
# trunk-ignore(ruff/B008)
async def callback_google(request: Request, db: Session = Depends(get_db)):
    user = await utils.google_sso.verify_and_process(request)
    user_data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user.id,
    }
    oauth_user = schemas_users.UserCreate(**user_data)
    oauth_check = (
        db.query(models.User).filter(models.User.email == oauth_user.email).first()
    )
    if check_user_email(oauth_user, db=db) and oauth_check.is_oauth is True:
        data: dict = {"email": oauth_user.email, "password": oauth_user.password}
        access_token = login_app_google(user_credentials=data, db=db)
        return access_token
    if check_user_email(oauth_user, db=db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        )
    new_oauth_user = create_new_user(oauth_user, db=db)
    new_oauth_user.is_verified = True
    new_oauth_user.is_oauth = True
    db.commit()
    return {"message": "login again to get access token"}
