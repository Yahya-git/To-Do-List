from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_misc
from src.handler.auth import (
    callback_google_handler,
    login_google_handler,
    login_handler,
)

router = APIRouter(tags=["Auth"])

get_db_session = Depends(get_db)
Depend = Depends()


# User Login Endpoint
@router.post(
    "/login",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dto_misc.TokenResponse,
)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depend,
    db: Session = get_db_session,
):
    return await login_handler(user_credentials, db)


# User Google Login Endpoint
@router.get("/login/oauth")
async def login_google():
    return await login_google_handler()


@router.get("/login/google/callback", status_code=status.HTTP_202_ACCEPTED)
async def callback_google(request: Request, db: Session = get_db_session):
    return await callback_google_handler(request, db)
