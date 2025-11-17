from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.associations import book_category_association

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.book import Book


class Category(BaseModel):
    """
    Category grouping for books.

    Fields:
        id (str): UUID primary key.
        name (str): Human-readable category name.
        slug (str): URL-friendly unique identifier.

    Relationships:
        books: Books belonging to this category (many-to-many).
    """

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)

    # Many-to-many relationship with Book
    books: Mapped[list["Book"]] = relationship(
        "Book",
        secondary=book_category_association,
        back_populates="categories",
        lazy="selectin",
    )
