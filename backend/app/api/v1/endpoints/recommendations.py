import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.book import Book
from app.models.user import User
from app.schemas.book import BookRead
from app.services.books import book_query, book_to_read
from app.services.recommendations import (
    personalized_recommendations,
    popular_in_genre as get_popular_in_genre,
    recommendations_for_book,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/personalized", response_model=list[BookRead])
def personalized(
    limit: int = Query(default=12, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    recommendations = personalized_recommendations(db, user=current_user, limit=limit)
    return [
        book_to_read(item.book, recommendation_reason=item.reason)
        for item in recommendations
    ]


@router.get("/book/{book_id}", response_model=list[BookRead])
def based_on_book(
    book_id: uuid.UUID,
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    book = db.scalar(book_query().where(Book.id == book_id))
    if not book:
        return []
    recommendations = recommendations_for_book(db, book=book, limit=limit)
    return [
        book_to_read(item.book, recommendation_reason=item.reason)
        for item in recommendations
    ]


@router.get("/genre/{genre}", response_model=list[BookRead])
def popular_in_genre(
    genre: str,
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    recommendations = get_popular_in_genre(db, genre=genre, limit=limit)
    return [
        book_to_read(item.book, recommendation_reason=item.reason)
        for item in recommendations
    ]


@router.get("/new-releases", response_model=list[BookRead])
def new_releases(
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    books = db.scalars(
        book_query()
        .order_by(
            Book.published_year.desc().nullslast(),
            Book.created_at.desc(),
            Book.id.asc(),
        )
        .limit(limit)
    ).unique().all()
    return [book_to_read(book, recommendation_reason="Recently published") for book in books]
