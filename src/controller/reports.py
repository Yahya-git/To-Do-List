from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_reports
from src.handler.utils import validate_user

router = APIRouter(prefix="/reports", tags=["Reports"])

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


@router.get("/count", response_model=dto_reports.CountReportResponse)
def count_tasks(db: Session = get_db_session, current_user: int = validated_user):
    query = text(
        "SELECT COUNT(tasks.id) AS total_tasks, SUM(CASE WHEN tasks.is_completed = True THEN 1 ELSE 0 END) AS completed_tasks, SUM(CASE WHEN tasks.is_completed = False THEN 1 ELSE 0 END) AS incomplete_tasks FROM tasks WHERE tasks.user_id = :user_id GROUP BY tasks.is_completed"
    )
    count = db.execute(query, {"user_id": current_user.id}).fetchone()
    return count


# @router.get("/average", response_model=dto_reports.AverageReportResponse)
# def average_tasks(db: Session = get_db_session, current_user: int = validated_user):
#     query = text("SELECT COUNT(tasks.id) AS total_tasks, SUM(CASE WHEN tasks.is_completed = True THEN 1 ELSE 0 END) AS completed_tasks, SUM(CASE WHEN tasks.is_completed = False THEN 1 ELSE 0 END) AS incomplete_tasks FROM tasks WHERE tasks.user_id = :user_id GROUP BY tasks.is_completed")
#     count = (db.execute(query, {'user_id': current_user.id}).fetchone())
#     return count
