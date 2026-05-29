from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.author import Author
from app.schemas.book import BookRead
from app.services.books import book_to_read, list_books

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/books", response_model=list[BookRead])
def search_books(
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    return [book_to_read(book) for book in list_books(db, q=q, limit=limit)]


@router.get("/authors")
def search_authors(
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    term = f"%{q.strip()}%"
    authors = db.scalars(
        select(Author).where(Author.name.ilike(term)).order_by(Author.name.asc()).limit(limit)
    ).all()
    return [{"id": str(author.id), "name": author.name} for author in authors]


@router.get("/advanced", response_model=list[BookRead])
def advanced_search(
    q: str = Query(default=""),
    genre: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BookRead]:
    return [book_to_read(book) for book in list_books(db, q=q, category=genre, limit=limit)]
