from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.genre import Genre
from app.models.user_book import UserBook
from app.services.books import book_query, book_to_read


@dataclass(frozen=True)
class CatalogFilters:
    max_pages: int | None = None
    year_from: int | None = None
    min_rating: float | None = None
    genres: tuple[str, ...] = ()


PAGE_PATTERN = re.compile(
    r"(?:до|under|less\s+than|max(?:imum)?)\s*(\d{2,4})\s*(?:pages?|стр(?:аниц[а-я]*)?)",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(
    r"(?:после|с|since|after|from|не\s+старше)\s*(19\d{2}|20\d{2})",
    re.IGNORECASE,
)
RATING_PATTERN = re.compile(
    r"(?:rating|рейтинг)\s*(?:выше|от|above|over|at\s+least)?\s*(\d(?:[.,]\d)?)",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[\w'-]{3,}", re.UNICODE)
STOP_WORDS = {
    "book",
    "books",
    "recommend",
    "recommendation",
    "please",
    "find",
    "show",
    "книга",
    "книги",
    "книгу",
    "книг",
    "найди",
    "покажи",
    "посоветуй",
    "рекомендуй",
    "хочу",
    "читать",
    "страниц",
    "рейтинг",
}


def extract_filters(db: Session, message: str) -> CatalogFilters:
    page_match = PAGE_PATTERN.search(message)
    year_match = YEAR_PATTERN.search(message)
    rating_match = RATING_PATTERN.search(message)
    lowered = message.casefold().replace("-", " ")
    known_genres = db.scalars(select(Genre).order_by(Genre.name.asc())).all()
    genres = tuple(
        genre.name
        for genre in known_genres
        if genre.name.casefold().replace("-", " ") in lowered
    )
    return CatalogFilters(
        max_pages=int(page_match.group(1)) if page_match else None,
        year_from=int(year_match.group(1)) if year_match else None,
        min_rating=(
            float(rating_match.group(1).replace(",", "."))
            if rating_match
            else None
        ),
        genres=genres,
    )


def search_catalog(
    db: Session,
    *,
    message: str,
    user_id: uuid.UUID,
    book_id: uuid.UUID | None = None,
    limit: int = 8,
) -> list[Book]:
    filters = extract_filters(db, message)
    stmt = book_query()
    if filters.max_pages is not None:
        stmt = stmt.where(Book.pages.is_not(None), Book.pages <= filters.max_pages)
    if filters.year_from is not None:
        stmt = stmt.where(
            Book.published_year.is_not(None), Book.published_year >= filters.year_from
        )
    if filters.min_rating is not None:
        stmt = stmt.where(Book.average_rating >= filters.min_rating)
    if filters.genres:
        stmt = stmt.join(Book.genres).where(Genre.name.in_(filters.genres))
    stmt = stmt.order_by(
        Book.average_rating.desc(), Book.review_count.desc(), Book.created_at.desc()
    ).limit(300)
    books = list(db.scalars(stmt).unique().all())

    library_ids = set(
        db.scalars(select(UserBook.book_id).where(UserBook.user_id == user_id)).all()
    )
    favorite_genres = set(
        db.scalars(
            select(Genre.name)
            .join(Genre.users)
            .where(Genre.users.any(id=user_id))
        ).all()
    )
    terms = {
        token.casefold()
        for token in TOKEN_PATTERN.findall(message)
        if token.casefold() not in STOP_WORDS and not token.isdigit()
    }

    def score(book: Book) -> float:
        title = book.title.casefold()
        author = book.author.name.casefold() if book.author else ""
        description = (book.description or "").casefold()
        genres = {genre.name for genre in book.genres}
        genre_text = " ".join(genres).casefold()
        relevance = 0.0
        for term in terms:
            if term in title:
                relevance += 6
            if term in author:
                relevance += 4
            if term in genre_text:
                relevance += 3
            if term in description:
                relevance += 1
        relevance += 2 * len(genres & favorite_genres)
        relevance += float(book.average_rating or 0) * 0.35
        relevance += math.log10(max(int(book.review_count or 0), 1)) * 0.15
        if book.id in library_ids:
            relevance -= 8
        if book_id and book.id == book_id:
            relevance += 100
        return relevance

    ranked = sorted(books, key=score, reverse=True)
    if terms:
        matching = [book for book in ranked if score(book) > 0.5]
        if matching:
            ranked = matching

    if book_id and all(book.id != book_id for book in ranked):
        contextual = db.scalar(book_query().where(Book.id == book_id))
        if contextual:
            ranked.insert(0, contextual)
    return ranked[: max(1, min(limit, 12))]


def books_for_provider(books: list[Book]) -> list[dict]:
    return [
        book_to_read(book).model_dump(mode="json", by_alias=True)
        for book in books
    ]

