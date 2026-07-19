from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.book import Book
from app.models.review import Review
from app.models.user import User
from app.models.user_book import UserBook


def get_user_taste(db: Session, *, user: User) -> dict:
    entries = db.scalars(
        select(UserBook)
        .options(selectinload(UserBook.book).selectinload(Book.genres))
        .where(UserBook.user_id == user.id)
        .order_by(UserBook.updated_at.desc())
        .limit(100)
    ).all()
    reviews = db.scalars(
        select(Review)
        .options(selectinload(Review.book))
        .where(Review.user_id == user.id)
        .order_by(Review.updated_at.desc())
        .limit(50)
    ).all()
    return {
        "favoriteGenres": [genre.name for genre in user.favorite_genres],
        "library": [
            {
                "bookId": str(entry.book_id),
                "title": entry.book.title,
                "status": entry.status.value,
                "isFavorite": bool(getattr(entry, "is_favorite", False)),
                "progressPages": entry.progress_pages,
            }
            for entry in entries
        ],
        "ratings": [
            {
                "bookId": str(review.book_id),
                "title": review.book.title,
                "rating": review.rating,
            }
            for review in reviews
        ],
    }


def get_owned_conversation_user_id(user_id: uuid.UUID) -> uuid.UUID:
    """Makes the server-owned identity explicit at the tool boundary."""

    return user_id

