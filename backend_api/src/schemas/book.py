from __future__ import annotations

from datetime import date

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, Field

from src.schemas.base import IDSchema, TimestampedSchema
from src.schemas.category import CategorySummary


class BookBase(PydBaseModel):
    """Shared properties for books."""
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None)

    cover_image_url: str | None = Field(default=None, max_length=512)
    file_url: str | None = Field(default=None, max_length=512)
    sample_file_url: str | None = Field(default=None, max_length=512)

    price_cents: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=8)

    published_date: date | None = None
    isbn: str | None = Field(default=None, max_length=32)
    language: str | None = Field(default=None, max_length=32)
    page_count: int | None = Field(default=None, ge=1)
    rating: float | None = Field(default=None, ge=0, le=5)

    model_config = ConfigDict(from_attributes=True)


class BookCreate(BookBase):
    """Payload for creating a new book."""
    pass


class BookUpdate(PydBaseModel):
    """Payload for updating a book; all fields optional."""
    title: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    description: str | None = None
    cover_image_url: str | None = Field(default=None, max_length=512)
    file_url: str | None = Field(default=None, max_length=512)
    sample_file_url: str | None = Field(default=None, max_length=512)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    published_date: date | None = None
    isbn: str | None = Field(default=None, max_length=32)
    language: str | None = Field(default=None, max_length=32)
    page_count: int | None = Field(default=None, ge=1)
    rating: float | None = Field(default=None, ge=0, le=5)


class BookRead(IDSchema, TimestampedSchema, BookBase):
    """Representation of a book returned by the API."""
    categories: list[CategorySummary] = []


class BookSummary(IDSchema):
    """Lightweight representation for embedding inside related models."""
    title: str
    author: str

    model_config = ConfigDict(from_attributes=True)
