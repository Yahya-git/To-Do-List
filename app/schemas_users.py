from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    # id: int
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]


class UserCreate(UserBase):
    password: str
    # created_at: datetime
    # updated_at: datetime


class UserUpdate(UserBase):
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    password: Optional[str]
    updated_at: Optional[datetime]


class User(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
