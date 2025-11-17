from __future__ import annotations

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, Field

from src.schemas.base import IDSchema, TimestampedSchema
from src.schemas.book import BookSummary
from src.schemas.user import UserSummary


class PurchaseBase(PydBaseModel):
    """Shared properties for purchases."""
    user_id: str = Field(..., description="User ID")
    book_id: str = Field(..., description="Book ID")
    price_cents: int = Field(default=0, ge=0, description="Price in cents")
    currency: str = Field(default="USD", min_length=3, max_length=8)
    transaction_id: str | None = Field(default=None)
    status: str = Field(default="completed")

    model_config = ConfigDict(from_attributes=True)


class PurchaseCreate(PurchaseBase):
    """Payload for creating a purchase."""
    pass


class PurchaseRead(IDSchema, TimestampedSchema, PurchaseBase):
    """Representation of a purchase returned by the API."""
    user: UserSummary | None = None
    book: BookSummary | None = None
