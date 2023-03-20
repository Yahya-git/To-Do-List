from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    # id: int
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]


class UserCreate(BaseModel):
    password: str
    # created_at: datetime
    # updated_at: datetime


class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    password: Optional[str]
    updated_at: Optional[datetime]


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
