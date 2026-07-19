import importlib.util
import uuid
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text

from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre


def _register(client, *, email: str, username: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Str0ngPassw0rd!",
            "username": username,
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _book(
    db_session,
    *,
    title: str,
    author_name: str,
    genres: list[Genre],
    pages: int = 200,
    external_rating: float = 0,
    external_review_count: int = 0,
) -> Book:
    author = Author(name=author_name)
    book = Book(
        title=title,
        author=author,
        genres=genres,
        description=f"Description for {title}",
        pages=pages,
        external_rating=external_rating,
        external_review_count=external_review_count,
    )
    db_session.add_all([author, book])
    db_session.commit()
    db_session.refresh(book)
    return book


def test_book_response_lists_all_genres_and_keeps_external_rating(client, db_session):
    headers = _register(
        client, email="ratings@example.com", username="ratings-reader"
    )
    fantasy = Genre(name="Fantasy")
    adventure = Genre(name="Adventure")
    db_session.add_all([fantasy, adventure])
    db_session.flush()
    book = _book(
        db_session,
        title="Two Genres",
        author_name="Rating Author",
        genres=[fantasy, adventure],
        external_rating=4,
        external_review_count=2,
    )

    response = client.post(
        "/api/v1/reviews",
        headers=headers,
        json={"bookId": str(book.id), "rating": 5, "text": "A local review."},
    )
    assert response.status_code == 201, response.text

    book_response = client.get(f"/api/v1/books/{book.id}")
    assert book_response.status_code == 200, book_response.text
    body = book_response.json()
    assert body["genres"] == ["Adventure", "Fantasy"]
    assert body["genre"] == "Adventure"
    assert body["externalRating"] == 4.0
    assert body["externalReviewCount"] == 2
    assert body["localRating"] == 5.0
    assert body["localReviewCount"] == 1
    assert body["reviewCount"] == 3
    assert body["rating"] == 4.3

    db_session.refresh(book)
    assert float(book.external_rating) == 4.0
    assert book.external_review_count == 2
    assert float(book.local_rating) == 5.0
    assert book.local_review_count == 1


def test_library_entry_contract_favorites_and_status_transitions(client, db_session):
    headers = _register(
        client, email="library@example.com", username="library-reader"
    )
    fiction = Genre(name="Library Fiction")
    db_session.add(fiction)
    db_session.flush()
    book = _book(
        db_session,
        title="Progress Book",
        author_name="Progress Author",
        genres=[fiction],
        pages=120,
    )

    added = client.post(
        "/api/v1/library/add",
        headers=headers,
        json={
            "bookId": str(book.id),
            "status": "reading",
            "progressPages": 40,
            "isFavorite": True,
        },
    )
    assert added.status_code == 200, added.text
    entry = added.json()
    assert entry["book"]["id"] == str(book.id)
    assert entry["status"] == "reading"
    assert entry["progressPages"] == 40
    assert entry["isFavorite"] is True
    assert entry["startedAt"] is not None
    assert entry["finishedAt"] is None

    too_far = client.patch(
        f"/api/v1/library/update/{book.id}",
        headers=headers,
        json={"progressPages": 121},
    )
    assert too_far.status_code == 422, too_far.text

    completed = client.patch(
        f"/api/v1/library/update/{book.id}",
        headers=headers,
        json={"status": "read"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["progressPages"] == 120
    assert completed.json()["finishedAt"] is not None

    unfavorited = client.patch(
        f"/api/v1/library/update/{book.id}",
        headers=headers,
        json={"isFavorite": False},
    )
    assert unfavorited.status_code == 200, unfavorited.text
    assert unfavorited.json()["status"] == "read"
    assert unfavorited.json()["isFavorite"] is False

    dropped = client.patch(
        f"/api/v1/library/update/{book.id}",
        headers=headers,
        json={"status": "dropped"},
    )
    assert dropped.status_code == 200, dropped.text
    assert dropped.json()["status"] == "dropped"
    assert dropped.json()["finishedAt"] is None

    reset = client.patch(
        f"/api/v1/library/update/{book.id}",
        headers=headers,
        json={"status": "want-to-read"},
    )
    assert reset.status_code == 200, reset.text
    assert reset.json()["progressPages"] == 0
    assert reset.json()["startedAt"] is None
    assert reset.json()["finishedAt"] is None

    favorites = client.get("/api/v1/library/favorites", headers=headers)
    assert favorites.status_code == 200, favorites.text
    assert favorites.json() == []


def test_personalized_recommendations_use_preferences_and_exclude_library(
    client, db_session
):
    headers = _register(
        client, email="recommend@example.com", username="recommend-reader"
    )
    fiction = Genre(name="Recommendation Fiction")
    history = Genre(name="Recommendation History")
    db_session.add_all([fiction, history])
    db_session.flush()
    owned = _book(
        db_session,
        title="Already Owned",
        author_name="Owned Author",
        genres=[fiction],
        external_rating=5,
        external_review_count=100,
    )
    match = _book(
        db_session,
        title="Preference Match",
        author_name="Match Author",
        genres=[fiction],
        external_rating=4,
        external_review_count=20,
    )
    _book(
        db_session,
        title="Unrelated Bestseller",
        author_name="Other Author",
        genres=[history],
        external_rating=5,
        external_review_count=1000,
    )

    favorite_genre = client.post(
        f"/api/v1/profile/favorite-genres/{fiction.id}", headers=headers
    )
    assert favorite_genre.status_code == 200, favorite_genre.text
    add_owned = client.post(
        "/api/v1/library/add",
        headers=headers,
        json={"bookId": str(owned.id), "status": "read", "isFavorite": True},
    )
    assert add_owned.status_code == 200, add_owned.text

    response = client.get(
        "/api/v1/recommendations/personalized?limit=2", headers=headers
    )
    assert response.status_code == 200, response.text
    recommendations = response.json()
    assert all(item["id"] != str(owned.id) for item in recommendations)
    assert recommendations[0]["id"] == str(match.id)
    assert recommendations[0]["recommendationReason"] == (
        "Matches your favorite genre: Recommendation Fiction"
    )


def test_migration_separates_legacy_local_ratings_and_favorite(test_engine):
    schema = f"domain_migration_{uuid.uuid4().hex}"
    migration_path = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "9c3d5e7f1a2b_split_ratings_and_library_favorites.py"
    )
    spec = importlib.util.spec_from_file_location("domain_data_migration", migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    book_id = uuid.uuid4()
    external_book_id = uuid.uuid4()
    entry_id = uuid.uuid4()
    with test_engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        connection.exec_driver_sql(f'SET search_path TO "{schema}"')
        try:
            connection.exec_driver_sql(
                "CREATE TYPE readingstatus AS ENUM "
                "('reading', 'want-to-read', 'read', 'favorite')"
            )
            connection.exec_driver_sql(
                """
                CREATE TABLE books (
                    id UUID PRIMARY KEY,
                    pages INTEGER,
                    published_year INTEGER,
                    average_rating NUMERIC(3, 2) NOT NULL,
                    review_count INTEGER NOT NULL
                )
                """
            )
            connection.exec_driver_sql(
                """
                CREATE TABLE user_books (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL,
                    book_id UUID NOT NULL,
                    status readingstatus NOT NULL,
                    progress_pages INTEGER NOT NULL
                )
                """
            )
            connection.exec_driver_sql(
                """
                CREATE TABLE reviews (
                    id UUID PRIMARY KEY,
                    book_id UUID NOT NULL,
                    rating INTEGER NOT NULL,
                    helpful INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.execute(
                text(
                    "INSERT INTO books "
                    "(id, pages, published_year, average_rating, review_count) "
                    "VALUES (:id, 300, 2020, 5, 1)"
                ),
                {"id": book_id},
            )
            connection.execute(
                text(
                    "INSERT INTO books "
                    "(id, pages, published_year, average_rating, review_count) "
                    "VALUES (:id, 240, 2019, 4.25, 123)"
                ),
                {"id": external_book_id},
            )
            connection.execute(
                text(
                    "INSERT INTO user_books "
                    "(id, user_id, book_id, status, progress_pages) "
                    "VALUES (:id, :user_id, :book_id, 'favorite', 0)"
                ),
                {"id": entry_id, "user_id": uuid.uuid4(), "book_id": book_id},
            )
            connection.execute(
                text(
                    "INSERT INTO reviews "
                    "(id, book_id, rating, helpful, created_at) "
                    "VALUES (:id, :book_id, 5, 0, NOW())"
                ),
                {"id": uuid.uuid4(), "book_id": book_id},
            )

            original_op = migration.op
            migration.op = Operations(MigrationContext.configure(connection))
            try:
                migration.upgrade()
            finally:
                migration.op = original_op

            rating_row = connection.execute(
                text(
                    "SELECT external_rating, external_review_count, "
                    "local_rating, local_review_count FROM books WHERE id = :id"
                ),
                {"id": book_id},
            ).one()
            assert float(rating_row.external_rating) == 0
            assert rating_row.external_review_count == 0
            assert float(rating_row.local_rating) == 5.0
            assert rating_row.local_review_count == 1

            external_row = connection.execute(
                text(
                    "SELECT external_rating, external_review_count, "
                    "local_rating, local_review_count FROM books WHERE id = :id"
                ),
                {"id": external_book_id},
            ).one()
            assert float(external_row.external_rating) == 4.25
            assert external_row.external_review_count == 123
            assert float(external_row.local_rating) == 0
            assert external_row.local_review_count == 0

            library_row = connection.execute(
                text(
                    "SELECT status::text, is_favorite "
                    "FROM user_books WHERE id = :id"
                ),
                {"id": entry_id},
            ).one()
            assert library_row[0] == "want-to-read"
            assert library_row.is_favorite is True

            original_op = migration.op
            migration.op = Operations(MigrationContext.configure(connection))
            try:
                migration.downgrade()
            finally:
                migration.op = original_op

            legacy_rating = connection.execute(
                text(
                    "SELECT average_rating, review_count "
                    "FROM books WHERE id = :id"
                ),
                {"id": book_id},
            ).one()
            assert float(legacy_rating.average_rating) == 5
            assert legacy_rating.review_count == 1
            legacy_status = connection.execute(
                text("SELECT status::text FROM user_books WHERE id = :id"),
                {"id": entry_id},
            ).scalar_one()
            assert legacy_status == "favorite"
        finally:
            connection.exec_driver_sql("SET search_path TO public")
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
