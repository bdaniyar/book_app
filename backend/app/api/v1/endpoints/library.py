import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.book import Book
from app.models.user import User
from app.models.user_book import ReadingStatus
from app.schemas.library import (
    LibraryAddRequest,
    LibraryEntryRead,
    LibraryStatusUpdateRequest,
)
from app.services.books import book_query
from app.services.library import (
    add_or_update_library_entry,
    get_library_entry,
    library_entry_to_read,
    list_library_entries,
    remove_library_entry,
    update_library_entry,
)

router = APIRouter(prefix="/library", tags=["library"])


def _entries_for_user(
    db: Session,
    user: User,
    *,
    status_filter: ReadingStatus | None = None,
    favorites_only: bool = False,
    page: int = 1,
    limit: int = 100,
) -> list[LibraryEntryRead]:
    entries = list_library_entries(
        db,
        user_id=user.id,
        status=status_filter,
        favorites_only=favorites_only,
        page=page,
        limit=limit,
    )
    return [library_entry_to_read(entry) for entry in entries]


@router.get("", response_model=list[LibraryEntryRead])
def get_library(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LibraryEntryRead]:
    return _entries_for_user(db, current_user, page=page, limit=limit)


@router.get("/reading", response_model=list[LibraryEntryRead])
def get_reading(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LibraryEntryRead]:
    return _entries_for_user(
        db, current_user, status_filter=ReadingStatus.reading, page=page, limit=limit
    )


@router.get("/want-to-read", response_model=list[LibraryEntryRead])
def get_want_to_read(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LibraryEntryRead]:
    return _entries_for_user(
        db,
        current_user,
        status_filter=ReadingStatus.want_to_read,
        page=page,
        limit=limit,
    )


@router.get("/favorites", response_model=list[LibraryEntryRead])
def get_favorites(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LibraryEntryRead]:
    return _entries_for_user(
        db, current_user, favorites_only=True, page=page, limit=limit
    )


@router.get("/read", response_model=list[LibraryEntryRead])
def get_read(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LibraryEntryRead]:
    return _entries_for_user(
        db, current_user, status_filter=ReadingStatus.read, page=page, limit=limit
    )


@router.get("/dropped", response_model=list[LibraryEntryRead])
def get_dropped(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LibraryEntryRead]:
    return _entries_for_user(
        db, current_user, status_filter=ReadingStatus.dropped, page=page, limit=limit
    )


@router.post("/add", response_model=LibraryEntryRead)
def add_book(
    payload: LibraryAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryEntryRead:
    book = db.scalar(book_query().where(Book.id == payload.book_id))
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    try:
        entry = add_or_update_library_entry(
            db,
            user_id=current_user.id,
            book=book,
            status=payload.status,
            progress_pages=payload.progress_pages,
            is_favorite=payload.is_favorite,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return library_entry_to_read(entry)


@router.patch("/update/{book_id}", response_model=LibraryEntryRead)
def update_status(
    book_id: uuid.UUID,
    payload: LibraryStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryEntryRead:
    entry = get_library_entry(db, user_id=current_user.id, book_id=book_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Book is not in your library")
    try:
        entry = update_library_entry(
            db,
            entry=entry,
            status=payload.status,
            progress_pages=payload.progress_pages,
            is_favorite=payload.is_favorite,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return library_entry_to_read(entry)


@router.delete("/remove/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_book(
    book_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    entry = get_library_entry(db, user_id=current_user.id, book_id=book_id)
    if entry:
        remove_library_entry(db, entry=entry)
    return None
