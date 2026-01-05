from jose import JWTError, jwt

from app.core.config import settings


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(
        token,
        str(settings.JWT_SECRET_KEY),
        algorithms=[settings.JWT_ALGORITHM],
    )


__all__ = ["JWTError", "decode_token"]
