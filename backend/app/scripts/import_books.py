from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre


OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"


@dataclass
class ImportStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def clean_isbn(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    return "".join(ch for ch in text if ch.isdigit() or ch.upper() == "X")[:32] or None


def clean_int(value: Any) -> int | None:
    text = clean_text(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def clean_rating(value: Any) -> Decimal:
    text = clean_text(value)
    if not text:
        return Decimal("0")
    try:
        rating = max(0, min(float(text), 9.99))
        return Decimal(str(round(rating, 2)))
    except ValueError:
        return Decimal("0")


def get_or_create_author(db: Session, name: str) -> Author:
    clean_name = name.strip() or "Unknown Author"
    author = db.scalar(select(Author).where(Author.name == clean_name))
    if author:
        return author
    author = Author(name=clean_name)
    db.add(author)
    db.flush()
    return author


def get_or_create_genre(db: Session, name: str) -> Genre:
    clean_name = name.strip() or "Imported"
    genre = db.scalar(select(Genre).where(Genre.name == clean_name))
    if genre:
        return genre
    genre = Genre(name=clean_name)
    db.add(genre)
    db.flush()
    return genre


def find_existing_book(
    db: Session,
    *,
    isbn: str | None,
    external_source: str | None,
    external_id: str | None,
    title: str,
    author_name: str,
) -> Book | None:
    if external_source and external_id:
        book = db.scalar(
            select(Book).where(
                Book.external_source == external_source,
                Book.external_id == external_id,
            )
        )
        if book:
            return book
    if isbn:
        book = db.scalar(select(Book).where(Book.isbn == isbn))
        if book:
            return book
    author = db.scalar(select(Author).where(Author.name == author_name))
    if author:
        return db.scalar(select(Book).where(Book.title == title, Book.author_id == author.id))
    return None


def upsert_book(
    db: Session,
    *,
    title: str,
    author_name: str,
    genre_names: list[str],
    description: str,
    isbn: str | None,
    cover_url: str | None,
    pages: int | None,
    published_year: int | None,
    average_rating: Decimal,
    review_count: int,
    external_source: str,
    external_id: str,
    update_existing: bool,
) -> str:
    author = get_or_create_author(db, author_name)
    existing = find_existing_book(
        db,
        isbn=isbn,
        external_source=external_source,
        external_id=external_id,
        title=title,
        author_name=author.name,
    )
    genres = [get_or_create_genre(db, name) for name in genre_names if name.strip()]

    if existing:
        if not update_existing:
            return "skipped"
        existing.title = title
        existing.author = author
        existing.description = description
        existing.isbn = isbn or existing.isbn
        existing.cover_url = cover_url or existing.cover_url
        existing.pages = pages or existing.pages
        existing.published_year = published_year or existing.published_year
        existing.average_rating = average_rating
        existing.review_count = review_count
        existing.external_source = external_source
        existing.external_id = external_id
        if genres:
            existing.genres = genres
        db.add(existing)
        return "updated"

    book = Book(
        title=title,
        author=author,
        description=description,
        isbn=isbn,
        cover_url=cover_url,
        pages=pages,
        published_year=published_year,
        average_rating=average_rating,
        review_count=review_count,
        external_source=external_source,
        external_id=external_id,
    )
    book.genres = genres
    db.add(book)
    return "created"


def apply_result(stats: ImportStats, result: str) -> None:
    if result == "created":
        stats.created += 1
    elif result == "updated":
        stats.updated += 1
    else:
        stats.skipped += 1


def fetch_open_library(subject: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "subject": subject,
        "limit": limit,
        "fields": ",".join(
            [
                "key",
                "title",
                "author_name",
                "isbn",
                "cover_i",
                "first_publish_year",
                "number_of_pages_median",
                "ratings_average",
                "ratings_count",
                "first_sentence",
            ]
        ),
    }
    url = f"{OPEN_LIBRARY_SEARCH_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "book_app_importer/1.0"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return list(payload.get("docs") or [])


def first_sentence(value: Any) -> str:
    if isinstance(value, list) and value:
        return clean_text(value[0]) or ""
    if isinstance(value, dict):
        return clean_text(value.get("value")) or ""
    return clean_text(value) or ""


def import_open_library(args: argparse.Namespace) -> ImportStats:
    stats = ImportStats()
    db = SessionLocal()
    try:
        for subject in args.subject:
            docs = fetch_open_library(subject, args.limit)
            genre_name = args.genre or subject.replace("_", " ").replace("-", " ").title()
            for doc in docs:
                title = clean_text(doc.get("title"))
                authors = doc.get("author_name") or []
                author_name = clean_text(authors[0] if authors else None)
                external_id = clean_text(doc.get("key"))
                if not title or not author_name or not external_id:
                    stats.skipped += 1
                    continue

                isbns = doc.get("isbn") or []
                cover_id = doc.get("cover_i")
                result = upsert_book(
                    db,
                    title=title[:255],
                    author_name=author_name[:255],
                    genre_names=[genre_name],
                    description=first_sentence(doc.get("first_sentence")),
                    isbn=clean_isbn(isbns[0] if isbns else None),
                    cover_url=OPEN_LIBRARY_COVER_URL.format(cover_id=cover_id) if cover_id else None,
                    pages=clean_int(doc.get("number_of_pages_median")),
                    published_year=clean_int(doc.get("first_publish_year")),
                    average_rating=clean_rating(doc.get("ratings_average")),
                    review_count=clean_int(doc.get("ratings_count")) or 0,
                    external_source="openlibrary",
                    external_id=external_id,
                    update_existing=args.update_existing,
                )
                apply_result(stats, result)
            db.commit()
            if args.sleep:
                time.sleep(args.sleep)
    finally:
        db.close()
    return stats


def import_goodreads_csv(args: argparse.Namespace) -> ImportStats:
    stats = ImportStats()
    csv_path = Path(args.path)
    db = SessionLocal()
    try:
        with csv_path.open(newline="", encoding=args.encoding) as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader):
                if args.limit and index >= args.limit:
                    break

                title = clean_text(row.get("title") or row.get("original_title"))
                author_name = clean_text(row.get("authors") or row.get("author") or row.get("author_name"))
                external_id = clean_text(row.get("book_id") or row.get("goodreads_book_id") or row.get("id"))
                if not title or not author_name or not external_id:
                    stats.skipped += 1
                    continue

                isbn = clean_isbn(row.get("isbn13") or row.get("isbn"))
                result = upsert_book(
                    db,
                    title=title[:255],
                    author_name=author_name.split(",")[0].strip()[:255],
                    genre_names=[args.genre],
                    description=clean_text(row.get("description")) or "",
                    isbn=isbn,
                    cover_url=clean_text(row.get("image_url") or row.get("cover_url") or row.get("small_image_url")),
                    pages=clean_int(row.get("num_pages") or row.get("pages")),
                    published_year=clean_int(row.get("original_publication_year") or row.get("published_year")),
                    average_rating=clean_rating(row.get("average_rating") or row.get("rating")),
                    review_count=clean_int(row.get("ratings_count") or row.get("work_ratings_count")) or 0,
                    external_source=args.source,
                    external_id=external_id,
                    update_existing=args.update_existing,
                )
                apply_result(stats, result)
        db.commit()
    finally:
        db.close()
    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import open book datasets into book_app.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    openlibrary = subparsers.add_parser("openlibrary", help="Import books from Open Library Search API.")
    openlibrary.add_argument("--subject", action="append", required=True, help="Open Library subject, e.g. fiction.")
    openlibrary.add_argument("--limit", type=int, default=50, help="Books per subject.")
    openlibrary.add_argument("--genre", default=None, help="Override genre name for imported books.")
    openlibrary.add_argument("--sleep", type=float, default=0.5, help="Delay between subject requests.")
    openlibrary.add_argument("--update-existing", action="store_true")
    openlibrary.set_defaults(func=import_open_library)

    csv_parser = subparsers.add_parser("goodreads-csv", help="Import a Goodreads/Goodbooks books.csv file.")
    csv_parser.add_argument("path", help="Path to books.csv.")
    csv_parser.add_argument("--limit", type=int, default=None)
    csv_parser.add_argument("--genre", default="Imported")
    csv_parser.add_argument("--source", default="goodreads")
    csv_parser.add_argument("--encoding", default="utf-8")
    csv_parser.add_argument("--update-existing", action="store_true")
    csv_parser.set_defaults(func=import_goodreads_csv)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    stats = args.func(args)
    print(
        f"Import finished: created={stats.created}, "
        f"updated={stats.updated}, skipped={stats.skipped}"
    )


if __name__ == "__main__":
    main()
