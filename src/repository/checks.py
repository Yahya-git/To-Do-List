from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from src.dtos import dto_users
from src.repository.tasks import get_max_tasks, get_task
from src.repository.users import get_user, get_verification_token

now_local = datetime.now(ZoneInfo("Asia/Karachi"))


def is_email_same(user: dto_users.UserResponse, db: Session):
    user_check = get_user(db, user_id=None, email=user.email)
    if user_check:
        return True


def false_token(token: int, db: Session):
    verification_token = get_verification_token(db, token=token, id=None)
    if not verification_token or verification_token.expires_at < now_local:
        return True


def is_user_authorized_for_task(
    id: int,
    db: Session,
    current_user: int,
):
    task_check = get_task(id, db, current_user.id)
    if task_check:
        return True


def max_tasks_reached(
    db: Session,
    current_user: int,
):
    task_check = get_max_tasks(current_user.id, db)
    if task_check:
        return True
