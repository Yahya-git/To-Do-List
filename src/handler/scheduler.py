from datetime import datetime

from fastapi import APIRouter
from fastapi_utils.session import FastAPISessionMaker
from fastapi_utils.tasks import repeat_every
from sqlalchemy.orm import Session

from src.config import settings
from src.handler import utils
from src.repository import tasks as tasks_repository
from src.repository import users as users_repository

database_uri = f"postgresql+psycopg2://{settings.db_username}:{settings.db_password}@{settings.db_hostname}:{settings.db_port}/{settings.db_name}"
sessionmaker = FastAPISessionMaker(database_uri)


router = APIRouter()


async def send_tasks_reminder_mail(db: Session):
    all_tasks_due_today = tasks_repository.all_tasks_due_today(db)
    if not all_tasks_due_today:
        return
    user_ids_due_today = list({task.user_id for task in all_tasks_due_today})
    for user_id in user_ids_due_today:
        user_tasks_due_today = tasks_repository.tasks_due_today(db, user_id)
        user_tasks_list = []
        for task in user_tasks_due_today:
            task_dict = {
                "title": task.title,
                "description": task.description,
                "due_date": task.due_date.strftime("%Y-%m-%d %H:%M:%S"),
            }
            user_tasks_list.append(task_dict)
        user = users_repository.get_user(db, user_id=user_id, email=None)
        email = user.email
        template = "The following tasks are due today:\n"
        for task in user_tasks_list:
            template += f"- title: {task['title']} due_at: ({task['due_date']})\n"
        await utils.send_mail(
            email=email,
            subject_template="Tasks Reminder",
            template=template,
        )


@router.on_event("startup")
@repeat_every(seconds=60 * 5, wait_first=True)
async def reminder_task():
    with sessionmaker.context_session() as db:
        now_utc = datetime.utcnow()
        target_time = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        target_time_max = datetime.utcnow().replace(
            hour=0, minute=10, second=0, microsecond=0
        )
        if now_utc.date() == target_time.date():
            if now_utc >= target_time and target_time_max >= now_utc:
                print("Sending Tasks Reminder Mail")
                try:
                    await send_tasks_reminder_mail(db)
                except Exception as e:
                    print(e)
