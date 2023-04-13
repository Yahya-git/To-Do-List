from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_tasks
from src.handler import tasks as handler
from src.handler.utils import validate_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


# Create Task Endpoint
@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=dto_tasks.TaskResponse
)
async def create_task(
    task: dto_tasks.CreateTaskRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    return handler.create_task(task, db, current_user)


# Update Task Endpoint
@router.put(
    "/{id}", status_code=status.HTTP_200_OK, response_model=dto_tasks.TaskResponse
)
async def update_task(
    id: int,
    task: dto_tasks.UpdateTaskRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    return handler.update_task(id, task, db, current_user)


# Delete Task Endpoint
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    return handler.delete_task(id, db, current_user)


# Get Tasks Endpoint
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[dto_tasks.TaskResponse],
)
async def get_tasks(
    db: Session = get_db_session,
    current_user: int = validated_user,
    search: Optional[str] = "",
    sort: Optional[str] = "due_date",
):
    return handler.get_tasks(db, current_user, search, sort)


# Get Task Endpoint
@router.get(
    "/{id}", status_code=status.HTTP_200_OK, response_model=dto_tasks.TaskResponse
)
async def get_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    return handler.get_task(id, db, current_user)


file = File(...)


# Upload File to Task Endpoint
@router.post(
    "/{task_id}/file",
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    task_id: int,
    file: UploadFile = file,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    return await handler.upload_file(task_id, file, db, current_user)


# Download File from Task Endpoint
@router.get(
    "/{task_id}/file/{file_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def download_file(
    task_id: int,
    file_id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    return await handler.download_file(task_id, file_id, db, current_user)
