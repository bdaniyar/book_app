import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt has a 72-byte input limit; request validation enforces max_length accordingly.
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"sub": subject, "type": "access", "exp": expire, "jti": str(uuid.uuid4())}
    return jwt.encode(
        to_encode,
        str(settings.JWT_SECRET_KEY),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {"sub": subject, "type": "refresh", "exp": expire, "jti": str(uuid.uuid4())}
    return jwt.encode(
        to_encode,
        str(settings.JWT_SECRET_KEY),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_password_reset_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {
        "sub": subject,
        "type": "password_reset",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        to_encode,
        str(settings.JWT_SECRET_KEY),
        algorithm=settings.JWT_ALGORITHM,
    )


def create_email_verification_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=1)
    to_encode = {
        "sub": subject,
        "type": "email_verification",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        to_encode,
        str(settings.JWT_SECRET_KEY),
        algorithm=settings.JWT_ALGORITHM,
    )
