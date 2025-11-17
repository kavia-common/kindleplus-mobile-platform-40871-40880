from __future__ import annotations

from math import ceil
from typing import Generic, List, Tuple, TypeVar

from pydantic import BaseModel as PydBaseModel
from pydantic import Field

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PageMeta(PydBaseModel):
    """Pagination metadata for list endpoints."""
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total: int = Field(..., ge=0, description="Total number of items available")
    total_pages: int = Field(..., ge=1, description="Total number of pages")

    @staticmethod
    # PUBLIC_INTERFACE
    def build(total: int, page: int, page_size: int) -> "PageMeta":
        """Build a PageMeta given total, page and page_size, clamping page >= 1 and page_size within [1, MAX_PAGE_SIZE]."""
        page = max(1, int(page or 1))
        page_size = int(page_size or DEFAULT_PAGE_SIZE)
        if page_size < 1:
            page_size = DEFAULT_PAGE_SIZE
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
        total_pages = max(ceil(total / page_size) if page_size else 1, 1)
        return PageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)


class Paginated(PydBaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T] = Field(..., description="List of items for the current page")
    meta: PageMeta = Field(..., description="Pagination metadata")


# PUBLIC_INTERFACE
def sanitize_pagination(page: int | None, page_size: int | None) -> Tuple[int, int]:
    """Clamp and sanitize pagination inputs, enforcing sensible limits."""
    page = max(1, int(page or 1))
    size = int(page_size or DEFAULT_PAGE_SIZE)
    if size < 1:
        size = DEFAULT_PAGE_SIZE
    if size > MAX_PAGE_SIZE:
        size = MAX_PAGE_SIZE
    return page, size


# PUBLIC_INTERFACE
def offset_limit(page: int, page_size: int) -> Tuple[int, int]:
    """Return (offset, limit) for the given page and page_size."""
    page, page_size = sanitize_pagination(page, page_size)
    offset = (page - 1) * page_size
    return offset, page_size
