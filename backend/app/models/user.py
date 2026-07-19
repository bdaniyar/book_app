import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.user_favorite_genre import user_favorite_genres


class User(Base):
    __allow_unmapped__ = True
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "token_version >= 0", name="ck_users_token_version_nonnegative"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # You can loosen/tighten constraints later.
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        unique=True,
        default=None,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    bio: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        default=None,
    )

    favorite_genres = relationship(
        "Genre",
        secondary=user_favorite_genres,
        back_populates="users",
        lazy="selectin",
    )

    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    library_entries = relationship(
        "UserBook", back_populates="user", cascade="all, delete-orphan"
    )

    # Admin helper (not stored in DB): plain password field for admin forms.
    # sqladmin can bind this attribute in forms; we hash it into `hashed_password` in the admin view.
    password: str | None = None
