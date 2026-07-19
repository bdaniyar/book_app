import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_superuser
from app.db.session import get_db
from app.models.book import Book
from app.models.genre import Genre
from app.models.user import User
from app.schemas.book import BookCreateRequest, BookRead, BookUpdateRequest
from app.services.books import book_query, book_to_read, create_book, list_books, update_book

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookRead])
def get_books(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    return [book_to_read(book) for book in list_books(db, page=page, limit=limit)]


@router.get("/search", response_model=list[BookRead])
def search_books(
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    return [book_to_read(book) for book in list_books(db, q=q, page=page, limit=limit)]


@router.get("/trending", response_model=list[BookRead])
def trending_books(
    limit: int = Query(default=12, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    books = (
        db.scalars(
            book_query()
            .order_by(
                Book.review_count.desc(),
                Book.average_rating.desc(),
                Book.title.asc(),
                Book.id.asc(),
            )
            .limit(limit)
        )
        .unique()
        .all()
    )
    return [book_to_read(book) for book in books]


@router.get("/recommended", response_model=list[BookRead])
def recommended_books(
    limit: int = Query(default=12, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    books = (
        db.scalars(
            book_query()
            .order_by(
                Book.average_rating.desc(),
                Book.review_count.desc(),
                Book.title.asc(),
                Book.id.asc(),
            )
            .limit(limit)
        )
        .unique()
        .all()
    )
    return [book_to_read(book) for book in books]


@router.get("/category/{category}", response_model=list[BookRead])
def books_by_category(
    category: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    return [
        book_to_read(book)
        for book in list_books(db, category=category, page=page, limit=limit)
    ]


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: uuid.UUID, db: Session = Depends(get_db)) -> BookRead:
    book = db.scalar(book_query().where(Book.id == book_id))
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_to_read(book)


@router.get("/{book_id}/similar", response_model=list[BookRead])
def similar_books(
    book_id: uuid.UUID,
    limit: int = Query(default=4, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    book = db.scalar(book_query().where(Book.id == book_id))
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book.genres:
        return []
    genre_ids = [g.id for g in book.genres]
    books = (
        db.scalars(
            book_query()
            .where(Book.id != book.id)
            .where(Book.genres.any(Genre.id.in_(genre_ids)))
            .order_by(
                Book.average_rating.desc(),
                Book.review_count.desc(),
                Book.title.asc(),
                Book.id.asc(),
            )
            .limit(limit)
        )
        .unique()
        .all()
    )
    return [book_to_read(item) for item in books]


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book_endpoint(
    payload: BookCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> BookRead:
    try:
        book = create_book(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A book with this ISBN or external identifier already exists",
        ) from None
    return book_to_read(book)


@router.put("/{book_id}", response_model=BookRead)
def update_book_endpoint(
    book_id: uuid.UUID,
    payload: BookUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> BookRead:
    book = db.scalar(book_query().where(Book.id == book_id))
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    try:
        book = update_book(db, book, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A book with this ISBN or external identifier already exists",
        ) from None
    return book_to_read(book)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_endpoint(
    book_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> None:
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
