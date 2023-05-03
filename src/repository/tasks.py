from datetime import date
from typing import Optional

from sqlalchemy import Date, cast, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from src.config import settings
from src.exceptions import (
    CreateError,
    DeleteError,
    GetError,
    MaxTasksReachedError,
    UpdateError,
)
from src.models.tasks import Attachment, Task
from src.repository import checks


def create_task(id, task: Task, db: Session):
    if checks.max_tasks_reached(db, id):
        raise MaxTasksReachedError
    try:
        query = (
            Task.__table__.insert()
            .returning("*")
            .values(
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                is_completed=task.is_completed,
                completed_at=task.completed_at,
                user_id=task.user_id,
            )
        )
        new_task = db.execute(query).fetchone()
        db.commit()
        return new_task
    except SQLAlchemyError as e:
        print(f"Exception: {e}")
        raise CreateError from e


def update_task(task_id: int, task: Task, db: Session, user_id: int):
    query = (
        Task.__table__.update()
        .returning("*")
        .where(Task.__table__.c.id == task_id, Task.__table__.c.user_id == user_id)
        .values(
            title=coalesce(task.title, Task.__table__.c.title),
            description=coalesce(task.description, Task.__table__.c.description),
            due_date=coalesce(task.due_date, Task.__table__.c.due_date),
            is_completed=coalesce(task.is_completed, Task.__table__.c.is_completed),
            completed_at=task.completed_at,
        )
    )
    updated_task = db.execute(query).fetchone()
    db.commit()
    if not updated_task:
        raise UpdateError
    return updated_task


def delete_task(task_id: int, db: Session, user_id: int):
    query = (
        Task.__table__.delete()
        .returning("*")
        .where(Task.__table__.c.id == task_id, Task.__table__.c.user_id == user_id)
    )
    deleted_task = db.execute(query).fetchone()
    db.commit()
    if not deleted_task:
        raise DeleteError
    return deleted_task


def get_task(task_id: int, db: Session, user_id):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise GetError
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
    if not tasks:
        raise GetError
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


def get_similar_tasks(user_id: int, db: Session):
    similar_tasks = (
        db.query(Task.title, Task.description, func.count("*").label("count"))
        .filter(Task.user_id == user_id)
        .group_by(Task.title, Task.description)
        .having(func.count("*") > 1)
    ).all()
    if not similar_tasks:
        raise GetError
    return similar_tasks


def all_tasks_due_today(db: Session):
    all_tasks_due_today = (
        db.query(Task).filter(cast(Task.due_date, Date) == date.today()).all()
    )
    return all_tasks_due_today


def tasks_due_today(db: Session, user_id: int):
    user_tasks_due_today = (
        db.query(Task)
        .filter(
            cast(Task.due_date, Date) == date.today(),
            Task.user_id == user_id,
        )
        .all()
    )
    return user_tasks_due_today


def create_file(task_id: int, file_name: str, file_data: bytes, db: Session):
    attachment = Attachment(
        task_id=task_id, file_attachment=file_data, file_name=file_name
    )
    query = (
        Attachment.__table__.insert()
        .returning("*")
        .values(
            task_id=attachment.task_id,
            file_attachment=attachment.file_attachment,
            file_name=attachment.file_name,
        )
    )
    new_file = db.execute(query).fetchone()
    db.commit()
    return new_file


def get_file(file_id: int, task_id: int, db: Session):
    file = (
        db.query(Attachment)
        .filter(Attachment.id == file_id, Attachment.task_id == task_id)
        .first()
    )
    if not file:
        raise FileNotFoundError
    return file
