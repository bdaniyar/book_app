"""add user token version for immediate session revocation

Revision ID: b5d7e9f1a3c5
Revises: a4b6c8d0e2f4
Create Date: 2026-07-19

"""

from alembic import op
import sqlalchemy as sa


revision = "b5d7e9f1a3c5"
down_revision = "a4b6c8d0e2f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("users", "token_version", server_default=None)
    op.create_check_constraint(
        "ck_users_token_version_nonnegative",
        "users",
        "token_version >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_token_version_nonnegative", "users", type_="check"
    )
    op.drop_column("users", "token_version")
