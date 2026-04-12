from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass

# Import models so SQLAlchemy registers them on Base.metadata
from app.models.user import User  # noqa: F401
from app.models.genre import Genre  # noqa: F401
from app.models.user_favorite_genre import user_favorite_genres  # noqa: F401

