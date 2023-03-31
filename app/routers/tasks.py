# from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.openapi.models import Response
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import utils
from app.schemas import schemas_tasks

from ..database.database import get_db
from ..database.models import tasks

# from zoneinfo import ZoneInfo


# local_tz = ZoneInfo("Asia/Karachi")
# now_local = datetime.now(local_tz)

MAX_TASKS = 50

router = APIRouter(prefix="/tasks", tags=["Tasks"])

get_db_session = Depends(get_db)
get_current_user = Depends(utils.get_current_user)


def user_auth(
    id: int,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    usercheck = db.query(tasks.Task).filter(tasks.Task.id == id).first()
    if usercheck.user_id == current_user.id:
        return True


def does_task_exists(
    id: int,
    db: Session = get_db_session,
):
    taskcheck = db.query(tasks.Task).filter(tasks.Task.id == id).first()
    if taskcheck:
        return True


def max_tasks_reached(
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    taskcheck = (
        db.query(tasks.Task.user_id)
        .filter(tasks.Task.user_id == current_user.id)
        .group_by(tasks.Task.user_id)
        .having(func.count(tasks.Task.user_id) == MAX_TASKS)
        .first()
    )
    if taskcheck:
        return True


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas_tasks.Task
)
async def create_task(
    task: schemas_tasks.TaskCreate,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    if max_tasks_reached(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"max number of tasks reached"}',
        )
    task = tasks.Task(user_id=current_user.id, **task.dict())
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
    if not does_task_exists(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        ) from None
    if not user_auth(id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    task_query = db.query(tasks.Task).filter(tasks.Task.id == id)
    updated_task = task_query.first()
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
    if not does_task_exists(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        ) from None
    if not user_auth(id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    db.query(tasks.Task).filter(tasks.Task.id == id).delete(synchronize_session=False)
    db.commit()
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        description="task deleted successfully",
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
    try:
        sort_attr = getattr(tasks.Task, sort)
        all_tasks = (
            db.query(tasks.Task)
            .filter(
                tasks.Task.user_id == current_user.id,
                tasks.Task.title.contains(search),
            )
            .order_by(sort_attr)
            .all()
        )
        return all_tasks
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'{"there are no tasks"}',
        ) from None


@router.get(
    "/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_tasks.Task
)
async def get_task(
    id: int,
    db: Session = get_db_session,
    current_user: int = get_current_user,
):
    try:
        if not user_auth(id, db, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{"not authorized to perform action"}',
            )
        task = (
            db.query(tasks.Task)
            .filter(tasks.Task.user_id == current_user.id, tasks.Task.id == id)
            .first()
        )
        return task
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        ) from None


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
    try:
        if not user_auth(task_id, db, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{"not authorized to perform action"}',
            )
        file_name = file.filename
        file_data = await file.read()
        attachment = tasks.Attachment(
            task_id=task_id, file_attachment=file_data, file_name=file_name
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return {"message": f"successfully attached file: {file_name}"}
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {task_id} does not exist",
        ) from None


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
    try:
        if not user_auth(task_id, db, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{"not authorized to perform action"}',
            )
        filecheck = (
            db.query(tasks.Attachment)
            .filter(tasks.Attachment.id == file_id, tasks.Attachment.task_id == task_id)
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
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {task_id} does not exist",
        ) from None
