from __future__ import annotations

from sqlalchemy import Date, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.associations import book_category_association

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.category import Category
    from src.models.wishlist import Wishlist
    from src.models.purchase import Purchase
    from src.models.library import Library
    from src.models.reading_progress import ReadingProgress


class Book(BaseModel):
    """
    Book entity representing an e-book available in the catalog.

    Fields:
        id (str): UUID primary key.
        title (str): Book title.
        author (str): Author name(s).
        description (str | None): Optional long-form description.
        cover_image_url (str | None): Optional cover image URL.
        file_url (str | None): Optional file download URL for full book.
        sample_file_url (str | None): Optional sample file URL (preview).
        price_cents (int): Price in cents for precision.
        currency (str): ISO currency code (e.g., 'USD').
        published_date (date | None): Optional publish date.
        isbn (str | None): Optional ISBN.
        language (str | None): Optional language code.
        page_count (int | None): Optional number of pages.
        rating (float | None): Optional average rating.

    Relationships:
        categories: Categories for this book (many-to-many).
        wishlist_entries: Wishlist entries referencing this book.
        purchases: Purchases referencing this book.
        library_entries: Library entries referencing this book.
        reading_progress_entries: Reading progress entries for this book.
    """

    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sample_file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")

    published_date: Mapped["Date | None"] = mapped_column(Date, nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Many-to-many relation with Category
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=book_category_association,
        back_populates="books",
        lazy="selectin",
    )

    # One-to-many relations with user interactions
    wishlist_entries: Mapped[list["Wishlist"]] = relationship(
        "Wishlist",
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase",
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    library_entries: Mapped[list["Library"]] = relationship(
        "Library",
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reading_progress_entries: Mapped[list["ReadingProgress"]] = relationship(
        "ReadingProgress",
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
