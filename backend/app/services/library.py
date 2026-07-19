import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.book import Book
from app.models.user_book import ReadingStatus, UserBook
from app.schemas.library import LibraryEntryRead
from app.services.books import book_to_read


def library_entry_query():
    return select(UserBook).options(
        selectinload(UserBook.book).selectinload(Book.author),
        selectinload(UserBook.book).selectinload(Book.genres),
    )


def get_library_entry(
    db: Session, *, user_id: uuid.UUID, book_id: uuid.UUID
) -> UserBook | None:
    return db.scalar(
        library_entry_query().where(
            UserBook.user_id == user_id,
            UserBook.book_id == book_id,
        )
    )


def list_library_entries(
    db: Session,
    *,
    user_id: uuid.UUID,
    status: ReadingStatus | None = None,
    favorites_only: bool = False,
    page: int = 1,
    limit: int = 100,
) -> list[UserBook]:
    stmt = library_entry_query().where(UserBook.user_id == user_id)
    if status is not None:
        stmt = stmt.where(UserBook.status == status)
    if favorites_only:
        stmt = stmt.where(UserBook.is_favorite.is_(True))
    stmt = (
        stmt.order_by(UserBook.updated_at.desc(), UserBook.id.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return list(db.scalars(stmt).unique().all())


def _validate_progress(book: Book, progress_pages: int) -> None:
    if progress_pages < 0:
        raise ValueError("Progress cannot be negative")
    if book.pages is not None and progress_pages > book.pages:
        raise ValueError(f"Progress cannot exceed the book length ({book.pages} pages)")


def _apply_status(
    entry: UserBook,
    status: ReadingStatus,
) -> None:
    now = datetime.now(timezone.utc)
    entry.status = status

    if status == ReadingStatus.want_to_read:
        entry.progress_pages = 0
        entry.started_at = None
        entry.finished_at = None
    elif status == ReadingStatus.reading:
        entry.started_at = entry.started_at or now
        entry.finished_at = None
    elif status == ReadingStatus.read:
        entry.started_at = entry.started_at or now
        entry.finished_at = entry.finished_at or now
        if entry.book.pages is not None:
            entry.progress_pages = entry.book.pages
    elif status == ReadingStatus.dropped:
        entry.finished_at = None


def _apply_library_changes(
    entry: UserBook,
    *,
    status: ReadingStatus | None,
    progress_pages: int | None,
    is_favorite: bool | None,
) -> None:
    if status == ReadingStatus.want_to_read and progress_pages not in (None, 0):
        raise ValueError("A want-to-read book cannot have reading progress")
    if (
        status is None
        and entry.status == ReadingStatus.want_to_read
        and progress_pages not in (None, 0)
    ):
        raise ValueError("Set status to reading before recording progress")
    if progress_pages is not None:
        _validate_progress(entry.book, progress_pages)
        entry.progress_pages = progress_pages
    if status is not None:
        _apply_status(entry, status)
    if is_favorite is not None:
        entry.is_favorite = is_favorite


def add_or_update_library_entry(
    db: Session,
    *,
    user_id: uuid.UUID,
    book: Book,
    status: ReadingStatus | None = None,
    progress_pages: int | None = None,
    is_favorite: bool | None = None,
    commit: bool = True,
) -> UserBook:
    entry = get_library_entry(db, user_id=user_id, book_id=book.id)
    if entry is None:
        entry = UserBook(
            user_id=user_id,
            book=book,
            status=ReadingStatus.want_to_read,
            progress_pages=0,
            is_favorite=False,
        )
    _apply_library_changes(
        entry,
        status=status,
        progress_pages=progress_pages,
        is_favorite=is_favorite,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    else:
        db.flush()
    return entry


def update_library_entry(
    db: Session,
    *,
    entry: UserBook,
    status: ReadingStatus | None = None,
    progress_pages: int | None = None,
    is_favorite: bool | None = None,
    commit: bool = True,
) -> UserBook:
    _apply_library_changes(
        entry,
        status=status,
        progress_pages=progress_pages,
        is_favorite=is_favorite,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    else:
        db.flush()
    return entry


def remove_library_entry(db: Session, *, entry: UserBook) -> None:
    db.delete(entry)
    db.commit()


def library_entry_to_read(entry: UserBook) -> LibraryEntryRead:
    return LibraryEntryRead(
        id=entry.id,
        book=book_to_read(entry.book),
        status=entry.status,
        progress_pages=entry.progress_pages,
        is_favorite=entry.is_favorite,
        started_at=entry.started_at,
        finished_at=entry.finished_at,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )
