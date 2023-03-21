from datetime import datetime

from pydantic import BaseModel


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
