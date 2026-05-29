import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.book import Book
from app.models.genre import Genre
from app.models.user import User
from app.schemas.book import BookRead
from app.services.books import book_query, book_to_read

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/personalized", response_model=list[BookRead])
def personalized(
    limit: int = Query(default=12, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    genre_ids = [g.id for g in current_user.favorite_genres]
    stmt = book_query().order_by(Book.average_rating.desc(), Book.review_count.desc()).limit(limit)
    if genre_ids:
        stmt = stmt.join(Book.genres).where(Genre.id.in_(genre_ids))
    books = db.scalars(stmt).unique().all()
    return [book_to_read(book) for book in books]


@router.get("/book/{book_id}", response_model=list[BookRead])
def based_on_book(
    book_id: uuid.UUID,
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    book = db.scalar(book_query().where(Book.id == book_id))
    if not book or not book.genres:
        return []
    genre_ids = [g.id for g in book.genres]
    books = db.scalars(
        book_query()
        .join(Book.genres)
        .where(Book.id != book.id, Genre.id.in_(genre_ids))
        .order_by(Book.average_rating.desc(), Book.review_count.desc())
        .limit(limit)
    ).unique().all()
    return [book_to_read(item) for item in books]


@router.get("/genre/{genre}", response_model=list[BookRead])
def popular_in_genre(
    genre: str,
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    books = db.scalars(
        book_query()
        .join(Book.genres)
        .where(Genre.name.ilike(genre.replace("-", " ")))
        .order_by(Book.average_rating.desc(), Book.review_count.desc())
        .limit(limit)
    ).unique().all()
    return [book_to_read(book) for book in books]


@router.get("/new-releases", response_model=list[BookRead])
def new_releases(
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    books = db.scalars(
        book_query().order_by(Book.published_year.desc().nullslast(), Book.created_at.desc()).limit(limit)
    ).unique().all()
    return [book_to_read(book) for book in books]
