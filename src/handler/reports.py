from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.exceptions import NoCompleteTasksError
from src.repository import reports as repository


def count_tasks(db: Session, current_user: int):
    try:
        count = repository.get_count_of_tasks(current_user.id, db)
        return count
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while generating a report"}',
        ) from None


def average_tasks(db: Session, current_user: int):
    try:
        average = repository.get_average_tasks(current_user.id, db)
        return average
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while generating a report"}',
        ) from None


def overdue_tasks(db: Session, current_user: int):
    try:
        overdue = repository.get_overdue_tasks(current_user.id, db)
        return overdue
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while generating a report"}',
        ) from None


def date_max_tasks(db: Session, current_user: int):
    try:
        max_date = repository.get_date_of_max_tasks_completed(current_user.id, db)
        return max_date
    except NoCompleteTasksError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="there are no completed tasks"
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while generating a report"}',
        ) from None


def day_of_week_tasks(db: Session, current_user: int):
    try:
        tasks_per_day = repository.get_days_of_week_with_tasks_created(
            current_user.id, db
        )
        return tasks_per_day
    except NoCompleteTasksError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="there are no completed tasks"
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while generating a report"}',
        ) from None
