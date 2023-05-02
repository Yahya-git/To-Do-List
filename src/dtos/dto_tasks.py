from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    is_completed: bool = False


class CreateTaskRequest(TaskBase):
    description: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    is_completed: Optional[bool] = False


class UpdateTaskRequest(TaskBase):
    title: Optional[str]
    description: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    is_completed: Optional[bool] = False


class TaskResponse(TaskBase):
    id: int
    user_id: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class SimilarTaskResponse(BaseModel):
    title: str
    description: Optional[str]
    count: int

    class Config:
        orm_mode = True
