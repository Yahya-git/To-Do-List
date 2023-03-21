from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str
    created_at: datetime
    updated_at: datetime


class UserUpdate(UserBase):
    password: str
    updated_at: datetime


class User(UserBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
