"""split ratings and library favorites

Revision ID: 9c3d5e7f1a2b
Revises: 4f6a7b8c9d10
Create Date: 2026-07-19

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "9c3d5e7f1a2b"
down_revision = "4f6a7b8c9d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Books without local reviews still contain imported catalog aggregates.
    # For books with reviews, however, the legacy review service overwrote those
    # two columns with the local aggregate, so treating them as external again
    # would double-count the same reviews.
    op.alter_column(
        "books",
        "average_rating",
        new_column_name="external_rating",
        existing_type=sa.Numeric(3, 2),
        existing_nullable=False,
    )
    op.alter_column(
        "books",
        "review_count",
        new_column_name="external_review_count",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.add_column(
        "books",
        sa.Column(
            "local_rating",
            sa.Numeric(3, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "books",
        sa.Column(
            "local_review_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.execute(
        """
        UPDATE books AS book
        SET external_rating = 0, external_review_count = 0
        WHERE EXISTS (
            SELECT 1 FROM reviews WHERE reviews.book_id = book.id
        )
        """
    )
    op.execute(
        """
        UPDATE books AS book
        SET
            local_rating = stats.average_rating,
            local_review_count = stats.review_count
        FROM (
            SELECT
                book_id,
                ROUND(AVG(rating)::numeric, 2) AS average_rating,
                COUNT(*)::integer AS review_count
            FROM reviews
            GROUP BY book_id
        ) AS stats
        WHERE book.id = stats.book_id
        """
    )
    op.alter_column("books", "local_rating", server_default=None)
    op.alter_column("books", "local_review_count", server_default=None)

    op.add_column(
        "user_books",
        sa.Column(
            "is_favorite",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.execute(
        "UPDATE user_books SET is_favorite = TRUE WHERE status::text = 'favorite'"
    )

    # PostgreSQL enum members cannot be removed in place. Rebuild the type while
    # translating legacy favorite rows to a real reading status.
    op.execute("ALTER TYPE readingstatus RENAME TO readingstatus_legacy")
    reading_status = postgresql.ENUM(
        "reading",
        "want-to-read",
        "read",
        "dropped",
        name="readingstatus",
    )
    reading_status.create(op.get_bind(), checkfirst=False)
    op.execute(
        """
        ALTER TABLE user_books
        ALTER COLUMN status TYPE readingstatus
        USING (
            CASE
                WHEN status::text = 'favorite' THEN 'want-to-read'
                ELSE status::text
            END
        )::readingstatus
        """
    )
    op.execute("DROP TYPE readingstatus_legacy")
    op.alter_column("user_books", "is_favorite", server_default=None)

    op.create_check_constraint(
        "ck_books_pages_positive", "books", "pages IS NULL OR pages > 0"
    )
    op.create_check_constraint(
        "ck_books_published_year_range",
        "books",
        "published_year IS NULL OR published_year BETWEEN 0 AND 3000",
    )
    op.create_check_constraint(
        "ck_books_external_rating_range",
        "books",
        "external_rating BETWEEN 0 AND 5",
    )
    op.create_check_constraint(
        "ck_books_local_rating_range", "books", "local_rating BETWEEN 0 AND 5"
    )
    op.create_check_constraint(
        "ck_books_external_review_count_nonnegative",
        "books",
        "external_review_count >= 0",
    )
    op.create_check_constraint(
        "ck_books_local_review_count_nonnegative",
        "books",
        "local_review_count >= 0",
    )
    op.create_check_constraint(
        "ck_user_books_progress_pages_nonnegative",
        "user_books",
        "progress_pages >= 0",
    )
    op.create_check_constraint(
        "ck_reviews_rating_range", "reviews", "rating BETWEEN 1 AND 5"
    )
    op.create_check_constraint(
        "ck_reviews_helpful_nonnegative", "reviews", "helpful >= 0"
    )

    op.create_index(
        "ix_books_external_popularity",
        "books",
        ["external_review_count", "external_rating"],
    )
    op.create_index(
        "ix_books_local_popularity",
        "books",
        ["local_review_count", "local_rating"],
    )
    op.create_index(
        "ix_user_books_user_status", "user_books", ["user_id", "status"]
    )
    op.create_index(
        "ix_user_books_user_favorite", "user_books", ["user_id", "is_favorite"]
    )
    op.create_index(
        "ix_reviews_book_created_at", "reviews", ["book_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_reviews_book_created_at", table_name="reviews")
    op.drop_index("ix_user_books_user_favorite", table_name="user_books")
    op.drop_index("ix_user_books_user_status", table_name="user_books")
    op.drop_index("ix_books_local_popularity", table_name="books")
    op.drop_index("ix_books_external_popularity", table_name="books")

    op.drop_constraint("ck_reviews_helpful_nonnegative", "reviews", type_="check")
    op.drop_constraint("ck_reviews_rating_range", "reviews", type_="check")
    op.drop_constraint(
        "ck_user_books_progress_pages_nonnegative", "user_books", type_="check"
    )
    op.drop_constraint(
        "ck_books_local_review_count_nonnegative", "books", type_="check"
    )
    op.drop_constraint(
        "ck_books_external_review_count_nonnegative", "books", type_="check"
    )
    op.drop_constraint("ck_books_local_rating_range", "books", type_="check")
    op.drop_constraint("ck_books_external_rating_range", "books", type_="check")
    op.drop_constraint("ck_books_published_year_range", "books", type_="check")
    op.drop_constraint("ck_books_pages_positive", "books", type_="check")

    op.execute("ALTER TYPE readingstatus RENAME TO readingstatus_current")
    legacy_reading_status = postgresql.ENUM(
        "reading",
        "want-to-read",
        "read",
        "favorite",
        name="readingstatus",
    )
    legacy_reading_status.create(op.get_bind(), checkfirst=False)
    op.execute(
        """
        ALTER TABLE user_books
        ALTER COLUMN status TYPE readingstatus
        USING (
            CASE
                WHEN is_favorite THEN 'favorite'
                WHEN status::text = 'dropped' THEN 'want-to-read'
                ELSE status::text
            END
        )::readingstatus
        """
    )
    op.execute("DROP TYPE readingstatus_current")

    op.drop_column("user_books", "is_favorite")
    # The legacy application has one aggregate pair and recalculates it from
    # local reviews, so preserve local values when downgrading reviewed books.
    op.execute(
        """
        UPDATE books
        SET
            external_rating = local_rating,
            external_review_count = local_review_count
        WHERE local_review_count > 0
        """
    )
    op.drop_column("books", "local_review_count")
    op.drop_column("books", "local_rating")
    op.alter_column(
        "books",
        "external_review_count",
        new_column_name="review_count",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "books",
        "external_rating",
        new_column_name="average_rating",
        existing_type=sa.Numeric(3, 2),
        existing_nullable=False,
    )
