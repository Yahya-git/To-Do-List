from sqlalchemy import text
from sqlalchemy.orm import Session

from src.exceptions import NoCompleteTasksError


def get_count_of_tasks(id, db: Session):
    query = text(
        "SELECT COUNT(tasks.id) AS total_tasks, SUM(CASE WHEN tasks.is_completed = True THEN 1 ELSE 0 END) AS completed_tasks, SUM(CASE WHEN tasks.is_completed = False THEN 1 ELSE 0 END) AS incomplete_tasks FROM tasks WHERE tasks.user_id = :user_id;"
    )
    count = db.execute(query, {"user_id": id}).fetchone()
    return count


def get_average_tasks(id, db: Session):
    query = text(
        "SELECT COALESCE(AVG(completed_tasks / days_since_creation), 0) AS average_tasks_completed_per_day FROM ( SELECT COUNT(tasks.id) AS completed_tasks, GREATEST(DATE_PART('day', NOW() - users.created_at), 1) AS days_since_creation FROM tasks INNER JOIN users ON tasks.user_id = users.id WHERE tasks.is_completed = TRUE AND tasks.user_id = :user_id GROUP BY users.id) AS task_counts;"
    )
    average = db.execute(query, {"user_id": id}).fetchone()
    return average


def get_overdue_tasks(id, db: Session):
    query = text(
        "SELECT COUNT(tasks.id) AS overdue_tasks FROM tasks WHERE tasks.user_id = :user_id AND COALESCE(tasks.completed_at, now()) > tasks.due_date;"
    )
    overdue = db.execute(query, {"user_id": id}).fetchone()
    return overdue


def get_date_of_max_tasks_completed(id, db: Session):
    query = text(
        "SELECT COALESCE(DATE_TRUNC('day', completed_at)::date, CURRENT_DATE) AS date, COALESCE(COUNT(*), 0) AS completed_tasks FROM tasks WHERE is_completed = TRUE AND tasks.user_id = :user_id GROUP BY date ORDER BY completed_tasks DESC LIMIT 1;"
    )
    max_date = db.execute(query, {"user_id": id}).fetchone()
    if not max_date:
        raise NoCompleteTasksError
    return max_date


def get_days_of_week_with_tasks_created(id, db: Session):
    query = text(
        "SELECT TRIM(to_char(tasks.created_at, 'Day')) AS day_of_week, count(*) AS created_tasks FROM tasks WHERE tasks.user_id = :user_id GROUP BY day_of_week ORDER BY date_part('dow', MIN(tasks.created_at));"
    )
    tasks_per_day = db.execute(query, {"user_id": id}).fetchall()
    if not tasks_per_day:
        raise NoCompleteTasksError
    return tasks_per_day
