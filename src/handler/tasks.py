from typing import Optional

from fastapi import Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_tasks
from src.handler.checks import does_task_exists, is_user_authorized, max_tasks_reached
from src.handler.utils import validate_user
from src.models import tasks

get_db_session = Depends(get_db)
validated_user = Depends(validate_user)


async def create_task_handler(
    task: dto_tasks.CreateTaskRequest,
    db: Session = get_db_session,
    current_user: int = validated_user,
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


async def update_task_handler(
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
    if not is_user_authorized(id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    task_query = db.query(tasks.Task).filter(tasks.Task.id == id)
    to_update_task = task_query.first()
    task_query.update(task.dict(exclude_unset=True), synchronize_session=False)
    db.commit()
    db.refresh(to_update_task)
    return to_update_task


async def delete_task_handler(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    if not does_task_exists(id, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"task with id: {id} does not exist",
        ) from None
    if not is_user_authorized(id, db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'{"not authorized to perform action"}',
        )
    db.query(tasks.Task).filter(tasks.Task.id == id).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def get_tasks_handler(
    db: Session = get_db_session,
    current_user: int = validated_user,
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


async def get_task_handler(
    id: int,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    try:
        if not is_user_authorized(id, db, current_user):
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


async def upload_file_handler(
    task_id: int,
    file: UploadFile = file,
    db: Session = get_db_session,
    current_user: int = validated_user,
):
    try:
        if not is_user_authorized(task_id, db, current_user):
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


async def download_file_handler(
    task_id: int,
    file_id: int,
    db: Session = get_db_session,
    current_user: int = validate_user,
):
    try:
        if not is_user_authorized(task_id, db, current_user):
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
        file_data = filecheck.file_attachment
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
