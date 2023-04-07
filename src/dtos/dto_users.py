from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]


class CreateUserRequest(UserBase):
    password: str


class UpdateUserRequest(UserBase):
    email: Optional[EmailStr]
    password: Optional[str]


class UpdateUserRestricted(BaseModel):
    is_verified: Optional[bool]
    is_oauth: Optional[bool]


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
