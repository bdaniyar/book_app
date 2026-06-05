import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.book import Book
from app.models.book_genre import book_genres
from app.models.genre import Genre
from app.models.review import Review
from app.models.user import User
from app.models.user_book import ReadingStatus, UserBook
from app.schemas.genre import FavoriteGenresUpdateRequest, GenreRead
from app.schemas.profile import ProfileUpdateRequest, ChangePasswordRequest
from app.schemas.stats import ProfileStatsRead, ReadingActivityRead
from app.schemas.user import UserRead
from app.services.users import get_user_by_email, get_user_by_username, change_password

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserRead)
def get_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("", response_model=UserRead)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    # email change (ensure unique)
    if payload.email is not None:
        new_email = str(payload.email)
        if new_email != current_user.email:
            existing = get_user_by_email(db, new_email)
            if existing and existing.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )
            current_user.email = new_email

    # username change (ensure unique)
    if payload.username is not None:
        new_username = payload.username.strip() or None
        if new_username != current_user.username:
            if new_username is not None:
                existing = get_user_by_username(db, new_username)
                if existing and existing.id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User with this username already exists",
                    )
            current_user.username = new_username

    if payload.first_name is not None:
        current_user.first_name = payload.first_name

    if payload.last_name is not None:
        current_user.last_name = payload.last_name

    if payload.bio is not None:
        current_user.bio = payload.bio

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    change_password(db, current_user, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stats", response_model=ProfileStatsRead)
def get_profile_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileStatsRead:
    books_read = db.scalar(
        select(func.count(UserBook.id)).where(
            UserBook.user_id == current_user.id,
            UserBook.status == ReadingStatus.read,
        )
    ) or 0
    pages_read = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    func.coalesce(
                        func.nullif(UserBook.progress_pages, 0),
                        Book.pages,
                        0,
                    )
                ),
                0,
            )
        )
        .select_from(UserBook)
        .join(Book, Book.id == UserBook.book_id)
        .where(
            UserBook.user_id == current_user.id,
            UserBook.status.in_([ReadingStatus.reading, ReadingStatus.read]),
        )
    ) or 0
    avg_rating = db.scalar(
        select(func.coalesce(func.avg(Review.rating), 0)).where(
            Review.user_id == current_user.id
        )
    ) or 0
    reviews_written = db.scalar(
        select(func.count(Review.id)).where(Review.user_id == current_user.id)
    ) or 0
    return ProfileStatsRead(
        booksRead=int(books_read),
        pagesRead=int(pages_read),
        avgRating=round(float(avg_rating), 1),
        reviewsWritten=int(reviews_written),
        readingStreak=0,
    )


@router.get("/reading-activity", response_model=list[ReadingActivityRead])
def get_reading_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReadingActivityRead]:
    entries = (
        db.query(UserBook)
        .filter(UserBook.user_id == current_user.id)
        .order_by(UserBook.updated_at.desc())
        .limit(20)
        .all()
    )
    return [
        ReadingActivityRead(
            date=entry.updated_at,
            action=f"marked as {entry.status.value}",
            title=entry.book.title,
        )
        for entry in entries
    ]


@router.get("/inferred-genres")
def get_inferred_genres(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, int | str]]:
    rows = db.execute(
        select(Genre.name, func.count(UserBook.id).label("count"))
        .join(book_genres, book_genres.c.genre_id == Genre.id)
        .join(UserBook, UserBook.book_id == book_genres.c.book_id)
        .where(
            UserBook.user_id == current_user.id,
            UserBook.status.in_(
                [ReadingStatus.reading, ReadingStatus.read, ReadingStatus.favorite]
            ),
        )
        .group_by(Genre.name)
        .order_by(func.count(UserBook.id).desc(), Genre.name.asc())
        .limit(8)
    ).all()
    return [{"name": name, "count": int(count)} for name, count in rows]


@router.get("/favorite-genres", response_model=list[GenreRead])
def get_favorite_genres(current_user: User = Depends(get_current_user)) -> list[Genre]:
    return list(current_user.favorite_genres)


@router.put("/favorite-genres", response_model=list[GenreRead])
def replace_favorite_genres(
    payload: FavoriteGenresUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Genre]:
    genres = db.query(Genre).filter(Genre.id.in_(payload.genre_ids)).order_by(Genre.name.asc()).all()
    if len(genres) != len(set(payload.genre_ids)):
        raise HTTPException(status_code=404, detail="One or more genres not found")

    current_user.favorite_genres = genres
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return list(current_user.favorite_genres)


@router.post("/favorite-genres/{genre_id}", response_model=list[GenreRead])
def add_favorite_genre(
    genre_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Genre]:
    g = db.query(Genre).filter(Genre.id == genre_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Genre not found")

    if all(x.id != g.id for x in current_user.favorite_genres):
        current_user.favorite_genres.append(g)
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

    return list(current_user.favorite_genres)


@router.delete("/favorite-genres/{genre_id}", response_model=list[GenreRead])
def remove_favorite_genre(
    genre_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Genre]:
    current_user.favorite_genres = [g for g in current_user.favorite_genres if g.id != genre_id]
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return list(current_user.favorite_genres)
