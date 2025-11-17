"""Initial database schema for KindlePlus Backend.

Revision ID: 0001_initial
Revises: 
Create Date: 2025-01-01 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _timestamps():
    """Helper to return created_at and updated_at column definitions."""
    # Note: Using CURRENT_TIMESTAMP as a generic server default; ORM sets onupdate for updated_at.
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        *_timestamps(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    # Categories
    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        *_timestamps(),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=False)
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    # Books
    op.create_table(
        "books",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        *_timestamps(),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=512), nullable=True),
        sa.Column("file_url", sa.String(length=512), nullable=True),
        sa.Column("sample_file_url", sa.String(length=512), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("isbn", sa.String(length=32), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
    )
    op.create_index("ix_books_title", "books", ["title"], unique=False)
    op.create_index("ix_books_author", "books", ["author"], unique=False)

    # Book <-> Category association
    op.create_table(
        "book_categories",
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category_id", sa.String(length=36), sa.ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("book_id", "category_id", name="uq_book_categories_book_id_category_id"),
    )

    # Wishlist entries
    op.create_table(
        "wishlists",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        *_timestamps(),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "book_id", name="uq_wishlists_user_id_book_id"),
    )
    op.create_index("ix_wishlists_user_id", "wishlists", ["user_id"], unique=False)
    op.create_index("ix_wishlists_book_id", "wishlists", ["book_id"], unique=False)

    # Purchases
    op.create_table(
        "purchases",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        *_timestamps(),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("transaction_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'completed'")),
        sa.UniqueConstraint("user_id", "book_id", name="uq_purchases_user_id_book_id"),
    )
    op.create_index("ix_purchases_user_id", "purchases", ["user_id"], unique=False)
    op.create_index("ix_purchases_book_id", "purchases", ["book_id"], unique=False)

    # Libraries
    op.create_table(
        "libraries",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        *_timestamps(),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default=sa.text("'purchase'")),
        sa.UniqueConstraint("user_id", "book_id", name="uq_libraries_user_id_book_id"),
    )
    op.create_index("ix_libraries_user_id", "libraries", ["user_id"], unique=False)
    op.create_index("ix_libraries_book_id", "libraries", ["book_id"], unique=False)

    # Reading progress
    op.create_table(
        "reading_progress",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        *_timestamps(),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", sa.String(length=36), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("current_chapter", sa.String(length=255), nullable=True),
        sa.Column("current_location", sa.String(length=255), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("user_id", "book_id", name="uq_reading_progress_user_id_book_id"),
    )
    op.create_index("ix_reading_progress_user_id", "reading_progress", ["user_id"], unique=False)
    op.create_index("ix_reading_progress_book_id", "reading_progress", ["book_id"], unique=False)


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_reading_progress_book_id", table_name="reading_progress")
    op.drop_index("ix_reading_progress_user_id", table_name="reading_progress")
    op.drop_table("reading_progress")

    op.drop_index("ix_libraries_book_id", table_name="libraries")
    op.drop_index("ix_libraries_user_id", table_name="libraries")
    op.drop_table("libraries")

    op.drop_index("ix_purchases_book_id", table_name="purchases")
    op.drop_index("ix_purchases_user_id", table_name="purchases")
    op.drop_table("purchases")

    op.drop_index("ix_wishlists_book_id", table_name="wishlists")
    op.drop_index("ix_wishlists_user_id", table_name="wishlists")
    op.drop_table("wishlists")

    op.drop_table("book_categories")

    op.drop_index("ix_books_author", table_name="books")
    op.drop_index("ix_books_title", table_name="books")
    op.drop_table("books")

    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
