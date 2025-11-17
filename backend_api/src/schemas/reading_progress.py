from __future__ import annotations

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, Field

from src.schemas.base import IDSchema, TimestampedSchema
from src.schemas.book import BookSummary
from src.schemas.user import UserSummary


class ReadingProgressBase(PydBaseModel):
    """Shared properties for reading progress entries."""
    user_id: str = Field(..., description="User ID")
    book_id: str = Field(..., description="Book ID")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    current_chapter: str | None = Field(default=None)
    current_location: str | None = Field(default=None)
    is_completed: bool = Field(default=False)

    model_config = ConfigDict(from_attributes=True)


class ReadingProgressCreate(ReadingProgressBase):
    """Payload for creating or setting initial progress."""
    pass


class ReadingProgressRead(IDSchema, TimestampedSchema, ReadingProgressBase):
    """Representation of reading progress returned by the API."""
    user: UserSummary | None = None
    book: BookSummary | None = None
