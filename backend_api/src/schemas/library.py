from __future__ import annotations

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, Field

from src.schemas.base import IDSchema, TimestampedSchema
from src.schemas.book import BookSummary
from src.schemas.user import UserSummary


class LibraryBase(PydBaseModel):
    """Shared properties for library entries."""
    user_id: str = Field(..., description="User ID")
    book_id: str = Field(..., description="Book ID")
    source: str = Field(default="purchase", description="Origin of the library entry")

    model_config = ConfigDict(from_attributes=True)


class LibraryCreate(LibraryBase):
    """Payload for creating a library entry."""
    pass


class LibraryRead(IDSchema, TimestampedSchema, LibraryBase):
    """Representation of a library entry returned by the API."""
    user: UserSummary | None = None
    book: BookSummary | None = None
