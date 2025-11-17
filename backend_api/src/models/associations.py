from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint

from src.db.base import Base

# Association table for many-to-many relation between Book and Category.
# This is a pure association table and does not inherit from BaseModel to avoid extra id/timestamps.
book_category_association: Table = Table(
    "book_categories",
    Base.metadata,
    Column("book_id", String(36), ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", String(36), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("book_id", "category_id", name="uq_book_categories_book_id_category_id"),
)
