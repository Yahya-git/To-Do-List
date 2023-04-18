from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_misc, dto_reports
from src.handler import reports as handler
from src.handler.utils import validate_user

router = APIRouter(prefix="/reports", tags=["Reports"])

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


@router.get(
    "/count",
    response_model=dto_misc.ReportSingleResponse[dto_reports.CountReportResponse],
)
def count_tasks(db: Session = get_db_session, current_user: int = validated_user):
    report = handler.count_tasks(db, current_user)
    return {"status": "success", "data": {"report": report}}


@router.get(
    "/average",
    response_model=dto_misc.ReportSingleResponse[dto_reports.AverageReportResponse],
)
def average_tasks(db: Session = get_db_session, current_user: int = validated_user):
    report = handler.average_tasks(db, current_user)
    return {"status": "success", "data": {"report": report}}


@router.get(
    "/overdue",
    response_model=dto_misc.ReportSingleResponse[dto_reports.OverdueReportResponse],
)
def overdue_tasks(db: Session = get_db_session, current_user: int = validated_user):
    report = handler.overdue_tasks(db, current_user)
    return {"status": "success", "data": {"report": report}}


@router.get(
    "/max",
    response_model=dto_misc.ReportSingleResponse[dto_reports.DateMaxReportResponse],
)
def date_max_tasks(db: Session = get_db_session, current_user: int = validated_user):
    report = handler.date_max_tasks(db, current_user)
    return {"status": "success", "data": {"report": report}}


@router.get(
    "/day",
    response_model=dto_misc.ReportMultipleResponse[dto_reports.DayTasksReportResponse],
)
def day_of_week_tasks(db: Session = get_db_session, current_user: int = validated_user):
    reports = handler.day_of_week_tasks(db, current_user)
    return {"status": "success", "data": {"reports": reports}}
