from datetime import datetime, timedelta
from random import randint
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from src.dtos.dto_users import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserRestricted,
)
from src.exceptions import (
    CreateError,
    DeleteError,
    DuplicateEmailError,
    GetError,
    UpdateError,
)
from src.handler.utils import hash_password
from src.models.users import User, Verification
from src.repository import checks


def create_user(user_data: CreateUserRequest, db: Session):
    if checks.is_email_same(user_data, db):
        raise DuplicateEmailError
    try:
        user_data.password = hash_password(user_data.password)
        user = User(**user_data.dict())
        db.add(user)
        db.commit()
        return user
    except SQLAlchemyError as e:
        print(f"Exception: {e}")
        raise CreateError from e


def update_user(user_id: int, user_data: UpdateUserRequest, db: Session):
    query = (
        User.__table__.update()
        .returning("*")
        .where(User.__table__.c.id == user_id)
        .values(
            email=coalesce(user_data.email, User.__table__.c.email),
            first_name=coalesce(user_data.first_name, User.__table__.c.first_name),
            last_name=coalesce(user_data.last_name, User.__table__.c.last_name),
            password=coalesce(user_data.password, User.__table__.c.password),
        )
    )
    user = db.execute(query).fetchone()
    if not user:
        raise UpdateError
    db.commit()
    return user


def update_user_restricted(user_id: int, user_data: UpdateUserRestricted, db: Session):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .update(user_data.dict(exclude_unset=True), synchronize_session=False)
    )
    if not user:
        raise UpdateError
    db.commit()
    return user


def get_user(db: Session, user_id: Optional[int], email: Optional[str]):
    user = db.query(User).filter(or_(User.id == user_id, User.email == email)).first()
    if not user:
        raise GetError
    return user


def create_verification_token(id: int, db: Session):
    try:
        token = get_verification_token(db, token=None, id=id)
        delete_verification_token(token.token, db)
    except GetError:
        pass
    except DeleteError:
        pass
    try:
        token = randint(100000, 999999)
        verification_token = Verification(
            user_id=id,
            token=token,
            expires_at=datetime.now() + timedelta(hours=24),
        )
        db.add(verification_token)
        db.commit()
        return verification_token
    except SQLAlchemyError as e:
        print(f"Exception: {e}")
        raise CreateError from e


def delete_verification_token(token: int, db: Session):
    token_data = db.query(Verification).filter(Verification.token == token).first()
    db.query(Verification).filter(Verification.token == token).delete()
    if not token_data:
        raise DeleteError
    db.commit()
    return token_data


def get_verification_token(db: Session, token: Optional[int], id: Optional[int]):
    verification_token = (
        db.query(Verification)
        .filter(or_(Verification.token == token, Verification.user_id == id))
        .first()
    )
    if not verification_token:
        raise GetError
    return verification_token
