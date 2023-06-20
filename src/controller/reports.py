import pickle

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.dtos import dto_misc, dto_reports
from src.handler import reports as handler
from src.handler.utils import validate_user
from src.redis import redis_client

router = APIRouter(prefix="/reports", tags=["Reports"])

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


@router.get(
    "/count",
    response_model=dto_misc.ReportSingleResponse[dto_reports.CountReportResponse],
)
def count_tasks(db: Session = get_db_session, current_user: int = validated_user):
    cache_key = f"task_count_report_user_{current_user.id}"
    cache_data = redis_client.get(cache_key)
    if cache_data:
        print("Cache Hit!")
        report = pickle.loads(cache_data)
    else:
        print("Cache Miss!!!")
        report = handler.count_tasks(db, current_user)
        redis_client.setex(cache_key, settings.cache_expiry_time, pickle.dumps(report))
    response = {"status": "success", "data": {"report": report}}
    return response


@router.get(
    "/average",
    response_model=dto_misc.ReportSingleResponse[dto_reports.AverageReportResponse],
)
def average_tasks(db: Session = get_db_session, current_user: int = validated_user):
    cache_key = f"task_average_report_user_{current_user.id}"
    cache_data = redis_client.get(cache_key)
    if cache_data:
        print("Cache Hit!")
        report = pickle.loads(cache_data)
    else:
        print("Cache Miss!!!")
        report = handler.average_tasks(db, current_user)
        redis_client.setex(cache_key, settings.cache_expiry_time, pickle.dumps(report))
    response = {"status": "success", "data": {"report": report}}
    return response


@router.get(
    "/overdue",
    response_model=dto_misc.ReportSingleResponse[dto_reports.OverdueReportResponse],
)
def overdue_tasks(db: Session = get_db_session, current_user: int = validated_user):
    cache_key = f"task_overdue_report_user_{current_user.id}"
    cache_data = redis_client.get(cache_key)
    if cache_data:
        print("Cache Hit!")
        report = pickle.loads(cache_data)
    else:
        print("Cache Miss!!!")
        report = handler.overdue_tasks(db, current_user)
        redis_client.setex(cache_key, settings.cache_expiry_time, pickle.dumps(report))
    response = {"status": "success", "data": {"report": report}}
    return response


@router.get(
    "/max",
    response_model=dto_misc.ReportSingleResponse[dto_reports.DateMaxReportResponse],
)
def date_max_tasks(db: Session = get_db_session, current_user: int = validated_user):
    cache_key = f"task_date_max_report_user_{current_user.id}"
    cache_data = redis_client.get(cache_key)
    if cache_data:
        print("Cache Hit!")
        report = pickle.loads(cache_data)
    else:
        print("Cache Miss!!!")
        report = handler.date_max_tasks(db, current_user)
        redis_client.setex(cache_key, settings.cache_expiry_time, pickle.dumps(report))
    response = {"status": "success", "data": {"report": report}}
    return response


@router.get(
    "/day",
    response_model=dto_misc.ReportMultipleResponse[dto_reports.DayTasksReportResponse],
)
def day_of_week_tasks(db: Session = get_db_session, current_user: int = validated_user):
    cache_key = f"task_day_of_week_report_user_{current_user.id}"
    cache_data = redis_client.get(cache_key)
    if cache_data:
        print("Cache Hit!")
        reports = pickle.loads(cache_data)
    else:
        print("Cache Miss!!!")
        reports = handler.day_of_week_tasks(db, current_user)
        redis_client.setex(cache_key, settings.cache_expiry_time, pickle.dumps(reports))
    response = {"status": "success", "data": {"reports": reports}}
    return response
