from datetime import datetime
from typing import Optional

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


class TaskBase(BaseModel):
    id: int
    title: str
    status: bool = False
    user_id: int


class TaskCreate(TaskBase):
    description: str
    created_at: datetime
    updated_at: datetime
    due_date: datetime


class TaskUpdate(TaskBase):
    description: str
    updated_at: datetime
    due_date: datetime
    completed_at: datetime
    status: bool


class Task(TaskBase):
    description: str
    created_at: datetime
    updated_at: datetime
    due_date: datetime
    completed_at: datetime

    class Config:
        orm_mode = True


class AttachmentBase(BaseModel):
    id: int
    file_attachment: Optional[bytes] = None


class AttachmentCreate(AttachmentBase):
    task_id: int


class Attachment(AttachmentBase):
    task_id: int

    class Config:
        orm_mode = True
