import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.orchestrator import (
    AssistantActionError,
    AssistantNotFoundError,
    AssistantRateLimitError,
    confirm_action,
    delete_conversation,
    list_messages,
    reject_action,
    send_message,
)
from app.ai.provider import provider_status
from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.assistant import AssistantConversation
from app.models.user import User
from app.schemas.assistant import (
    ActionResultRead,
    AssistantMessageCreateRequest,
    AssistantMessageHistoryRead,
    AssistantMessageRead,
    AssistantReply,
    AssistantStatusRead,
    ConversationCreateRequest,
    ConversationRead,
)


router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/status", response_model=AssistantStatusRead)
def get_assistant_status(
    _: User = Depends(get_current_user),
) -> AssistantStatusRead:
    provider, model, configured = provider_status()
    return AssistantStatusRead(provider=provider, model=model, configured=configured)


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistantConversation:
    conversation = AssistantConversation(
        user_id=current_user.id,
        title=payload.title or "New conversation",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=list[ConversationRead])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AssistantConversation]:
    return list(
        db.scalars(
            select(AssistantConversation)
            .where(AssistantConversation.user_id == current_user.id)
            .order_by(AssistantConversation.updated_at.desc())
            .limit(100)
        ).all()
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[AssistantMessageHistoryRead],
)
def get_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return list_messages(
            db, conversation_id=conversation_id, user_id=current_user.id
        )
    except AssistantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/conversations/{conversation_id}/messages", response_model=AssistantReply
)
def create_message(
    conversation_id: uuid.UUID,
    payload: AssistantMessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistantReply:
    try:
        return send_message(
            db,
            conversation_id=conversation_id,
            user=current_user,
            message=payload.message,
            book_id=payload.book_id,
        )
    except AssistantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AssistantRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        delete_conversation(
            db, conversation_id=conversation_id, user_id=current_user.id
        )
    except AssistantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _action_result(action) -> ActionResultRead:
    return ActionResultRead(id=action.id, status=action.status, result=action.result)


@router.post("/actions/{action_id}/confirm", response_model=ActionResultRead)
def execute_action(
    action_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionResultRead:
    try:
        action = confirm_action(db, action_id=action_id, user_id=current_user.id)
    except AssistantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (AssistantActionError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _action_result(action)


@router.post("/actions/{action_id}/reject", response_model=ActionResultRead)
def decline_action(
    action_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActionResultRead:
    try:
        action = reject_action(db, action_id=action_id, user_id=current_user.id)
    except AssistantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AssistantActionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _action_result(action)
