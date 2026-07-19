import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.book import BookRead


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ConversationRead(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class AssistantMessageCreateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    book_id: uuid.UUID | None = Field(default=None, validation_alias="bookId")

    model_config = {"populate_by_name": True}

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message must not be blank")
        return cleaned


class AssistantMessageRead(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    book_ids: list[str] = Field(default_factory=list, serialization_alias="bookIds")
    created_at: datetime = Field(serialization_alias="createdAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class AssistantCitation(BaseModel):
    book_id: uuid.UUID = Field(serialization_alias="bookId")
    fields: list[str]

    model_config = {"populate_by_name": True}


class ProposedActionRead(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    status: Literal["pending", "executed", "rejected", "expired"]
    expires_at: datetime = Field(serialization_alias="expiresAt")

    model_config = {"populate_by_name": True}


class AssistantMessageHistoryRead(AssistantMessageRead):
    """A persisted message enriched with its grounded catalog evidence."""

    books: list[BookRead] = Field(default_factory=list)
    citations: list[AssistantCitation] = Field(default_factory=list)
    proposed_actions: list[ProposedActionRead] = Field(
        default_factory=list, serialization_alias="proposedActions"
    )


class AssistantReply(BaseModel):
    conversation_id: uuid.UUID = Field(serialization_alias="conversationId")
    message: AssistantMessageRead
    books: list[BookRead] = Field(default_factory=list)
    citations: list[AssistantCitation] = Field(default_factory=list)
    proposed_actions: list[ProposedActionRead] = Field(
        default_factory=list, serialization_alias="proposedActions"
    )

    model_config = {"populate_by_name": True}


class AssistantStatusRead(BaseModel):
    provider: str
    model: str
    configured: bool


class ActionResultRead(BaseModel):
    id: uuid.UUID
    status: Literal["executed", "rejected", "expired"]
    result: dict[str, Any] | None = None
