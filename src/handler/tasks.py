from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_tasks
from src.handler.checks import (
    do_tasks_exist,
    does_task_exists,
    is_user_authorized_for_task,
    max_tasks_reached,
)
from src.handler.utils import validate_user
from src.repository.database_queries import (
    create_file_by_task_id,
    create_task_by_user_id,
    delete_task_by_id,
    get_file_by_file_and_task_id,
    get_task_by_id,
    get_tasks_by_user_id,
    update_task_by_id,
)

now_local = datetime.now(ZoneInfo("Asia/Karachi"))

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


def create_task_handler(
    task: dto_tasks.CreateTaskRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    if max_tasks_reached(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"max number of tasks reached"}',
        )
    new_task = create_task_by_user_id(current_user.id, task, db)
    return new_task


def update_task_handler(
    id: int,
    task: dto_tasks.UpdateTaskRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    if not does_task_exists(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        ) from None
    if not is_user_authorized_for_task(id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    to_update_task = get_task_by_id(id, db)
    if task.is_completed is True:
        if not task.completed_at:
            to_update_task.completed_at = now_local
    if task.is_completed is False:
        to_update_task.completed_at = None
    update_task_by_id(id, task, db)
    return to_update_task


def delete_task_handler(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    if not does_task_exists(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        ) from None
    if not is_user_authorized_for_task(id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    delete_task_by_id(id, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def get_tasks_handler(
    db: Session = get_db_session,
    current_user: int = validated_user,
    search: Optional[str] = "",
    sort: Optional[str] = "due_date",
):
    if not do_tasks_exist(current_user.id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'{"there are no tasks"}'
        )
    tasks = get_tasks_by_user_id(current_user.id, db, search, sort)
    return tasks


def get_task_handler(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    if not does_task_exists(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        )
    if not is_user_authorized_for_task(id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    task = get_task_by_id(id, db)
    return task


to_be_uploaded_file = File(...)


async def upload_file_handler(
    task_id: int,
    file: UploadFile = to_be_uploaded_file,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    try:
        if not is_user_authorized_for_task(task_id, db, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{"not authorized to perform action"}',
            )
        file_name = file.filename
        file_data = await file.read()
        attachment = create_file_by_task_id(task_id, file_name, file_data, db)
        return {
            "message": f"successfully attached file: {file_name} (file_id: {attachment.id})"
        }
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {task_id} does not exist",
        ) from None


async def download_file_handler(
    task_id: int,
    file_id: int,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    try:
        if not is_user_authorized_for_task(task_id, db, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{"not authorized to perform action"}',
            )
        file = get_file_by_file_and_task_id(file_id, task_id, db)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"file with id: {file_id} not found",
            )
        file_name = file.file_name
        file_data = file.file_attachment
        with open("temp_file", "wb") as f:
            f.write(file_data)
        return FileResponse(
            path="temp_file", filename=file_name, media_type="application/octet-stream"
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {task_id} does not exist",
        ) from None
