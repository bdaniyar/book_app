import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.book_genre import book_genres


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    isbn: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(2048), nullable=True, default=None)
    pages: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    average_rating: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("authors.id", ondelete="SET NULL"), nullable=True
    )
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

    author = relationship("Author", back_populates="books", lazy="selectin")
    genres = relationship(
        "Genre",
        secondary=book_genres,
        back_populates="books",
        lazy="selectin",
    )
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    library_entries = relationship("UserBook", back_populates="book", cascade="all, delete-orphan")
