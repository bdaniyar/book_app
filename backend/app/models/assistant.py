import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AssistantConversation(Base):
    __tablename__ = "assistant_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(120), nullable=False, default="New conversation"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    messages = relationship(
        "AssistantMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    actions = relationship(
        "AssistantAction",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')", name="ck_assistant_messages_role"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    book_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )

    conversation = relationship("AssistantConversation", back_populates="messages")


class AssistantAction(Base):
    __tablename__ = "assistant_actions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'executed', 'rejected', 'expired')",
            name="ck_assistant_actions_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assistant_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    idempotency_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    conversation = relationship("AssistantConversation", back_populates="actions")
    assistant_message = relationship("AssistantMessage")
