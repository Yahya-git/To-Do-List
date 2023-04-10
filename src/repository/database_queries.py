from datetime import datetime, timedelta
from random import randint
from typing import Optional

from fastapi import Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.dtos.dto_tasks import CreateTaskRequest, UpdateTaskRequest
from src.dtos.dto_users import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserRestricted,
)
from src.handler.utils import hash_password
from src.models.tasks import Attachment, Task
from src.models.users import User, Verification

get_db_session = Depends(get_db)


def create_user(user_data: CreateUserRequest, db: Session = get_db_session):
    user_data.password = hash_password(user_data.password)
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    return user


def update_user_by_id(
    user_id: int, user_data: UpdateUserRequest, db: Session = get_db_session
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .update(user_data.dict(exclude_unset=True), synchronize_session=False)
    )
    db.commit()
    return user


def update_user_by_id_restricted(
    user_id: int, user_data: UpdateUserRestricted, db: Session = get_db_session
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .update(user_data.dict(exclude_unset=True), synchronize_session=False)
    )
    db.commit()
    return user


def get_user_by_id(user_id: int, db: Session = get_db_session):
    user = db.query(User).filter(User.id == user_id).first()
    return user


def get_user_by_email(email: str, db: Session = get_db_session):
    user = db.query(User).filter(User.email == email).first()
    return user


def create_task_by_user_id(
    id, task_data: CreateTaskRequest, db: Session = get_db_session
):
    task = Task(user_id=id, **task_data.dict())
    db.add(task)
    db.commit()
    return task


def update_task_by_id(
    task_id: int, task_data: UpdateTaskRequest, db: Session = get_db_session
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id)
        .update(task_data.dict(exclude_unset=True), synchronize_session=False)
    )
    db.commit()
    return task


def delete_task_by_id(task_id: int, db: Session = get_db_session):
    db.query(Task).filter(Task.id == task_id).delete()
    db.commit()


def get_task_by_id(task_id: int, db: Session = get_db_session):
    task = db.query(Task).filter(Task.id == task_id).first()
    return task


def get_tasks_by_user_id(
    user_id: int,
    db: Session = get_db_session,
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


def get_max_tasks_by_user_id(id: int, db: Session = get_db_session):
    max_tasks = (
        db.query(Task.user_id)
        .filter(Task.user_id == id)
        .group_by(Task.user_id)
        .having(func.count(Task.user_id) == settings.max_tasks)
        .first()
    )
    return max_tasks


def create_verification_token_by_user_id(id: int, db: Session = get_db_session):
    token = get_verification_token_by_user_id(id, db)
    if token:
        delete_verification_token(token.token, db)
    token = randint(100000, 999999)
    verification_token = Verification(
        user_id=id,
        token=token,
        expires_at=datetime.now() + timedelta(hours=24),
    )
    db.add(verification_token)
    db.commit()
    return verification_token


def delete_verification_token(token: int, db: Session = get_db_session):
    token_data = db.query(Verification).filter(Verification.token == token).first()
    db.query(Verification).filter(Verification.token == token).delete()
    db.commit()
    return token_data


def get_verification_token(token: int, db: Session = get_db_session):
    verification_token = (
        db.query(Verification).filter(Verification.token == token).first()
    )
    return verification_token


def get_verification_token_by_user_id(id: int, db: Session = get_db_session):
    verification_token = (
        db.query(Verification).filter(Verification.user_id == id).first()
    )
    return verification_token


def get_file_by_file_and_task_id(
    file_id: int, task_id: int, db: Session = get_db_session
):
    file = (
        db.query(Attachment)
        .filter(Attachment.id == file_id, Attachment.task_id == task_id)
        .first()
    )
    return file


def get_count_of_tasks_by_user_id(id, db: Session = get_db_session):
    query = text(
        "SELECT COUNT(tasks.id) AS total_tasks, SUM(CASE WHEN tasks.is_completed = True THEN 1 ELSE 0 END) AS completed_tasks, SUM(CASE WHEN tasks.is_completed = False THEN 1 ELSE 0 END) AS incomplete_tasks FROM tasks WHERE tasks.user_id = :user_id;"
    )
    count = db.execute(query, {"user_id": id}).fetchone()
    return count


def get_average_tasks_by_user_id(id, db: Session = get_db_session):
    query = text(
        "SELECT AVG(completed_tasks / days_since_creation) as average_tasks_completed_per_day FROM ( SELECT COUNT(tasks.id) AS completed_tasks, DATE_PART('day', NOW() - users.created_at) AS days_since_creation FROM tasks INNER JOIN users ON tasks.user_id = users.id WHERE tasks.is_completed = TRUE AND tasks.user_id = :user_id GROUP BY users.id) AS task_counts;"
    )
    average = db.execute(query, {"user_id": id}).fetchone()
    return average


def get_overdue_tasks_by_user_id(id, db: Session = get_db_session):
    query = text(
        "SELECT COUNT(tasks.id) AS overdue_tasks FROM tasks WHERE tasks.user_id = :user_id AND COALESCE(tasks.completed_at, now()) > tasks.due_date;"
    )
    overdue = db.execute(query, {"user_id": id}).fetchone()
    return overdue


def get_date_of_max_tasks_completed_by_user_id(id, db: Session = get_db_session):
    query = text(
        "SELECT DATE_TRUNC('day', completed_at)::date as date, COUNT(*) as completed_tasks FROM tasks WHERE is_completed = TRUE GROUP BY date ORDER BY completed_tasks DESC LIMIT 1;"
    )
    max_date = db.execute(query, {"user_id": id}).fetchone()
    return max_date


def get_days_of_week_with_tasks_created_by_user_id(id, db: Session = get_db_session):
    query = text(
        "SELECT TRIM(to_char(tasks.created_at, 'Day')) AS day_of_week, count(*) AS created_tasks FROM tasks WHERE tasks.user_id = :user_id GROUP BY day_of_week ORDER BY date_part('dow', MIN(tasks.created_at));"
    )
    tasks_per_day = db.execute(query, {"user_id": id}).fetchall()
    return tasks_per_day
