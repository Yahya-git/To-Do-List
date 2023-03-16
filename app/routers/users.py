from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas_users, utils
from ..database import models
from ..database.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas_users.User
)
# trunk-ignore(ruff/B008)
def create_user(user: schemas_users.UserCreate, db: Session = Depends(get_db)):
    usercheck = db.query(models.User).filter(models.User.email == user.email).first()
    if usercheck:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user with email: {user.email} already exists",
        )
    else:
        password = utils.hash(user.password)
        user.password = password
        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user


@router.patch(
    "/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=schemas_users.User
)
# trunk-ignore(ruff/B008)
def update_user(id: int, user: schemas_users.UserUpdate, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == id)
    update_user = user_query.first()
    if not update_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user with id: {id} does not exist",
        )
    else:
        update_data = {"updated_at": datetime.now()}
        if user.email:
            update_data["email"] = user.email
        if user.first_name:
            update_data["first_name"] = user.first_name
        if user.last_name:
            update_data["last_name"] = user.last_name
        if user.password:
            password = utils.hash(user.password)
            user.password = password
        user_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(update_user)
        return update_user
