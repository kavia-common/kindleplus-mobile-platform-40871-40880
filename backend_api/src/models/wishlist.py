from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
    from src.models.book import Book


class Wishlist(BaseModel):
    """
    Wishlist item linking a user to a book they have wishlisted.

    Fields:
        id (str): UUID primary key.
        user_id (str): FK to users.id.
        book_id (str): FK to books.id.

    Constraints:
        Unique (user_id, book_id): A book appears only once per user's wishlist.

    Relationships:
        user: The user owning this wishlist entry.
        book: The book wishlisted by the user.
    """

    __tablename__ = "wishlists"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_wishlists_user_id_book_id"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="wishlist_entries")
    book: Mapped["Book"] = relationship("Book", back_populates="wishlist_entries")
