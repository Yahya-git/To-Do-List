from datetime import datetime, timedelta
from random import randint
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import coalesce

from src.exceptions import (
    CreateError,
    DeleteError,
    DuplicateEmailError,
    GetError,
    UpdateError,
)
from src.models.users import User, Verification
from src.repository import checks


def create_user(user: User, db: Session):
    if checks.is_email_same(user, db):
        raise DuplicateEmailError
    try:
        query = (
            User.__table__.insert()
            .returning("*")
            .values(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                password=user.password,
            )
        )
        new_user = db.execute(query).fetchone()
        db.commit()
        return new_user
    except Exception as e:
        print(f"Exception: {e}")
        raise CreateError from e


def update_user(user_id: int, user: User, db: Session):
    query = (
        User.__table__.update()
        .returning("*")
        .where(User.__table__.c.id == user_id)
        .values(
            email=coalesce(user.email, User.__table__.c.email),
            first_name=coalesce(user.first_name, User.__table__.c.first_name),
            last_name=coalesce(user.last_name, User.__table__.c.last_name),
            password=coalesce(user.password, User.__table__.c.password),
        )
    )
    user = db.execute(query).fetchone()
    if not user:
        raise UpdateError
    db.commit()
    return user


def update_user_restricted(user_id: int, user: User, db: Session):
    query = (
        User.__table__.update()
        .returning("*")
        .where(User.__table__.c.id == user_id)
        .values(
            is_verified=coalesce(user.is_verified, User.__table__.c.is_verified),
            is_oauth=coalesce(user.is_oauth, User.__table__.c.is_oauth),
        )
    )
    user = db.execute(query).fetchone()
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
        if token:
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
        query = (
            Verification.__table__.insert()
            .returning("*")
            .values(
                user_id=verification_token.user_id,
                token=verification_token.token,
                expires_at=verification_token.expires_at,
            )
        )
        new_token = db.execute(query).fetchone()
        db.commit()
        return new_token
    except Exception as e:
        print(f"Exception: {e}")
        raise CreateError from e


def delete_verification_token(token: int, db: Session):
    query = (
        Verification.__table__.delete()
        .returning("*")
        .where(Verification.__table__.c.token == token)
    )
    deleted_token = db.execute(query).fetchone()
    db.commit()
    if not deleted_token:
        raise DeleteError
    db.commit()
    return deleted_token


def get_verification_token(db: Session, token: Optional[int], id: Optional[int]):
    verification_token = (
        db.query(Verification)
        .filter(or_(Verification.token == token, Verification.user_id == id))
        .first()
    )
    if not verification_token:
        raise GetError
    return verification_token
