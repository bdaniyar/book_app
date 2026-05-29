from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre


def _register(client) -> str:
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "reader@example.com",
            "password": "Str0ngPassw0rd!",
            "username": "reader",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _seed_book(db_session) -> Book:
    author = Author(name="Test Author")
    genre = Genre(name="Fiction")
    book = Book(
        title="Test Book",
        author=author,
        description="A testable book.",
        isbn="9780000000000",
        pages=320,
        published_year=2026,
        cover_url="/placeholder.svg",
    )
    book.genres = [genre]
    db_session.add_all([author, genre, book])
    db_session.commit()
    db_session.refresh(book)
    return book


def test_books_library_reviews_and_profile_stats(client, db_session):
    access = _register(client)
    headers = {"Authorization": f"Bearer {access}"}
    book = _seed_book(db_session)

    r_books = client.get("/api/v1/books")
    assert r_books.status_code == 200, r_books.text
    assert r_books.json()[0]["title"] == "Test Book"
    assert r_books.json()[0]["coverUrl"] == "/placeholder.svg"

    r_add = client.post(
        "/api/v1/library/add",
        json={"bookId": str(book.id), "status": "read"},
        headers=headers,
    )
    assert r_add.status_code == 200, r_add.text

    r_review = client.post(
        "/api/v1/reviews",
        json={"bookId": str(book.id), "rating": 5, "text": "Excellent."},
        headers=headers,
    )
    assert r_review.status_code == 201, r_review.text
    assert r_review.json()["userName"] == "reader"

    r_review_list = client.get(f"/api/v1/reviews/book/{book.id}")
    assert r_review_list.status_code == 200, r_review_list.text
    assert r_review_list.json()[0]["rating"] == 5

    r_stats = client.get("/api/v1/profile/stats", headers=headers)
    assert r_stats.status_code == 200, r_stats.text
    assert r_stats.json()["booksRead"] == 1
    assert r_stats.json()["reviewsWritten"] == 1
