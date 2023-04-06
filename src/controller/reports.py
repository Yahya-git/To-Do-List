# from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.dtos import dto_reports
from src.handler import utils

from ..database import get_db

# from zoneinfo import ZoneInfo


# local_tz = ZoneInfo("Asia/Karachi")
# now_local = datetime.now(local_tz)

MAX_TASKS = 50

router = APIRouter(prefix="/reports", tags=["Reports"])

get_db_session = Depends(get_db)
validate_user = Depends(utils.validate_user)


@router.get("/count", response_model=dto_reports.CountReportResponse)
def count_tasks(db: Session = get_db_session, current_user: int = validate_user):
    query = text(
        "SELECT COUNT(tasks.id) AS total_tasks, SUM(CASE WHEN tasks.is_completed = True THEN 1 ELSE 0 END) AS completed_tasks, SUM(CASE WHEN tasks.is_completed = False THEN 1 ELSE 0 END) AS incomplete_tasks FROM tasks WHERE tasks.user_id = :user_id GROUP BY tasks.is_completed"
    )
    count = db.execute(query, {"user_id": current_user.id}).fetchone()
    return count


# @router.get("/average", response_model=dto_reports.AverageReportResponse)
# def average_tasks(db: Session = get_db_session, current_user: int = validate_user):
#     query = text("SELECT COUNT(tasks.id) AS total_tasks, SUM(CASE WHEN tasks.is_completed = True THEN 1 ELSE 0 END) AS completed_tasks, SUM(CASE WHEN tasks.is_completed = False THEN 1 ELSE 0 END) AS incomplete_tasks FROM tasks WHERE tasks.user_id = :user_id GROUP BY tasks.is_completed")
#     count = (db.execute(query, {'user_id': current_user.id}).fetchone())
#     return count
