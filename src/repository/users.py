from datetime import datetime, timedelta
from random import randint
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from src.dtos.dto_users import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserRestricted,
)
from src.handler.utils import hash_password
from src.models.users import User, Verification


def create_user(user_data: CreateUserRequest, db: Session):
    user_data.password = hash_password(user_data.password)
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    return user


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
    updated_user = db.execute(query).fetchone()
    db.commit()
    return updated_user


def update_user_restricted(user_id: int, user_data: UpdateUserRestricted, db: Session):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .update(user_data.dict(exclude_unset=True), synchronize_session=False)
    )
    db.commit()
    return user


def get_user(db: Session, user_id: Optional[int], email: Optional[str]):
    user = db.query(User).filter(or_(User.id == user_id, User.email == email)).first()
    return user


def create_verification_token(id: int, db: Session):
    token = get_verification_token(db, token=None, id=id)
    if token:
        delete_verification_token(token.token, db)
    token = randint(100000, 999999)
    verification_token = Verification(
        user_id=id,
        token=token,
        expires_at=datetime.now() + timedelta(hours=24),
    )
    db.add(verification_token)
    db.commit()
    return verification_token


def delete_verification_token(token: int, db: Session):
    token_data = db.query(Verification).filter(Verification.token == token).first()
    db.query(Verification).filter(Verification.token == token).delete()
    db.commit()
    return token_data


def get_verification_token(db: Session, token: Optional[int], id: Optional[int]):
    verification_token = (
        db.query(Verification)
        .filter(or_(Verification.token == token, Verification.user_id == id))
        .first()
    )
    return verification_token
