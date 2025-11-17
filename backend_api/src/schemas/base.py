"""
Common base Pydantic schemas and type exports for backend_api schemas.

This module provides basic schema classes like IDSchema, ResponseMessage, and PaginationMeta
to be used throughout the API and serve as building blocks for other schemas.

PUBLIC INTERFACE:
- IDSchema: Schema for models/resources identified by a single 'id' (UUID/str).
- ResponseMessage: Standard simple response with a message.
- PaginationMeta: Metadata for paginated list endpoints (page, size, total, total_pages).
"""

from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class IDSchema(BaseModel):
    """Schema representing a unique identifier for a model/resource."""
    id: str = Field(..., description="Unique identifier for the resource (UUID or string).")

# PUBLIC_INTERFACE
class ResponseMessage(BaseModel):
    """Schema for plain message responses."""
    message: str = Field(..., description="Response message.")

# PUBLIC_INTERFACE
class PaginationMeta(BaseModel):
    """Schema representing pagination metadata for paged list responses."""
    page: int = Field(..., description="Current page number (1-based).")
    page_size: int = Field(..., description="Number of items on the current page.")
    total: int = Field(..., description="Total number of items available.")
    total_pages: int = Field(..., description="Total number of pages.")

__all__ = [
    "BaseModel",
    "IDSchema",
    "ResponseMessage",
    "PaginationMeta",
]
