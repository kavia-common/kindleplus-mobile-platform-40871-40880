from __future__ import annotations

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, Field

from src.schemas.base import IDSchema, TimestampedSchema


class CategoryBase(PydBaseModel):
    """Shared properties for categories."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=120)

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(CategoryBase):
    """Payload for creating a new category."""
    pass


class CategoryUpdate(PydBaseModel):
    """Payload for updating a category."""
    name: str | None = Field(default=None, max_length=100)
    slug: str | None = Field(default=None, max_length=120)


class CategoryRead(IDSchema, TimestampedSchema, CategoryBase):
    """Representation of a category returned by the API."""
    pass


class CategorySummary(IDSchema):
    """Lightweight category representation for embedding inside books."""
    name: str
    slug: str | None = None

    model_config = ConfigDict(from_attributes=True)
