"""add book external source

Revision ID: 4f6a7b8c9d10
Revises: 8e1a2c3d4f5b
Create Date: 2026-06-05

"""

from alembic import op
import sqlalchemy as sa


revision = "4f6a7b8c9d10"
down_revision = "8e1a2c3d4f5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("external_source", sa.String(length=64), nullable=True))
    op.add_column("books", sa.Column("external_id", sa.String(length=128), nullable=True))
    op.create_unique_constraint(
        "uq_books_external_source_id",
        "books",
        ["external_source", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_books_external_source_id", "books", type_="unique")
    op.drop_column("books", "external_id")
    op.drop_column("books", "external_source")
