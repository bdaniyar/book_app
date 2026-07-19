import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ReadingStatus(str, enum.Enum):
    reading = "reading"
    want_to_read = "want-to-read"
    read = "read"
    dropped = "dropped"


class UserBook(Base):
    __tablename__ = "user_books"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_books_user_book"),
        CheckConstraint(
            "progress_pages >= 0", name="ck_user_books_progress_pages_nonnegative"
        ),
        Index("ix_user_books_user_status", "user_id", "status"),
        Index("ix_user_books_user_favorite", "user_id", "is_favorite"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ReadingStatus] = mapped_column(
        Enum(ReadingStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ReadingStatus.want_to_read,
    )
    progress_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    user = relationship("User", back_populates="library_entries", lazy="selectin")
    book = relationship("Book", back_populates="library_entries", lazy="selectin")
