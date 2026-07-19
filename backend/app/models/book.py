import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    case,
    cast,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.book_genre import book_genres


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("external_source", "external_id", name="uq_books_external_source_id"),
        CheckConstraint("pages IS NULL OR pages > 0", name="ck_books_pages_positive"),
        CheckConstraint(
            "published_year IS NULL OR published_year BETWEEN 0 AND 3000",
            name="ck_books_published_year_range",
        ),
        CheckConstraint(
            "external_rating BETWEEN 0 AND 5",
            name="ck_books_external_rating_range",
        ),
        CheckConstraint(
            "local_rating BETWEEN 0 AND 5",
            name="ck_books_local_rating_range",
        ),
        CheckConstraint(
            "external_review_count >= 0",
            name="ck_books_external_review_count_nonnegative",
        ),
        CheckConstraint(
            "local_review_count >= 0",
            name="ck_books_local_review_count_nonnegative",
        ),
        Index(
            "ix_books_external_popularity",
            "external_review_count",
            "external_rating",
        ),
        Index("ix_books_local_popularity", "local_review_count", "local_rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    isbn: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    external_source: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)
    cover_url: Mapped[str | None] = mapped_column(String(2048), nullable=True, default=None)
    pages: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    external_rating: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, default=0
    )
    external_review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    local_rating: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, default=0
    )
    local_review_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
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

    @hybrid_property
    def review_count(self) -> int:
        """Combined count kept for the public API and older integrations."""

        return int(self.external_review_count or 0) + int(self.local_review_count or 0)

    @review_count.expression
    def review_count(cls):
        return cls.external_review_count + cls.local_review_count

    @hybrid_property
    def average_rating(self) -> float:
        """Weighted external/local rating kept as a compatibility aggregate."""

        external_count = int(self.external_review_count or 0)
        local_count = int(self.local_review_count or 0)
        total = external_count + local_count
        if total:
            return float(
                (
                    float(self.external_rating or 0) * external_count
                    + float(self.local_rating or 0) * local_count
                )
                / total
            )
        return float(self.local_rating or self.external_rating or 0)

    @average_rating.expression
    def average_rating(cls):
        total_count = cls.external_review_count + cls.local_review_count
        weighted_total = (
            cls.external_rating * cls.external_review_count
            + cls.local_rating * cls.local_review_count
        )
        return case(
            (
                total_count > 0,
                weighted_total / cast(total_count, Numeric(12, 4)),
            ),
            else_=case(
                (cls.local_rating > 0, cls.local_rating),
                else_=cls.external_rating,
            ),
        )
