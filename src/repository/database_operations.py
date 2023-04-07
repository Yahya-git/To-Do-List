from datetime import datetime, timedelta
from random import randint

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.dtos import dto_users
from src.handler.utils import hash_password
from src.models import users

get_db_session = Depends(get_db)


def add_to_database(record, db: Session = get_db_session):
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def delete_from_database(record, db: Session = get_db_session):
    db.delete(record)
    db.commit()


def update_in_database(record, db: Session = get_db_session):
    db.commit()
    db.refresh(record)


def create_new_user(user: dto_users.CreateUserRequest, db: Session = get_db_session):
    password = hash_password(user.password)
    user.password = password
    new_user = users.User(**user.dict())
    add_to_database(new_user, db)
    return new_user


def create_new_token(user: dto_users.UserResponse, db: Session = get_db_session):
    verification_token = (
        db.query(users.Verification)
        .filter(users.Verification.user_id == user.id)
        .first()
    )
    if verification_token:
        delete_from_database(verification_token, db)
    token = randint(100000, 999999)
    verification_token = users.Verification(
        user_id=user.id,
        token=token,
        expires_at=datetime.now() + timedelta(hours=24),
    )
    add_to_database(verification_token, db)
    return token


def delete_used_token(token: int, db: Session = get_db_session):
    verification_token = (
        db.query(users.Verification).filter(users.Verification.token == token).first()
    )
    user_id = verification_token.user_id
    delete_from_database(verification_token, db)
    return user_id


def verify_user(user_id, db: Session = get_db_session):
    user = db.query(users.User).filter(users.User.id == user_id).first()
    user.is_verified = True
    update_in_database(user, db)
