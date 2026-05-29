"""add books library reviews and tokens

Revision ID: 8e1a2c3d4f5b
Revises: 2b9b0a1f3d21
Create Date: 2026-05-29

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "8e1a2c3d4f5b"
down_revision = "2b9b0a1f3d21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "email_verified", server_default=None)

    op.create_table(
        "authors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_authors_name"), "authors", ["name"], unique=False)

    op.create_table(
        "books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("isbn", sa.String(length=32), nullable=True),
        sa.Column("cover_url", sa.String(length=2048), nullable=True),
        sa.Column("pages", sa.Integer(), nullable=True),
        sa.Column("published_year", sa.Integer(), nullable=True),
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("authors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("isbn"),
    )
    op.create_index(op.f("ix_books_isbn"), "books", ["isbn"], unique=False)
    op.create_index(op.f("ix_books_title"), "books", ["title"], unique=False)

    op.create_table(
        "book_genres",
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
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
    )

    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE readingstatus AS ENUM ('reading', 'want-to-read', 'read', 'favorite');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    reading_status = postgresql.ENUM(
        "reading",
        "want-to-read",
        "read",
        "favorite",
        name="readingstatus",
        create_type=False,
    )

    op.create_table(
        "user_books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", reading_status, nullable=False),
        sa.Column("progress_pages", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "book_id", name="uq_user_books_user_book"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("helpful", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "book_id", name="uq_reviews_user_book"),
    )

    for table_name in (
        "refresh_tokens",
        "password_reset_tokens",
        "email_verification_tokens",
    ):
        op.create_table(
            table_name,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "revoked_at" if table_name == "refresh_tokens" else "used_at",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index(op.f(f"ix_{table_name}_token_hash"), table_name, ["token_hash"])
        op.create_index(op.f(f"ix_{table_name}_user_id"), table_name, ["user_id"])


def downgrade() -> None:
    for table_name in (
        "email_verification_tokens",
        "password_reset_tokens",
        "refresh_tokens",
    ):
        op.drop_index(op.f(f"ix_{table_name}_user_id"), table_name=table_name)
        op.drop_index(op.f(f"ix_{table_name}_token_hash"), table_name=table_name)
        op.drop_table(table_name)

    op.drop_table("reviews")
    op.drop_table("user_books")
    sa.Enum(name="readingstatus").drop(op.get_bind(), checkfirst=True)
    op.drop_table("book_genres")
    op.drop_index(op.f("ix_books_title"), table_name="books")
    op.drop_index(op.f("ix_books_isbn"), table_name="books")
    op.drop_table("books")
    op.drop_index(op.f("ix_authors_name"), table_name="authors")
    op.drop_table("authors")
    op.drop_column("users", "email_verified")
