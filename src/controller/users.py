from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_users
from src.handler.users import (
    create_user_handler,
    reset_password_handler,
    reset_password_request_handler,
    update_user_handler,
    verify_email_handler,
)
from src.handler.utils import validate_user

router = APIRouter(prefix="/users", tags=["Users"])

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


# User Registration Endpoint
@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=dto_users.UserResponse
)
async def create_user(user: dto_users.CreateUserRequest, db: Session = get_db_session):
    return await create_user_handler(user, db)


# User Updation Endpoint
@router.put(
    "/{id}", status_code=status.HTTP_200_OK, response_model=dto_users.UserResponse
)
async def update_user(
    id: int,
    user: dto_users.UpdateUserRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    return await update_user_handler(id, user, db, current_user)


# User Email Verification Endpoint
@router.get("/verify-email", status_code=status.HTTP_202_ACCEPTED)
def verify_email(token: int, db: Session = get_db_session):
    return verify_email_handler(token, db)


# User Password Reset Request Endpoint
@router.get("/{id}/reset-password-request", status_code=status.HTTP_201_CREATED)
async def reset_password_request(
    id: int, db: Session = get_db_session, current_user: int = validated_user
):
    return await reset_password_request_handler(id, db, current_user)


# User Password Reset Endpoint
@router.get("/{id}/reset-password", status_code=status.HTTP_202_ACCEPTED)
def reset_password(id: int, token: int, db: Session = get_db_session):
    return reset_password_handler(id, token, db)
