import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    username = (username or "").strip()
    if not username:
        return None
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, data: RegisterRequest) -> User:
    user = User(
        email=str(data.email),
        username=data.username,
        first_name=None,
        last_name=None,
        bio=None,
        avatar_url=None,
        hashed_password=hash_password(data.password),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Could be email or username unique violation (or other constraint).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        )
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
