import uuid
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from passlib.exc import UnknownHashError

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.profile import ChangePasswordRequest
from app.services.tokens import revoke_all_refresh_tokens


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_username(username: str) -> str:
    return unicodedata.normalize("NFKC", username).strip()


def get_user_by_email(db: Session, email: str) -> User | None:
    normalized = normalize_email(email)
    return db.scalar(select(User).where(func.lower(User.email) == normalized))


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    username = normalize_username(username or "")
    if not username:
        return None
    return db.scalar(select(User).where(User.username == username))


def create_user(
    db: Session, data: RegisterRequest, *, commit: bool = True
) -> User:
    username = normalize_username(data.username)
    user = User(
        email=normalize_email(str(data.email)),
        username=username,
        first_name=None,
        last_name=None,
        bio=None,
        avatar_url=None,
        hashed_password=hash_password(data.password),
        is_active=True,
        email_verified=False,
        is_superuser=False,
    )
    db.add(user)
    try:
        if commit:
            db.commit()
        else:
            db.flush()
    except IntegrityError:
        db.rollback()
        # Could be email or username unique violation (or other constraint).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        )
    if commit:
        db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    try:
        ok = verify_password(password, user.hashed_password)
    except UnknownHashError:
        # Stored password isn't a valid hash (e.g. edited manually in admin).
        return None
    if not ok or not user.is_active:
        return None
    return user


def change_password(db: Session, user: User, payload: ChangePasswordRequest) -> None:
    try:
        password_matches = verify_password(
            payload.current_password, user.hashed_password
        )
    except UnknownHashError:
        password_matches = False

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if payload.new_password != payload.new_password2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.hashed_password = hash_password(payload.new_password)
    user.token_version += 1
    db.add(user)
    # Password changes invalidate every browser/device refresh session.
    revoke_all_refresh_tokens(db, user.id, commit=False)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
