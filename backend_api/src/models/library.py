from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
    from src.models.book import Book


class Library(BaseModel):
    """
    Library entry indicating a book available in a user's library.

    Fields:
        id (str): UUID primary key.
        user_id (str): FK to users.id.
        book_id (str): FK to books.id.
        source (str): How the book was added (e.g., 'purchase', 'manual', 'gift').

    Constraints:
        Unique (user_id, book_id): Each book appears once per user's library.

    Relationships:
        user: The library owner.
        book: The book available in the library.
    """

    __tablename__ = "libraries"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_libraries_user_id_book_id"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="purchase")

    user: Mapped["User"] = relationship("User", back_populates="library_entries")
    book: Mapped["Book"] = relationship("Book", back_populates="library_entries")
