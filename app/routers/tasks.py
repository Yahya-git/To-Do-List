# from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.openapi.models import Response
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import utils
from app.schemas import schemas_tasks

from ..database import models
from ..database.database import get_db

# from zoneinfo import ZoneInfo


# local_tz = ZoneInfo("Asia/Karachi")
# now_local = datetime.now(local_tz)


router = APIRouter(prefix="/tasks", tags=["Tasks"])

get_db_session = Depends(get_db)
get_current_user = Depends(utils.get_current_user)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas_tasks.Task
)
async def create_task(
    task: schemas_tasks.TaskCreate,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    taskcheck = (
        db.query(models.Task.user_id)
        .group_by(models.Task.user_id)
        .having(func.count(models.Task.user_id) == 50)
        .first()
    )
    if taskcheck:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"max number of tasks reached"}',
        )
    task = models.Task(user_id=current_user.id, **task.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch(
    "/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_tasks.Task
)
async def update_task(
    id: int,
    task: schemas_tasks.TaskUpdate,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    updated_task = task_query.first()
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        )
    if updated_task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    task_query.update(task.dict(), synchronize_session=False)
    db.commit()
    db.refresh(updated_task)
    return updated_task


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    task_query = db.query(models.Task).filter(models.Task.id == id)
    deleted_task = task_query.first()
    if deleted_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        )
    if deleted_task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    task_query.delete(synchronize_session=False)
    db.commit()
    return Response(
        status_code=status.HTTP_204_NO_CONTENT, description="task deleted successfully"
    )


@router.get(
    "/", status_code=status.HTTP_202_ACCEPTED, response_model=List[schemas_tasks.Task]
)
async def get_tasks(
    db: Session = get_db_session,
    current_user: int = get_current_user,
    search: Optional[str] = "",
    sort: Optional[str] = "due_date",
):
    sort_attr = getattr(models.Task, sort)
    tasks = (
        db.query(models.Task)
        .filter(
            models.Task.user_id == current_user.id, models.Task.title.contains(search)
        )
        .order_by(sort_attr)
        .all()
    )
    return tasks


@router.get(
    "/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_tasks.Task
)
async def get_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    taskcheck = db.query(models.Task).filter(models.Task.id == id).first()
    if not taskcheck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        )
    task = (
        db.query(models.Task)
        .filter(models.Task.user_id == current_user.id, models.Task.id == id)
        .first()
    )
    return task


file = File(...)


@router.post(
    "/{task_id}/file",
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    task_id: int,
    file: UploadFile = file,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    taskcheck = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not taskcheck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {task_id} not found",
        )
    file_name = file.filename
    file_data = await file.read()
    attachment = models.Attachment(
        task_id=task_id, file_attachment=file_data, file_name=file_name
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return {"message": f"successfully attached file: {file_name}"}


@router.get(
    "/{task_id}/file/{file_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def download_file(
    task_id: int,
    file_id: int,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    filecheck = (
        db.query(models.Attachment)
        .filter(models.Attachment.id == file_id, models.Attachment.task_id == task_id)
        .first()
    )
    if not filecheck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"file with id: {file_id} not found",
        )
    file_name = filecheck.file_name
    file_data = bytes(filecheck.file_attachment)
    with open("temp_file", "wb") as f:
        f.write(file_data)
    return FileResponse(path="temp_file", filename=file_name)
