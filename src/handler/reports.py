from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.repository import reports as repository


def count_tasks(db: Session, current_user: int):
    count = repository.get_count_of_tasks(current_user.id, db)
    return count


def average_tasks(db: Session, current_user: int):
    average = repository.get_average_tasks(current_user.id, db)
    return average


def overdue_tasks(db: Session, current_user: int):
    overdue = repository.get_overdue_tasks_by(current_user.id, db)
    return overdue


def date_max_tasks(db: Session, current_user: int):
    max_date = repository.get_date_of_max_tasks_completed(current_user.id, db)
    if not max_date:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="there are no completed tasks"
        )
    return max_date


def day_of_week_tasks(db: Session, current_user: int):
    tasks_per_day = repository.get_days_of_week_with_tasks_created(current_user.id, db)
    if not tasks_per_day:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="there are no completed tasks"
        )
    return tasks_per_day
