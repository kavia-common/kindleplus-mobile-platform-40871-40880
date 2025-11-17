from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel as PydBaseModel
from pydantic import Field
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from src.db.session import get_db
from src.models.book import Book
from src.models.user import User
from src.models.wishlist import Wishlist
from src.schemas.wishlist import WishlistRead
from src.services.auth_service import get_current_user
from src.utils.pagination import PageMeta, Paginated, offset_limit, sanitize_pagination

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


class WishlistAddRequest(PydBaseModel):
    """Request payload for adding a book to the current user's wishlist."""
    book_id: str = Field(..., description="Book ID to add to wishlist")


def _query_user_wishlist_base(user_id: str) -> Select:
    """Build a base select for a user's wishlist with relationships preloaded."""
    return (
        select(Wishlist)
        .options(
            selectinload(Wishlist.book),
            selectinload(Wishlist.user),
        )
        .where(Wishlist.user_id == user_id)
    )


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=Paginated[WishlistRead],
    summary="List wishlist",
    description="List the authenticated user's wishlist with pagination.",
)
def list_wishlist(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Paginated[WishlistRead]:
    """
    List wishlist entries for the authenticated user.

    Parameters:
        page: Page number (1-based).
        page_size: Items per page.

    Returns:
        Paginated[WishlistRead]: Paginated list of wishlist entries.
    """
    page, page_size = sanitize_pagination(page, page_size)

    # Count total
    total: int = int(db.scalar(select(func.count(Wishlist.id)).where(Wishlist.user_id == current_user.id)) or 0)

    # Fetch page
    off, lim = offset_limit(page, page_size)
    stmt = _query_user_wishlist_base(current_user.id).order_by(Wishlist.created_at.desc()).offset(off).limit(lim)
    items: List[Wishlist] = list(db.execute(stmt).scalars().all())

    meta = PageMeta.build(total=total, page=page, page_size=page_size)
    return Paginated[WishlistRead](items=[WishlistRead.model_validate(w) for w in items], meta=meta)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=WishlistRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add to wishlist",
    description="Add a book to the authenticated user's wishlist.",
    responses={
        201: {"description": "Wishlist entry created"},
        404: {"description": "Book not found"},
        409: {"description": "Book already in wishlist"},
    },
)
def add_to_wishlist(
    payload: WishlistAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WishlistRead:
    """
    Add a book to the current user's wishlist.

    Parameters:
        payload: Contains the target book_id.

    Returns:
        WishlistRead: The created wishlist entry.

    Raises:
        HTTPException 404: Book not found.
        HTTPException 409: Already exists in wishlist.
    """
    book = db.get(Book, payload.book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    exists = db.scalar(
        select(Wishlist).where(Wishlist.user_id == current_user.id, Wishlist.book_id == payload.book_id)
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book already in wishlist")

    entry = Wishlist(user_id=current_user.id, book_id=payload.book_id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return WishlistRead.model_validate(entry)


# PUBLIC_INTERFACE
@router.get(
    "/{entry_id}",
    response_model=WishlistRead,
    summary="Get wishlist entry",
    description="Retrieve a wishlist entry by ID (must belong to the authenticated user).",
    responses={404: {"description": "Wishlist entry not found"}},
)
def get_wishlist_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WishlistRead:
    """
    Get a specific wishlist entry by its identifier for the current user.

    Parameters:
        entry_id: Wishlist entry ID.

    Returns:
        WishlistRead.

    Raises:
        HTTPException 404: If not found or not owned by the user.
    """
    stmt = (
        select(Wishlist)
        .options(selectinload(Wishlist.book), selectinload(Wishlist.user))
        .where(Wishlist.id == entry_id, Wishlist.user_id == current_user.id)
    )
    entry = db.execute(stmt).scalars().first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist entry not found")
    return WishlistRead.model_validate(entry)


# PUBLIC_INTERFACE
@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove from wishlist",
    description="Remove a wishlist entry by ID (must belong to the authenticated user).",
    responses={204: {"description": "Wishlist entry removed"}, 404: {"description": "Wishlist entry not found"}},
)
def remove_from_wishlist(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Remove a wishlist entry by its identifier for the current user.

    Parameters:
        entry_id: Wishlist entry ID.

    Returns:
        None (204)

    Raises:
        HTTPException 404: If not found or not owned by the user.
    """
    entry = db.get(Wishlist, entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist entry not found")
    db.delete(entry)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
