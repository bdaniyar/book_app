import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tokens import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def store_refresh_token(db: Session, user_id, token: str) -> RefreshToken:
    row = RefreshToken(
        user_id=user_id,
        token_hash=token_hash(token),
        expires_at=utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(row)
    db.commit()
    return row


def get_active_refresh_token(db: Session, token: str) -> RefreshToken | None:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash(token)))
    if not row or row.revoked_at is not None or row.expires_at <= utcnow():
        return None
    return row


def revoke_refresh_token(db: Session, token: str) -> None:
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash(token)))
    if row and row.revoked_at is None:
        row.revoked_at = utcnow()
        db.add(row)
        db.commit()


def store_password_reset_token(db: Session, user_id, token: str) -> PasswordResetToken:
    row = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash(token),
        expires_at=utcnow()
        + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(row)
    db.commit()
    return row


def get_usable_password_reset_token(db: Session, token: str) -> PasswordResetToken | None:
    row = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash(token))
    )
    if not row or row.used_at is not None or row.expires_at <= utcnow():
        return None
    return row


def mark_password_reset_used(db: Session, row: PasswordResetToken) -> None:
    row.used_at = utcnow()
    db.add(row)


def store_email_verification_token(db: Session, user_id, token: str) -> EmailVerificationToken:
    row = EmailVerificationToken(
        user_id=user_id,
        token_hash=token_hash(token),
        expires_at=utcnow() + timedelta(days=1),
    )
    db.add(row)
    db.commit()
    return row


def get_usable_email_verification_token(
    db: Session, token: str
) -> EmailVerificationToken | None:
    row = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash(token)
        )
    )
    if not row or row.used_at is not None or row.expires_at <= utcnow():
        return None
    return row


def mark_email_verification_used(db: Session, row: EmailVerificationToken) -> None:
    row.used_at = utcnow()
    db.add(row)
