from __future__ import annotations

from app.db.session import SessionLocal
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre


BOOKS = [
    {
        "title": "The Midnight Library",
        "author": "Matt Haig",
        "cover_url": "/midnight-library-cover.png",
        "rating": 4.5,
        "review_count": 12453,
        "description": "Between life and death there is a library, and within that library, the shelves go on forever.",
        "genre": "Fiction",
        "published_year": 2020,
        "pages": 304,
        "isbn": "9780525559474",
    },
    {
        "title": "Project Hail Mary",
        "author": "Andy Weir",
        "cover_url": "/project-hail-mary-cover.png",
        "rating": 4.7,
        "review_count": 18920,
        "description": "A lone astronaut must save the earth from disaster in this science-based thriller.",
        "genre": "Science Fiction",
        "published_year": 2021,
        "pages": 496,
        "isbn": "9780593135204",
    },
    {
        "title": "The Seven Husbands of Evelyn Hugo",
        "author": "Taylor Jenkins Reid",
        "cover_url": "/the-seven-husbands-of-evelyn-hugo-book-cover.jpg",
        "rating": 4.6,
        "review_count": 25678,
        "description": "A reclusive Hollywood icon tells the truth about her glamorous and scandalous life.",
        "genre": "Fiction",
        "published_year": 2017,
        "pages": 400,
        "isbn": "9781501161933",
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "cover_url": "/atomic-habits-inspired-cover.png",
        "rating": 4.8,
        "review_count": 34521,
        "description": "A practical guide to building good habits and breaking bad ones.",
        "genre": "Self-Help",
        "published_year": 2018,
        "pages": 320,
        "isbn": "9780735211292",
    },
    {
        "title": "The Silent Patient",
        "author": "Alex Michaelides",
        "cover_url": "/the-silent-patient-book-cover.jpg",
        "rating": 4.4,
        "review_count": 19834,
        "description": "A woman shoots her husband and then never speaks another word.",
        "genre": "Mystery",
        "published_year": 2019,
        "pages": 336,
        "isbn": "9781250301697",
    },
    {
        "title": "Where the Crawdads Sing",
        "author": "Delia Owens",
        "cover_url": "/where-the-crawdads-sing-book-cover.jpg",
        "rating": 4.5,
        "review_count": 28945,
        "description": "A mystery and coming-of-age story set on the North Carolina coast.",
        "genre": "Fiction",
        "published_year": 2018,
        "pages": 384,
        "isbn": "9780735219090",
    },
    {
        "title": "The Song of Achilles",
        "author": "Madeline Miller",
        "cover_url": "/the-song-of-achilles-book-cover.jpg",
        "rating": 4.6,
        "review_count": 15234,
        "description": "A retelling of Achilles and Patroclus with mythic sweep and human tenderness.",
        "genre": "Fantasy",
        "published_year": 2011,
        "pages": 352,
        "isbn": "9780062060624",
    },
    {
        "title": "Educated",
        "author": "Tara Westover",
        "cover_url": "/educated-memoir-book-cover.jpg",
        "rating": 4.7,
        "review_count": 22156,
        "description": "A memoir about education, family, and self-invention.",
        "genre": "Biography",
        "published_year": 2018,
        "pages": 352,
        "isbn": "9780399590504",
    },
]


def get_or_create_author(db, name: str) -> Author:
    author = db.query(Author).filter(Author.name == name).first()
    if author:
        return author
    author = Author(name=name)
    db.add(author)
    db.flush()
    return author


def get_or_create_genre(db, name: str) -> Genre:
    genre = db.query(Genre).filter(Genre.name == name).first()
    if genre:
        return genre
    genre = Genre(name=name)
    db.add(genre)
    db.flush()
    return genre


def main() -> None:
    db = SessionLocal()
    try:
        for item in BOOKS:
            existing = db.query(Book).filter(Book.isbn == item["isbn"]).first()
            if existing:
                continue
            author = get_or_create_author(db, item["author"])
            genre = get_or_create_genre(db, item["genre"])
            book = Book(
                title=item["title"],
                author=author,
                cover_url=item["cover_url"],
                average_rating=item["rating"],
                review_count=item["review_count"],
                description=item["description"],
                published_year=item["published_year"],
                pages=item["pages"],
                isbn=item["isbn"],
            )
            book.genres = [genre]
            db.add(book)
        db.commit()
        print("Seeded books and genres.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
