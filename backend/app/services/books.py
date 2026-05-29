import uuid
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.schemas.book import BookCreateRequest, BookRead, BookUpdateRequest


def book_to_read(book: Book) -> BookRead:
    primary_genre = book.genres[0].name if book.genres else "Uncategorized"
    rating = float(book.average_rating or 0)
    return BookRead(
        id=book.id,
        title=book.title,
        author=book.author.name if book.author else "Unknown Author",
        cover_url=book.cover_url,
        rating=round(rating, 1),
        review_count=book.review_count,
        description=book.description,
        genre=primary_genre,
        published_year=book.published_year,
        pages=book.pages,
        isbn=book.isbn,
    )


def book_query():
    return select(Book).options(
        selectinload(Book.author),
        selectinload(Book.genres),
    )


def get_or_create_author(db: Session, name: str) -> Author:
    clean_name = name.strip()
    author = db.scalar(select(Author).where(Author.name == clean_name))
    if author:
        return author
    author = Author(name=clean_name)
    db.add(author)
    db.flush()
    return author


def resolve_genres(db: Session, genre_ids: list[uuid.UUID]) -> list[Genre]:
    if not genre_ids:
        return []
    genres = db.scalars(select(Genre).where(Genre.id.in_(genre_ids))).all()
    if len(genres) != len(set(genre_ids)):
        raise ValueError("One or more genres not found")
    return list(genres)


def create_book(db: Session, payload: BookCreateRequest) -> Book:
    author = get_or_create_author(db, payload.author)
    book = Book(
        title=payload.title.strip(),
        author=author,
        description=payload.description or "",
        isbn=payload.isbn,
        cover_url=payload.cover_url,
        pages=payload.pages,
        published_year=payload.published_year,
    )
    book.genres = resolve_genres(db, payload.genre_ids)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book: Book, payload: BookUpdateRequest) -> Book:
    if payload.title is not None:
        book.title = payload.title.strip()
    if payload.author is not None:
        book.author = get_or_create_author(db, payload.author)
    if payload.description is not None:
        book.description = payload.description
    if payload.isbn is not None:
        book.isbn = payload.isbn
    if payload.cover_url is not None:
        book.cover_url = payload.cover_url
    if payload.pages is not None:
        book.pages = payload.pages
    if payload.published_year is not None:
        book.published_year = payload.published_year
    if payload.genre_ids is not None:
        book.genres = resolve_genres(db, payload.genre_ids)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def list_books(
    db: Session,
    *,
    q: str | None = None,
    category: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> list[Book]:
    stmt = book_query()
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.join(Book.author, isouter=True).where(
            or_(Book.title.ilike(term), Author.name.ilike(term), Book.isbn.ilike(term))
        )
    if category:
        clean_category = category.replace("-", " ").strip()
        stmt = stmt.join(Book.genres).where(Genre.name.ilike(clean_category))
    stmt = stmt.order_by(Book.created_at.desc()).offset((page - 1) * limit).limit(limit)
    return list(db.scalars(stmt).unique().all())


def recalculate_book_rating(db: Session, book_id: uuid.UUID) -> None:
    count, avg = db.execute(
        select(func.count(Review.id), func.avg(Review.rating)).where(Review.book_id == book_id)
    ).one()
    book = db.get(Book, book_id)
    if not book:
        return
    book.review_count = int(count or 0)
    book.average_rating = Decimal(str(round(float(avg or 0), 2)))
    db.add(book)
