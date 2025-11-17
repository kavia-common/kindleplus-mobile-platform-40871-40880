from datetime import datetime

from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class IDSchema(BaseModel):
    """Base schema for standard UUID primary key objects."""
    id: str = Field(..., description="Unique UUID identifier")

# PUBLIC_INTERFACE
class TimestampedSchema(BaseModel):
    """
    Base schema for objects with created_at and updated_at timestamps.

    This should be used as a mixin for all resource schema models that require audit fields.
    """
    created_at: datetime = Field(..., description="Resource creation timestamp (ISO-8601)")
    updated_at: datetime = Field(..., description="Resource last update timestamp (ISO-8601)")

# PUBLIC_INTERFACE
class ResponseMessage(BaseModel):
    """A simple response message payload (for status, notifications, etc)."""
    message: str = Field(..., description="Detail message for client display or logs")

# PUBLIC_INTERFACE
class PaginationMeta(BaseModel):
    """Pagination metadata for paginated API endpoints."""
    page: int = Field(..., description="Current page number (1-based)", ge=1)
    page_size: int = Field(..., description="Number of items per page (>=1)", ge=1)
    total: int = Field(..., description="Total number of items matching criteria (>=0)", ge=0)
    total_pages: int = Field(..., description="Total number of available pages (>=1)", ge=1)

__all__ = [
    "IDSchema",
    "TimestampedSchema",
    "ResponseMessage",
    "PaginationMeta"
]
