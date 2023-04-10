from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.handler.utils import validate_user
from src.repository.database_queries import (
    get_average_tasks_by_user_id,
    get_count_of_tasks_by_user_id,
    get_date_of_max_tasks_completed_by_user_id,
    get_days_of_week_with_tasks_created_by_user_id,
    get_overdue_tasks_by_user_id,
)

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


def count_tasks_handler(
    db: Session = get_db_session, current_user: int = validated_user
):
    count = get_count_of_tasks_by_user_id(current_user.id, db)
    return count


def average_tasks_handler(
    db: Session = get_db_session, current_user: int = validated_user
):
    average = get_average_tasks_by_user_id(current_user.id, db)
    return average


def overdue_tasks_handler(
    db: Session = get_db_session, current_user: int = validated_user
):
    overdue = get_overdue_tasks_by_user_id(current_user.id, db)
    return overdue


def date_max_tasks_handler(
    db: Session = get_db_session, current_user: int = validated_user
):
    max_date = get_date_of_max_tasks_completed_by_user_id(current_user.id, db)
    return max_date


def day_of_week_tasks_handler(
    db: Session = get_db_session, current_user: int = validated_user
):
    tasks_per_day = get_days_of_week_with_tasks_created_by_user_id(current_user.id, db)
    return tasks_per_day
