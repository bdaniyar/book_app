import uuid

import pytest
from sqlalchemy import event

from app.models.author import Author
from app.models.assistant import AssistantAction
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


def _seed_catalog(db_session) -> Book:
    author = Author(name="AI Test Author")
    genre = Genre(name="Science Fiction")
    book = Book(
        title="AI Test Book",
        author=author,
        description="A grounded catalog description about a journey through space.",
        pages=280,
        published_year=2024,
    )
    book.genres = [genre]
    db_session.add_all([author, genre, book])
    db_session.commit()
    db_session.refresh(book)
    return book


def test_assistant_grounded_chat_and_confirmed_action(client, db_session, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "AI_PROVIDER", "local", raising=False)
    headers = _register(client, email="ai@example.com", username="ai-reader")
    book = _seed_catalog(db_session)

    created = client.post(
        "/api/v1/assistant/conversations",
        json={"title": "My librarian"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    conversation_id = created.json()["id"]

    reply = client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        json={
            "message": "Добавь эту книгу в хочу прочитать",
            "bookId": str(book.id),
        },
        headers=headers,
    )
    assert reply.status_code == 200, reply.text
    body = reply.json()
    assert body["books"][0]["id"] == str(book.id)
    assert body["citations"][0]["bookId"] == str(book.id)
    assert body["proposedActions"][0]["status"] == "pending"

    action_id = body["proposedActions"][0]["id"]
    action_row = db_session.get(AssistantAction, uuid.UUID(action_id))
    assert action_row is not None
    assert str(action_row.assistant_message_id) == body["message"]["id"]
    history = client.get(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        headers=headers,
    )
    assert history.status_code == 200, history.text
    persisted_reply = history.json()[-1]
    assert persisted_reply["books"][0]["id"] == str(book.id)
    assert persisted_reply["citations"][0]["bookId"] == str(book.id)
    assert persisted_reply["proposedActions"][0]["id"] == action_id

    def fail_commit(_session):
        raise RuntimeError("simulated transaction failure")

    event.listen(db_session, "before_commit", fail_commit)
    try:
        with pytest.raises(RuntimeError, match="simulated transaction failure"):
            client.post(
                f"/api/v1/assistant/actions/{action_id}/confirm",
                headers=headers,
            )
    finally:
        event.remove(db_session, "before_commit", fail_commit)

    # The library write and action status share one transaction: neither side
    # can survive a failed commit.
    library_after_failure = client.get("/api/v1/library", headers=headers)
    assert library_after_failure.status_code == 200
    assert library_after_failure.json() == []
    history_after_failure = client.get(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        headers=headers,
    ).json()
    assert history_after_failure[-1]["proposedActions"][0]["status"] == "pending"

    confirmed = client.post(
        f"/api/v1/assistant/actions/{action_id}/confirm", headers=headers
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "executed"

    library = client.get("/api/v1/library", headers=headers)
    assert library.status_code == 200, library.text
    assert library.json()[0]["book"]["id"] == str(book.id)
    assert library.json()[0]["status"] == "want-to-read"

    confirmed_again = client.post(
        f"/api/v1/assistant/actions/{action_id}/confirm", headers=headers
    )
    assert confirmed_again.status_code == 200
    assert confirmed_again.json()["status"] == "executed"

    refreshed_history = client.get(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        headers=headers,
    ).json()
    assert refreshed_history[-1]["proposedActions"][0]["status"] == "executed"


def test_assistant_conversations_are_private(client):
    first = _register(client, email="one-ai@example.com", username="one-ai")
    conversation = client.post(
        "/api/v1/assistant/conversations", json={}, headers=first
    ).json()

    client.post("/api/v1/auth/logout", headers=first)
    second = _register(client, email="two-ai@example.com", username="two-ai")
    response = client.get(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages",
        headers=second,
    )
    assert response.status_code == 404
