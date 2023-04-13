from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.dtos import dto_tasks
from src.repository import checks
from src.repository import tasks as repository

now_local = datetime.now(ZoneInfo("Asia/Karachi"))


def create_task(
    task: dto_tasks.CreateTaskRequest,
    db: Session,
    current_user: int,
):
    if checks.max_tasks_reached(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"max number of tasks reached"}',
        )
    new_task = repository.create_task(current_user.id, task, db)
    return new_task


def update_task(
    id: int,
    task: dto_tasks.UpdateTaskRequest,
    db: Session,
    current_user: int,
):
    if task.is_completed is True:
        task.completed_at = now_local
    if task.is_completed is False:
        task.completed_at = None
    updated_task = repository.update_task(id, task, db, current_user.id)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {id} does not exist",
        )
    return updated_task


def delete_task(
    id: int,
    db: Session,
    current_user: int,
):
    deleted_task = repository.delete_task(id, db, current_user.id)
    if not deleted_task:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {id} does not exist",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def get_tasks(
    db: Session,
    current_user: int,
    search: Optional[str] = "",
    sort: Optional[str] = "due_date",
):
    tasks = repository.get_tasks(current_user.id, db, search, sort)
    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'{"there are no tasks"}'
        )
    return tasks


def get_task(
    id: int,
    db: Session,
    current_user: int,
):
    task = repository.get_task(id, db, current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {id} does not exist",
        )
    return task


async def upload_file(
    task_id: int,
    file: UploadFile,
    db: Session,
    current_user: int,
):
    if not checks.is_user_authorized_for_task(task_id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    file_name = file.filename
    file_data = await file.read()
    attachment = repository.create_file(task_id, file_name, file_data, db)
    return {
        "message": "successfully attached file",
        "file_name": f"{file_name}",
        "file_id": f"{attachment.id}",
    }


async def download_file(
    task_id: int,
    file_id: int,
    db: Session,
    current_user: int,
):
    if not checks.is_user_authorized_for_task(task_id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    file = repository.get_file(file_id, task_id, db)
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
