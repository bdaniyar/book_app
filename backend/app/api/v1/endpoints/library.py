import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.book import Book
from app.models.user import User
from app.models.user_book import ReadingStatus, UserBook
from app.schemas.book import BookRead
from app.schemas.library import LibraryAddRequest, LibraryStatusUpdateRequest
from app.services.books import book_to_read

router = APIRouter(prefix="/library", tags=["library"])


def _books_for_status(
    db: Session, user: User, status: ReadingStatus | None = None
) -> list[BookRead]:
    stmt = (
        select(UserBook)
        .options(
            selectinload(UserBook.book).selectinload(Book.author),
            selectinload(UserBook.book).selectinload(Book.genres),
        )
        .where(UserBook.user_id == user.id)
        .order_by(UserBook.updated_at.desc())
    )
    if status is not None:
        stmt = stmt.where(UserBook.status == status)
    entries = db.scalars(stmt).all()
    return [book_to_read(entry.book) for entry in entries]


@router.get("", response_model=list[BookRead])
def get_library(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    return _books_for_status(db, current_user)


@router.get("/reading", response_model=list[BookRead])
def get_reading(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    return _books_for_status(db, current_user, ReadingStatus.reading)


@router.get("/want-to-read", response_model=list[BookRead])
def get_want_to_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    return _books_for_status(db, current_user, ReadingStatus.want_to_read)


@router.get("/favorites", response_model=list[BookRead])
def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    return _books_for_status(db, current_user, ReadingStatus.favorite)


@router.get("/read", response_model=list[BookRead])
def get_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookRead]:
    return _books_for_status(db, current_user, ReadingStatus.read)


@router.post("/add", response_model=BookRead)
def add_book(
    payload: LibraryAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookRead:
    book = db.get(Book, payload.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    entry = db.scalar(
        select(UserBook).where(
            UserBook.user_id == current_user.id,
            UserBook.book_id == payload.book_id,
        )
    )
    if not entry:
        entry = UserBook(user_id=current_user.id, book_id=payload.book_id)
    entry.status = payload.status
    if payload.status == ReadingStatus.reading and entry.started_at is None:
        entry.started_at = datetime.now(timezone.utc)
    if payload.status == ReadingStatus.read and entry.finished_at is None:
        entry.finished_at = datetime.now(timezone.utc)
    db.add(entry)
    db.commit()
    db.refresh(book)
    return book_to_read(book)


@router.patch("/update/{book_id}", response_model=BookRead)
def update_status(
    book_id: uuid.UUID,
    payload: LibraryStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookRead:
    entry = db.scalar(
        select(UserBook).where(
            UserBook.user_id == current_user.id,
            UserBook.book_id == book_id,
        )
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Book is not in your library")
    entry.status = payload.status
    if payload.progress_pages is not None:
        entry.progress_pages = payload.progress_pages
    if payload.status == ReadingStatus.read and entry.finished_at is None:
        entry.finished_at = datetime.now(timezone.utc)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return book_to_read(entry.book)


@router.delete("/remove/{book_id}", status_code=204)
def remove_book(
    book_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    entry = db.scalar(
        select(UserBook).where(
            UserBook.user_id == current_user.id,
            UserBook.book_id == book_id,
        )
    )
    if not entry:
        return None
    db.delete(entry)
    db.commit()
    return None
