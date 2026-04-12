"""create genres and user_favorite_genres

Revision ID: 2b9b0a1f3d21
Revises: 17ec7d03f9bb
Create Date: 2026-04-12

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2b9b0a1f3d21"
down_revision = "17ec7d03f9bb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "genres",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_genres_name"), "genres", ["name"], unique=False)

    op.create_table(
        "user_favorite_genres",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "genre_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("genres.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", "genre_id"),
    )


def downgrade() -> None:
    op.drop_table("user_favorite_genres")
    op.drop_index(op.f("ix_genres_name"), table_name="genres")
    op.drop_table("genres")
