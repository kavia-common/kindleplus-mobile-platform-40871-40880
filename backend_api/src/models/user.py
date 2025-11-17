from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.wishlist import Wishlist
    from src.models.purchase import Purchase
    from src.models.library import Library
    from src.models.reading_progress import ReadingProgress


class User(BaseModel):
    """
    Persistent user entity representing an application account.

    Fields:
        id (str): UUID primary key from BaseModel.
        email (str): Unique email address for the user.
        hashed_password (str): Hashed password (never store plain text).
        full_name (str | None): Optional full name.
        avatar_url (str | None): Optional avatar URL.
        is_active (bool): Whether the user account is active.
        is_superuser (bool): Whether the user has admin privileges.

    Relationships:
        wishlist_entries: Wishlist items created by the user.
        purchases: Purchases made by the user.
        library_entries: Library entries for owned/saved books.
        reading_progress: Reading progress for books the user is reading.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    wishlist_entries: Mapped[list["Wishlist"]] = relationship(
        "Wishlist",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    library_entries: Mapped[list["Library"]] = relationship(
        "Library",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reading_progress: Mapped[list["ReadingProgress"]] = relationship(
        "ReadingProgress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
