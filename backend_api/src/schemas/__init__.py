# Re-export common schema types for cross-module usage.
from .base import (
    BaseModel,
    IDSchema,
    ResponseMessage,
    PaginationMeta,
)

__all__ = [
    "BaseModel",
    "IDSchema",
    "ResponseMessage",
    "PaginationMeta",
]
