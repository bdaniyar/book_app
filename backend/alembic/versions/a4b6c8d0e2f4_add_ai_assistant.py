"""add grounded AI assistant conversations and actions

Revision ID: a4b6c8d0e2f4
Revises: 9c3d5e7f1a2b
Create Date: 2026-07-19

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a4b6c8d0e2f4"
down_revision = "9c3d5e7f1a2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assistant_conversations",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_assistant_conversations_user_id",
        "assistant_conversations",
        ["user_id"],
    )

    op.create_table(
        "assistant_messages",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("book_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')", name="ck_assistant_messages_role"
        ),
    )
    op.create_index(
        "ix_assistant_messages_conversation_id",
        "assistant_messages",
        ["conversation_id"],
    )
    op.create_index(
        "ix_assistant_messages_created_at", "assistant_messages", ["created_at"]
    )

    op.create_table(
        "assistant_actions",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assistant_message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assistant_messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'executed', 'rejected', 'expired')",
            name="ck_assistant_actions_status",
        ),
    )
    op.create_index(
        "ix_assistant_actions_conversation_id",
        "assistant_actions",
        ["conversation_id"],
    )
    op.create_index(
        "ix_assistant_actions_user_id", "assistant_actions", ["user_id"]
    )
    op.create_index(
        "ix_assistant_actions_assistant_message_id",
        "assistant_actions",
        ["assistant_message_id"],
    )
    op.create_index(
        "ix_assistant_actions_idempotency_key",
        "assistant_actions",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_assistant_actions_expires_at", "assistant_actions", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_assistant_actions_expires_at", table_name="assistant_actions")
    op.drop_index(
        "ix_assistant_actions_idempotency_key", table_name="assistant_actions"
    )
    op.drop_index("ix_assistant_actions_user_id", table_name="assistant_actions")
    op.drop_index(
        "ix_assistant_actions_assistant_message_id",
        table_name="assistant_actions",
    )
    op.drop_index(
        "ix_assistant_actions_conversation_id", table_name="assistant_actions"
    )
    op.drop_table("assistant_actions")

    op.drop_index(
        "ix_assistant_messages_created_at", table_name="assistant_messages"
    )
    op.drop_index(
        "ix_assistant_messages_conversation_id", table_name="assistant_messages"
    )
    op.drop_table("assistant_messages")

    op.drop_index(
        "ix_assistant_conversations_user_id",
        table_name="assistant_conversations",
    )
    op.drop_table("assistant_conversations")
