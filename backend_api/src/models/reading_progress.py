from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
    from src.models.book import Book


class ReadingProgress(BaseModel):
    """
    Reading progress entry for a user-book pair.

    Fields:
        id (str): UUID primary key.
        user_id (str): FK to users.id.
        book_id (str): FK to books.id.
        progress_percent (float): 0.0 to 100.0 progress percentage.
        current_chapter (str | None): Current chapter identifier.
        current_location (str | None): Current location/position marker within the book.
        is_completed (bool): Whether the book was finished by the user.

    Constraints:
        Unique (user_id, book_id): One progress record per user-book pair.

    Relationships:
        user: The reader.
        book: The book being read.
    """

    __tablename__ = "reading_progress"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_reading_progress_user_id_book_id"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )

    progress_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_chapter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship("User", back_populates="reading_progress")
    book: Mapped["Book"] = relationship("Book", back_populates="reading_progress_entries")
