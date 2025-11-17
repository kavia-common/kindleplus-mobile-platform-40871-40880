from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
    from src.models.book import Book


class Purchase(BaseModel):
    """
    Purchase record representing a user buying a book.

    Fields:
        id (str): UUID primary key.
        user_id (str): FK to users.id.
        book_id (str): FK to books.id.
        price_cents (int): Price in cents at purchase time.
        currency (str): ISO currency code (default 'USD').
        transaction_id (str | None): External payment transaction id.
        status (str): Purchase status (e.g., 'completed', 'refunded').

    Constraints:
        Unique (user_id, book_id): A user purchases the same book once.

    Relationships:
        user: The purchasing user.
        book: The purchased book.
    """

    __tablename__ = "purchases"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_purchases_user_id_book_id"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )

    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")

    user: Mapped["User"] = relationship("User", back_populates="purchases")
    book: Mapped["Book"] = relationship("Book", back_populates="purchases")
