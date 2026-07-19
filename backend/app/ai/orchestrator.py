from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.policy import requested_action, requests_write, user_uses_cyrillic
from app.ai.provider import generate_with_fallback
from app.ai.tools.catalog import books_for_provider, search_catalog
from app.ai.tools.profile import get_user_taste
from app.models.assistant import (
    AssistantAction,
    AssistantConversation,
    AssistantMessage,
)
from app.models.book import Book
from app.models.user import User
from app.models.user_book import ReadingStatus
from app.schemas.assistant import (
    AssistantCitation,
    AssistantMessageHistoryRead,
    AssistantMessageRead,
    AssistantReply,
    ProposedActionRead,
)
from app.services.books import book_query, book_to_read


class AssistantNotFoundError(LookupError):
    pass


class AssistantRateLimitError(RuntimeError):
    pass


class AssistantActionError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_conversation(
    db: Session, *, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> AssistantConversation:
    conversation = db.scalar(
        select(AssistantConversation).where(
            AssistantConversation.id == conversation_id,
            AssistantConversation.user_id == user_id,
        )
    )
    if not conversation:
        raise AssistantNotFoundError("Conversation not found")
    return conversation


def list_messages(
    db: Session, *, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> list[AssistantMessageHistoryRead]:
    get_conversation(db, conversation_id=conversation_id, user_id=user_id)
    messages = list(
        db.scalars(
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == conversation_id)
            .order_by(AssistantMessage.created_at.asc(), AssistantMessage.id.asc())
        ).all()
    )
    raw_book_ids = {
        book_id
        for message in messages
        for book_id in (message.book_ids or [])
    }
    valid_book_ids: set[uuid.UUID] = set()
    for raw_book_id in raw_book_ids:
        try:
            valid_book_ids.add(uuid.UUID(str(raw_book_id)))
        except (TypeError, ValueError, AttributeError):
            continue
    books = (
        list(
            db.scalars(book_query().where(Book.id.in_(valid_book_ids)))
            .unique()
            .all()
        )
        if valid_book_ids
        else []
    )
    books_by_id = {str(book.id): book for book in books}
    actions = list(
        db.scalars(
            select(AssistantAction)
            .where(AssistantAction.conversation_id == conversation_id)
            .order_by(AssistantAction.created_at.asc(), AssistantAction.id.asc())
        ).all()
    )

    actions_by_message: dict[uuid.UUID, list[AssistantAction]] = {}
    for action in actions:
        if action.assistant_message_id is not None:
            actions_by_message.setdefault(action.assistant_message_id, []).append(
                action
            )

    result: list[AssistantMessageHistoryRead] = []
    for message in messages:
        message_books = [
            books_by_id[book_id]
            for book_id in (message.book_ids or [])
            if book_id in books_by_id
        ]
        message_actions = actions_by_message.get(message.id, [])
        result.append(
            AssistantMessageHistoryRead(
                **AssistantMessageRead.model_validate(message).model_dump(),
                books=[book_to_read(book) for book in message_books],
                citations=[
                    AssistantCitation(
                        book_id=book.id,
                        fields=[
                            "title",
                            "author",
                            "genres",
                            "rating",
                            "pages",
                            "publishedYear",
                        ],
                    )
                    for book in message_books
                ],
                proposed_actions=[
                    ProposedActionRead(
                        id=action.id,
                        type=action.action_type,
                        payload=action.payload,
                        status=action.status,
                        expires_at=action.expires_at,
                    )
                    for action in message_actions
                ],
            )
        )
    return result


def delete_conversation(
    db: Session, *, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    conversation = get_conversation(
        db, conversation_id=conversation_id, user_id=user_id
    )
    db.delete(conversation)
    db.commit()


def _enforce_rate_limit(db: Session, user_id: uuid.UUID) -> None:
    since = utcnow() - timedelta(minutes=1)
    count = db.scalar(
        select(func.count(AssistantMessage.id))
        .join(
            AssistantConversation,
            AssistantConversation.id == AssistantMessage.conversation_id,
        )
        .where(
            AssistantConversation.user_id == user_id,
            AssistantMessage.role == "user",
            AssistantMessage.created_at >= since,
        )
    )
    if int(count or 0) >= 20:
        raise AssistantRateLimitError("Too many assistant messages; try again later")


def _propose_action(
    db: Session,
    *,
    conversation: AssistantConversation,
    user_message: AssistantMessage,
    message: str,
    books: list[Book],
    book_id: uuid.UUID | None,
) -> AssistantAction | None:
    if not requests_write(message) or not books:
        return None
    normalized_message = re.sub(r"[^\w]+", " ", message.casefold()).strip()
    if book_id:
        target_book = next((book for book in books if book.id == book_id), None)
    else:
        # Never mutate a high-ranked but unintended book. Without explicit page
        # context, the full catalog title must be present in the user's message.
        target_book = next(
            (
                book
                for book in books
                if re.sub(r"[^\w]+", " ", book.title.casefold()).strip()
                in normalized_message
            ),
            None,
        )
    if target_book is None:
        return None
    action_type, payload = requested_action(message)
    payload = {"bookId": str(target_book.id), **payload}
    digest_source = json.dumps(
        {
            "conversation": str(conversation.id),
            "message": str(user_message.id),
            "type": action_type,
            "payload": payload,
        },
        sort_keys=True,
    )
    action = AssistantAction(
        conversation_id=conversation.id,
        user_id=conversation.user_id,
        action_type=action_type,
        payload=payload,
        status="pending",
        idempotency_key=hashlib.sha256(digest_source.encode()).hexdigest(),
        expires_at=utcnow() + timedelta(minutes=15),
    )
    db.add(action)
    db.flush()
    return action


def send_message(
    db: Session,
    *,
    conversation_id: uuid.UUID,
    user: User,
    message: str,
    book_id: uuid.UUID | None,
) -> AssistantReply:
    conversation = get_conversation(
        db, conversation_id=conversation_id, user_id=user.id
    )
    _enforce_rate_limit(db, user.id)

    user_message = AssistantMessage(
        conversation_id=conversation.id,
        role="user",
        content=message,
        book_ids=[str(book_id)] if book_id else [],
    )
    db.add(user_message)
    if conversation.title == "New conversation":
        conversation.title = message[:117] + ("..." if len(message) > 117 else "")
    conversation.updated_at = utcnow()
    db.add(conversation)
    db.commit()
    db.refresh(user_message)

    history_rows = db.scalars(
        select(AssistantMessage)
        .where(AssistantMessage.conversation_id == conversation.id)
        .order_by(AssistantMessage.created_at.desc())
        .limit(10)
    ).all()
    history = [
        {"role": row.role, "content": row.content}
        for row in reversed(list(history_rows))
    ]
    books = search_catalog(
        db, message=message, user_id=user.id, book_id=book_id, limit=8
    )
    profile = get_user_taste(db, user=user)
    action = _propose_action(
        db,
        conversation=conversation,
        user_message=user_message,
        message=message,
        books=books,
        book_id=book_id,
    )
    if action:
        db.commit()
        db.refresh(action)

    provider_books = books_for_provider(books)
    answer = generate_with_fallback(
        message=message,
        history=history,
        books=provider_books,
        profile=profile,
    )
    if action:
        answer += (
            "\n\nЯ подготовил действие. Проверьте книгу и нажмите «Подтвердить» — до этого данные не изменятся."
            if user_uses_cyrillic(message)
            else "\n\nI prepared an action. Check the book and press Confirm; nothing changes before confirmation."
        )

    assistant_message = AssistantMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        book_ids=[str(book.id) for book in books],
    )
    if action:
        action.assistant_message = assistant_message
        db.add(action)
    conversation.updated_at = utcnow()
    db.add_all([assistant_message, conversation])
    db.commit()
    db.refresh(assistant_message)

    citations = [
        AssistantCitation(
            book_id=book.id,
            fields=["title", "author", "genres", "rating", "pages", "publishedYear"],
        )
        for book in books
    ]
    actions = []
    if action:
        actions.append(
            ProposedActionRead(
                id=action.id,
                type=action.action_type,
                payload=action.payload,
                status=action.status,
                expires_at=action.expires_at,
            )
        )
    return AssistantReply(
        conversation_id=conversation.id,
        message=AssistantMessageRead.model_validate(assistant_message),
        books=[book_to_read(book) for book in books],
        citations=citations,
        proposed_actions=actions,
    )


def _get_action_for_update(
    db: Session, *, action_id: uuid.UUID, user_id: uuid.UUID
) -> AssistantAction:
    action = db.scalar(
        select(AssistantAction)
        .where(
            AssistantAction.id == action_id,
            AssistantAction.user_id == user_id,
        )
        .with_for_update()
    )
    if not action:
        raise AssistantNotFoundError("Assistant action not found")
    return action


def reject_action(
    db: Session, *, action_id: uuid.UUID, user_id: uuid.UUID
) -> AssistantAction:
    action = _get_action_for_update(db, action_id=action_id, user_id=user_id)
    if action.status == "pending" and action.expires_at <= utcnow():
        action.status = "expired"
    elif action.status == "pending":
        action.status = "rejected"
    elif action.status == "executed":
        raise AssistantActionError("An executed action cannot be rejected")
    db.add(action)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(action)
    return action


def confirm_action(
    db: Session, *, action_id: uuid.UUID, user_id: uuid.UUID
) -> AssistantAction:
    action = _get_action_for_update(db, action_id=action_id, user_id=user_id)
    if action.status == "executed":
        return action
    if action.status != "pending":
        raise AssistantActionError(f"Action is already {action.status}")
    if action.expires_at <= utcnow():
        action.status = "expired"
        db.add(action)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(action)
        return action

    try:
        book_id = uuid.UUID(str(action.payload["bookId"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise AssistantActionError("Invalid action payload") from exc
    book = db.get(Book, book_id)
    if not book:
        raise AssistantActionError("Book no longer exists")

    from app.services.library import (
        add_or_update_library_entry,
        get_library_entry,
        update_library_entry,
    )

    entry = get_library_entry(db, user_id=user_id, book_id=book_id)
    if action.action_type == "set_library_status":
        try:
            status = ReadingStatus(str(action.payload["status"]))
        except (KeyError, ValueError) as exc:
            raise AssistantActionError("Invalid reading status") from exc
        if entry:
            entry = update_library_entry(
                db, entry=entry, status=status, commit=False
            )
        else:
            entry = add_or_update_library_entry(
                db,
                user_id=user_id,
                book=book,
                status=status,
                commit=False,
            )
    elif action.action_type == "set_favorite":
        is_favorite = bool(action.payload.get("isFavorite", True))
        if entry:
            entry = update_library_entry(
                db,
                entry=entry,
                is_favorite=is_favorite,
                commit=False,
            )
        else:
            entry = add_or_update_library_entry(
                db,
                user_id=user_id,
                book=book,
                status=ReadingStatus.want_to_read,
                is_favorite=is_favorite,
                commit=False,
            )
    else:
        raise AssistantActionError("Unsupported assistant action")

    action.status = "executed"
    action.executed_at = utcnow()
    action.result = {
        "libraryEntryId": str(entry.id),
        "bookId": str(entry.book_id),
        "status": entry.status.value,
        "isFavorite": bool(entry.is_favorite),
    }
    db.add(action)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(action)
    return action
