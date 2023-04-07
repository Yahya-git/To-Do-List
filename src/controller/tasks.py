from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_tasks
from src.handler import utils
from src.handler.tasks import (
    create_task_handler,
    delete_task_handler,
    download_file_handler,
    get_task_handler,
    get_tasks_handler,
    update_task_handler,
    upload_file_handler,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

get_db_session = Depends(get_db)
validate_user = Depends(utils.validate_user)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=dto_tasks.TaskResponse
)
async def create_task(
    task: dto_tasks.CreateTaskRequest,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    return await create_task_handler(task, db, current_user)


@router.put(
    "/{id}", status_code=status.HTTP_200_OK, response_model=dto_tasks.TaskResponse
)
async def update_task(
    id: int,
    task: dto_tasks.UpdateTaskRequest,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    return await update_task_handler(id, task, db, current_user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    return await delete_task_handler(id, db, current_user)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[dto_tasks.TaskResponse],
)
async def get_tasks(
    db: Session = get_db_session,
    current_user: int = validate_user,
    search: Optional[str] = "",
    sort: Optional[str] = "due_date",
):
    return await get_tasks_handler(db, current_user, search, sort)


@router.get(
    "/{id}", status_code=status.HTTP_200_OK, response_model=dto_tasks.TaskResponse
)
async def get_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    return await get_task_handler(id, db, current_user)


file = File(...)


@router.post(
    "/{task_id}/file",
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    task_id: int,
    file: UploadFile = file,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    return await upload_file_handler(task_id, file, db, current_user)


@router.get(
    "/{task_id}/file/{file_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def download_file(
    task_id: int,
    file_id: int,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    return await download_file_handler(task_id, file_id, db, current_user)
