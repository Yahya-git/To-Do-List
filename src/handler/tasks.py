from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.dtos import dto_tasks
from src.exceptions import (
    CreateError,
    DeleteError,
    GetError,
    MaxTasksReachedError,
    UpdateError,
)
from src.models.tasks import Task
from src.repository import tasks as repository


def create_task(
    task_data: dto_tasks.CreateTaskRequest,
    db: Session,
    current_user: int,
):
    try:
        task = Task(user_id=current_user.id, **task_data.dict())
        new_task = repository.create_task(current_user.id, task, db)
        return new_task
    except MaxTasksReachedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"message: maximum number of tasks reached"}',
        ) from None
    except CreateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"message: something went wrong while creating a task"}',
        ) from None


def update_task(
    id: int,
    task_data: dto_tasks.UpdateTaskRequest,
    db: Session,
    current_user: int,
):
    local_tz = ZoneInfo("Asia/Karachi")
    now_local = datetime.now(local_tz)
    if task_data.is_completed is True:
        task_data.completed_at = now_local
    if task_data.is_completed is False:
        task_data.completed_at = None
    try:
        task = Task(**task_data.dict())
        updated_task = repository.update_task(id, task, db, current_user.id)
        return updated_task
    except UpdateError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {id} does not exist",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while updating the task"}',
        ) from None


def delete_task(
    id: int,
    db: Session,
    current_user: int,
):
    try:
        repository.delete_task(id, db, current_user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except DeleteError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {id} does not exist",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while deleting the task"}',
        ) from None


def get_tasks(
    db: Session,
    current_user: int,
    search: Optional[str] = "",
    sort: Optional[str] = "due_date",
):
    try:
        tasks = repository.get_tasks(current_user.id, db, search, sort)
        return tasks
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'{"there are no tasks"}'
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while retrieving the tasks"}',
        ) from None


def get_similar_tasks(
    db: Session,
    current_user: int,
):
    try:
        tasks = repository.get_similar_tasks(current_user.id, db)
        return tasks
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'{"there are no similar tasks"}',
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while retrieving the tasks"}',
        ) from None


def get_task(
    id: int,
    db: Session,
    current_user: int,
):
    try:
        task = repository.get_task(id, db, current_user.id)
        return task
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {id} does not exist",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while retrieving the task"}',
        ) from None


async def upload_file(
    task_id: int,
    file: UploadFile,
    db: Session,
    current_user: int,
):
    try:
        repository.get_task(task_id, db, current_user.id)
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {task_id} does not exist",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while retrieving the task"}',
        ) from None
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
    try:
        repository.get_task(task_id, db, current_user.id)
    except GetError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"not authorized to perform action or task with id: {task_id} does not exist",
        ) from None
    try:
        file = repository.get_file(file_id, task_id, db)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"file with id: {file_id} not found",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'{"something went wrong while retrieving the file"}',
        ) from None
    file_name = file.file_name
    file_data = file.file_attachment
    with open("temp_file", "wb") as f:
        f.write(file_data)
    return FileResponse(
        path="temp_file", filename=file_name, media_type="application/octet-stream"
    )
