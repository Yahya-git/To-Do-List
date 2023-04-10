from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database import get_db
from src.handler.utils import validate_user

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


def count_tasks_handler(
    db: Session = get_db_session, current_user: int = validated_user
):
    query = text(
        "SELECT COUNT(tasks.id) AS total_tasks, SUM(CASE WHEN tasks.is_completed = True THEN 1 ELSE 0 END) AS completed_tasks, SUM(CASE WHEN tasks.is_completed = False THEN 1 ELSE 0 END) AS incomplete_tasks FROM tasks WHERE tasks.user_id = :user_id GROUP BY tasks.is_completed"
    )
    count = db.execute(query, {"user_id": current_user.id}).fetchone()
    return count


def average_tasks_handler(
    db: Session = get_db_session, current_user: int = validated_user
):
    query = text(
        "SELECT AVG(completed_tasks / days_since_creation) as average_tasks_completed_per_day FROM ( SELECT COUNT(tasks.id) AS completed_tasks, DATE_PART('day', NOW() - users.created_at) AS days_since_creation FROM tasks INNER JOIN users ON tasks.user_id = users.id WHERE tasks.is_completed = TRUE AND tasks.user_id = :user_id GROUP BY users.id) AS task_counts;"
    )
    count = db.execute(query, {"user_id": current_user.id}).fetchone()
    return count
