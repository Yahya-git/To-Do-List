from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_users
from src.handler.utils import validate_user
from src.repository.database_queries import (
    get_max_tasks_by_user_id,
    get_task_by_id,
    get_tasks_by_user_id,
    get_user_by_email,
    get_user_by_id,
    get_verification_token,
)

now_local = datetime.now(ZoneInfo("Asia/Karachi"))

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


# Check Conditions
def is_email_same(user: dto_users.UserResponse, db: Session = get_db_session):
    user_check = get_user_by_email(user.email, db)
    if user_check:
        return True


def does_user_exist(id: int, db: Session = get_db_session):
    user_check = get_user_by_id(id, db)
    if user_check:
        return True


def false_token(token: int, db: Session = get_db_session):
    verification_token = get_verification_token(token, db)
    if not verification_token or verification_token.expires_at < now_local:
        return True


def is_user_authorized(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    user_check = get_user_by_id(id, db)
    if user_check.id == current_user.id:
        return True


def is_user_authorized_for_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    task_check = get_task_by_id(id, db)
    if task_check.user_id == current_user.id:
        return True


def do_tasks_exist(user_id: int, db: Session = get_db_session):
    tasks_check = get_tasks_by_user_id(user_id, db)
    if tasks_check:
        return True


def does_task_exists(
    id: int,
    db: Session = get_db_session,
):
    task_check = get_task_by_id(id, db)
    if task_check:
        return True


def max_tasks_reached(
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    task_check = get_max_tasks_by_user_id(current_user.id, db)
    if task_check:
        return True
