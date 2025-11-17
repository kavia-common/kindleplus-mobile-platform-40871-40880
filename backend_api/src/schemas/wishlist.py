from __future__ import annotations

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, Field

from src.schemas.base import IDSchema, TimestampedSchema
from src.schemas.book import BookSummary
from src.schemas.user import UserSummary


class WishlistBase(PydBaseModel):
    """Shared properties for wishlist entries."""
    user_id: str = Field(..., description="User ID")
    book_id: str = Field(..., description="Book ID")

    model_config = ConfigDict(from_attributes=True)


class WishlistCreate(WishlistBase):
    """Payload for creating a wishlist entry."""
    pass


class WishlistRead(IDSchema, TimestampedSchema, WishlistBase):
    """Representation of a wishlist entry returned by the API."""
    user: UserSummary | None = None
    book: BookSummary | None = None
