from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_users
from src.models import tasks, users

from ..handler.utils import validate_user

MAX_TASKS = 50
local_tz = ZoneInfo("Asia/Karachi")
now_local = datetime.now(local_tz)

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


# Check Conditions
def is_email_same(user: dto_users.UserResponse, db: Session = get_db_session):
    usercheck = db.query(users.User).filter(users.User.email == user.email).first()
    if usercheck:
        return True


def does_user_exist(id: int, db: Session = get_db_session):
    usercheck = db.query(users.User).filter(users.User.id == id).first()
    if usercheck:
        return True


def false_token(token: int, db: Session = get_db_session):
    verification_token = (
        db.query(users.Verification).filter(users.Verification.token == token).first()
    )
    if not verification_token or verification_token.expires_at < now_local:
        return True


def is_user_authorized(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    usercheck = db.query(tasks.Task).filter(tasks.Task.id == id).first()
    if usercheck.user_id == current_user.id:
        return True


def does_task_exists(
    id: int,
    db: Session = get_db_session,
):
    taskcheck = db.query(tasks.Task).filter(tasks.Task.id == id).first()
    if taskcheck:
        return True


def max_tasks_reached(
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    taskcheck = (
        db.query(tasks.Task.user_id)
        .filter(tasks.Task.user_id == current_user.id)
        .group_by(tasks.Task.user_id)
        .having(func.count(tasks.Task.user_id) == MAX_TASKS)
        .first()
    )
    if taskcheck:
        return True
