from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_misc, dto_users
from src.handler import users as handler
from src.handler.utils import validate_user

router = APIRouter(prefix="/users", tags=["Users"])

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


# User Registration Endpoint
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=dto_misc.UserSingleResponse[dto_users.UserResponse],
)
async def create_user(
    user_data: dto_users.CreateUserRequest, db: Session = get_db_session
):
    user = await handler.create_user(user_data, db)
    return {"status": "registration complete", "data": {"user": user}}


# User Updation Endpoint
@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=dto_misc.UserSingleResponse[dto_users.UserResponse],
)
async def update_user(
    id: int,
    user_data: dto_users.UpdateUserRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    user = await handler.update_user(id, user_data, db, current_user)
    return {"status": "successfully updated user data", "data": {"user": user}}


# User Email Verification Endpoint
@router.get("/verify-email", status_code=status.HTTP_202_ACCEPTED)
def verify_email(token: int, db: Session = get_db_session):
    return handler.verify_email(token, db)


# User Password Reset Request Endpoint
@router.get("/{id}/reset-password-request", status_code=status.HTTP_201_CREATED)
async def reset_password_request(id: int, db: Session = get_db_session):
    return await handler.reset_password_request(id, db)


# User Password Reset Endpoint
@router.get("/{id}/reset-password", status_code=status.HTTP_202_ACCEPTED)
def reset_password(id: int, token: int, db: Session = get_db_session):
    return handler.reset_password(id, token, db)
