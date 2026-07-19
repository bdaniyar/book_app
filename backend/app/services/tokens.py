import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tokens import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)
from app.models.user import User


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def store_refresh_token(
    db: Session,
    user_id: uuid.UUID,
    token: str,
    *,
    commit: bool = True,
) -> RefreshToken:
    row = RefreshToken(
        user_id=user_id,
        token_hash=token_hash(token),
        expires_at=utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def get_active_refresh_token(db: Session, token: str) -> RefreshToken | None:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash(token)))
    if not row or row.revoked_at is not None or row.expires_at <= utcnow():
        return None
    return row


def rotate_refresh_token(
    db: Session,
    token: str,
    new_token: str,
    *,
    expected_user_id: uuid.UUID,
) -> RefreshToken | None:
    """Atomically consume a refresh token and issue its replacement.

    The row lock makes concurrent refresh requests serialize. Only the first
    request can consume the token; subsequent requests observe ``revoked_at``.
    The user is locked and checked in the same transaction so a deactivated
    account cannot receive a new session.
    """

    now = utcnow()
    row = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash(token))
        .with_for_update()
    )
    if (
        not row
        or row.user_id != expected_user_id
        or row.revoked_at is not None
        or row.expires_at <= now
    ):
        db.rollback()
        return None

    user = db.scalar(
        select(User).where(User.id == expected_user_id).with_for_update()
    )
    if not user or not user.is_active:
        db.rollback()
        return None

    row.revoked_at = now
    replacement = RefreshToken(
        user_id=expected_user_id,
        token_hash=token_hash(new_token),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add_all([row, replacement])
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(replacement)
    return replacement


def revoke_refresh_token(db: Session, token: str, *, commit: bool = True) -> None:
    row = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash(token))
        .with_for_update()
    )
    if row and row.revoked_at is None:
        row.revoked_at = utcnow()
        db.add(row)
        if commit:
            db.commit()
        else:
            db.flush()


def revoke_all_refresh_tokens(
    db: Session, user_id: uuid.UUID, *, commit: bool = True
) -> int:
    result = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=utcnow())
    )
    if commit:
        db.commit()
    else:
        db.flush()
    return int(result.rowcount or 0)


def store_password_reset_token(
    db: Session,
    user_id: uuid.UUID,
    token: str,
    *,
    commit: bool = True,
) -> PasswordResetToken:
    # A newly requested reset link invalidates all older unused links.
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=utcnow())
    )
    row = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash(token),
        expires_at=utcnow()
        + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def get_usable_password_reset_token(
    db: Session, token: str, *, for_update: bool = False
) -> PasswordResetToken | None:
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token_hash == token_hash(token)
    )
    if for_update:
        stmt = stmt.with_for_update()
    row = db.scalar(stmt)
    if not row or row.used_at is not None or row.expires_at <= utcnow():
        return None
    return row


def mark_password_reset_used(db: Session, row: PasswordResetToken) -> None:
    row.used_at = utcnow()
    db.add(row)


def store_email_verification_token(
    db: Session,
    user_id: uuid.UUID,
    token: str,
    *,
    commit: bool = True,
) -> EmailVerificationToken:
    db.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
        )
        .values(used_at=utcnow())
    )
    row = EmailVerificationToken(
        user_id=user_id,
        token_hash=token_hash(token),
        expires_at=utcnow() + timedelta(days=1),
    )
    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    else:
        db.flush()
    return row


def get_usable_email_verification_token(
    db: Session, token: str, *, for_update: bool = False
) -> EmailVerificationToken | None:
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.token_hash == token_hash(token)
    )
    if for_update:
        stmt = stmt.with_for_update()
    row = db.scalar(stmt)
    if not row or row.used_at is not None or row.expires_at <= utcnow():
        return None
    return row


def mark_email_verification_used(db: Session, row: EmailVerificationToken) -> None:
    row.used_at = utcnow()
    db.add(row)
