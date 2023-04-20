from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from src.dtos import dto_users
from src.exceptions import GetError
from src.repository.tasks import get_max_tasks
from src.repository.users import get_user, get_verification_token


def is_email_same(user: dto_users.UserResponse, db: Session):
    try:
        user_check = get_user(db, user_id=None, email=user.email)
        if user_check:
            return True
    except GetError:
        pass


def false_token(token: int, db: Session):
    local_tz = ZoneInfo("Asia/Karachi")
    now_local = datetime.now(local_tz)
    try:
        verification_token = get_verification_token(db, token=token, id=None)
        if verification_token.expires_at < now_local:
            return True
    except GetError:
        return True


def max_tasks_reached(
    db: Session,
    id: int,
):
    task_check = get_max_tasks(id, db)
    if task_check:
        return True
