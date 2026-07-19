import math
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user import User
from app.models.user_book import ReadingStatus, UserBook
from app.services.books import book_query


@dataclass(frozen=True)
class BookRecommendation:
    book: Book
    reason: str


def _popular_order(stmt):
    return stmt.order_by(
        Book.average_rating.desc(),
        Book.review_count.desc(),
        Book.title.asc(),
        Book.id.asc(),
    )


def _preference_profile(
    db: Session, user: User
) -> tuple[dict[uuid.UUID, float], dict[uuid.UUID, str], set[uuid.UUID], set[uuid.UUID]]:
    scores: dict[uuid.UUID, float] = {}
    genre_names: dict[uuid.UUID, str] = {}
    explicit_genres = {genre.id for genre in user.favorite_genres}
    excluded_books: set[uuid.UUID] = set()

    for genre in user.favorite_genres:
        scores[genre.id] = scores.get(genre.id, 0) + 5
        genre_names[genre.id] = genre.name

    entries = db.scalars(
        select(UserBook)
        .options(selectinload(UserBook.book).selectinload(Book.genres))
        .where(UserBook.user_id == user.id)
    ).all()
    status_weight = {
        ReadingStatus.want_to_read: 0.5,
        ReadingStatus.reading: 2.0,
        ReadingStatus.read: 3.0,
        ReadingStatus.dropped: -2.0,
    }
    for entry in entries:
        excluded_books.add(entry.book_id)
        weight = status_weight[entry.status] + (5 if entry.is_favorite else 0)
        for genre in entry.book.genres:
            scores[genre.id] = scores.get(genre.id, 0) + weight
            genre_names[genre.id] = genre.name

    reviews = db.scalars(
        select(Review)
        .options(selectinload(Review.book).selectinload(Book.genres))
        .where(Review.user_id == user.id)
    ).all()
    for review in reviews:
        excluded_books.add(review.book_id)
        weight = {1: -4.0, 2: -2.0, 3: 0.5, 4: 3.0, 5: 5.0}[review.rating]
        for genre in review.book.genres:
            scores[genre.id] = scores.get(genre.id, 0) + weight
            genre_names[genre.id] = genre.name

    return scores, genre_names, explicit_genres, excluded_books


def personalized_recommendations(
    db: Session, *, user: User, limit: int
) -> list[BookRecommendation]:
    scores, _, explicit_genres, excluded_books = _preference_profile(db, user)
    positive_genres = {genre_id for genre_id, score in scores.items() if score > 0}
    candidate_limit = max(limit * 20, 100)

    base_stmt = book_query()
    if excluded_books:
        base_stmt = base_stmt.where(Book.id.not_in(excluded_books))

    candidates: list[Book] = []
    if positive_genres:
        matching = db.scalars(
            _popular_order(
                base_stmt.where(Book.genres.any(Genre.id.in_(positive_genres)))
            ).limit(candidate_limit)
        ).unique().all()
        candidates.extend(matching)

    if len(candidates) < limit:
        fallback = db.scalars(
            _popular_order(base_stmt).limit(candidate_limit)
        ).unique().all()
        seen = {book.id for book in candidates}
        candidates.extend(book for book in fallback if book.id not in seen)

    def rank(book: Book) -> tuple[float, float, int, str, str]:
        affinity = sum(scores.get(genre.id, 0) for genre in book.genres)
        quality = float(book.average_rating or 0) * 0.25
        popularity = math.log1p(book.review_count) * 0.02
        return (
            affinity + quality + popularity,
            float(book.average_rating or 0),
            book.review_count,
            book.title.casefold(),
            str(book.id),
        )

    candidates.sort(
        key=lambda book: (
            -rank(book)[0],
            -rank(book)[1],
            -rank(book)[2],
            rank(book)[3],
            rank(book)[4],
        )
    )

    recommendations: list[BookRecommendation] = []
    for book in candidates[:limit]:
        matching_genres = [genre for genre in book.genres if scores.get(genre.id, 0) > 0]
        matching_genres.sort(
            key=lambda genre: (-scores[genre.id], genre.name.casefold(), str(genre.id))
        )
        if matching_genres:
            genre = matching_genres[0]
            if genre.id in explicit_genres:
                reason = f"Matches your favorite genre: {genre.name}"
            else:
                reason = f"Based on your library and ratings: {genre.name}"
        else:
            reason = "Highly rated by readers"
        recommendations.append(BookRecommendation(book=book, reason=reason))
    return recommendations


def recommendations_for_book(
    db: Session, *, book: Book, limit: int
) -> list[BookRecommendation]:
    if not book.genres:
        return []
    genre_ids = {genre.id for genre in book.genres}
    books = db.scalars(
        _popular_order(
            book_query()
            .where(Book.id != book.id)
            .where(Book.genres.any(Genre.id.in_(genre_ids)))
        ).limit(limit)
    ).unique().all()
    source_names = {genre.id: genre.name for genre in book.genres}
    return [
        BookRecommendation(
            book=item,
            reason=f"Similar genre: {next(source_names[g.id] for g in item.genres if g.id in source_names)}",
        )
        for item in books
    ]


def popular_in_genre(
    db: Session, *, genre: str, limit: int
) -> list[BookRecommendation]:
    clean_genre = genre.replace("-", " ").strip()
    books = db.scalars(
        _popular_order(
            book_query().where(Book.genres.any(Genre.name.ilike(clean_genre)))
        ).limit(limit)
    ).unique().all()
    return [
        BookRecommendation(book=book, reason=f"Popular in {clean_genre}")
        for book in books
    ]
