from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from src.config import settings
from src.dtos.dto_tasks import CreateTaskRequest, UpdateTaskRequest
from src.models.tasks import Attachment, Task


def create_task(id, task_data: CreateTaskRequest, db: Session):
    task = Task(user_id=id, **task_data.dict())
    db.add(task)
    db.commit()
    return task


def update_task(task_id: int, task_data: UpdateTaskRequest, db: Session, user_id: int):
    query = (
        Task.__table__.update()
        .returning("*")
        .where(Task.__table__.c.id == task_id, Task.__table__.c.user_id == user_id)
        .values(
            title=coalesce(task_data.title, Task.__table__.c.title),
            description=coalesce(task_data.description, Task.__table__.c.description),
            due_date=coalesce(task_data.due_date, Task.__table__.c.due_date),
            is_completed=coalesce(
                task_data.is_completed, Task.__table__.c.is_completed
            ),
            completed_at=task_data.completed_at,
        )
    )
    updated_task = db.execute(query).fetchone()
    db.commit()
    return updated_task


def delete_task(task_id: int, db: Session, user_id: int):
    query = (
        Task.__table__.delete()
        .returning("*")
        .where(Task.__table__.c.id == task_id, Task.__table__.c.user_id == user_id)
    )
    deleted_task = db.execute(query).fetchone()
    db.commit()
    return deleted_task


def get_task(task_id: int, db: Session, user_id):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    return task


def get_tasks(
    user_id: int,
    db: Session,
    search: Optional[str] = "",
    sort: Optional[str] = "due_date",
):
    sort_attr = getattr(Task, sort)
    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.title.contains(search),
        )
        .order_by(sort_attr)
        .all()
    )
    return tasks


def get_max_tasks(id: int, db: Session):
    max_tasks = (
        db.query(Task.user_id)
        .filter(Task.user_id == id)
        .group_by(Task.user_id)
        .having(func.count(Task.user_id) == settings.max_tasks)
        .first()
    )
    return max_tasks


def create_file(task_id: int, file_name: str, file_data: bytes, db: Session):
    attachment = Attachment(
        task_id=task_id, file_attachment=file_data, file_name=file_name
    )
    db.add(attachment)
    db.commit()
    return attachment


def get_file(file_id: int, task_id: int, db: Session):
    file = (
        db.query(Attachment)
        .filter(Attachment.id == file_id, Attachment.task_id == task_id)
        .first()
    )
    return file
