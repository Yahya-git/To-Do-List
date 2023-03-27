from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    is_completed: bool = False


class TaskCreate(TaskBase):
    description: Optional[str]
    due_date: Optional[datetime]


class TaskUpdate(TaskBase):
    title: Optional[str]
    description: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    is_completed: Optional[bool] = False


class Task(TaskBase):
    id: int
    user_id: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    file_attachment: Optional[bytes]

    class Config:
        orm_mode = True
