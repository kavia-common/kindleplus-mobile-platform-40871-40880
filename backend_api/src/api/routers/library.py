from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel as PydBaseModel
from pydantic import Field
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from src.db.session import get_db
from src.models.book import Book
from src.models.library import Library
from src.models.user import User
from src.schemas.library import LibraryRead
from src.services.auth_service import get_current_user
from src.utils.pagination import PageMeta, Paginated, offset_limit, sanitize_pagination

router = APIRouter(prefix="/library", tags=["Library"])


class LibraryAddRequest(PydBaseModel):
    """Request payload for adding a book to the current user's library."""
    book_id: str = Field(..., description="Book ID to add to library")
    source: str = Field(default="manual", description="Source of the library entry (e.g., purchase, manual, gift)")


def _query_user_library_base(user_id: str) -> Select:
    """Build a base select for a user's library with relationships preloaded."""
    return (
        select(Library)
        .options(
            selectinload(Library.book),
            selectinload(Library.user),
        )
        .where(Library.user_id == user_id)
    )


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=Paginated[LibraryRead],
    summary="List library",
    description="List the authenticated user's library with pagination and optional search by book title/author.",
)
def list_library(
    q: Optional[str] = Query(default=None, description="Search across book title and author"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Paginated[LibraryRead]:
    """
    List library entries for the current user with optional text search.

    Parameters:
        q: Optional search query across book title and author.
        page: Page number (1-based).
        page_size: Items per page.

    Returns:
        Paginated[LibraryRead]
    """
    page, page_size = sanitize_pagination(page, page_size)

    base = _query_user_library_base(current_user.id)
    count_stmt: Select
    if q:
        like = f"%{q}%"
        base = base.join(Library.book).where(or_(Book.title.ilike(like), Book.author.ilike(like)))
        count_stmt = select(func.count(Library.id)).join(Library.book).where(
            and_(Library.user_id == current_user.id, or_(Book.title.ilike(like), Book.author.ilike(like)))
        )
    else:
        count_stmt = select(func.count(Library.id)).where(Library.user_id == current_user.id)

    total: int = int(db.scalar(count_stmt) or 0)

    off, lim = offset_limit(page, page_size)
    stmt = base.order_by(Library.created_at.desc()).offset(off).limit(lim)
    items: List[Library] = list(db.execute(stmt).scalars().all())

    meta = PageMeta.build(total=total, page=page, page_size=page_size)
    return Paginated[LibraryRead](items=[LibraryRead.model_validate(l) for l in items], meta=meta)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=LibraryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add to library",
    description="Add a book to the authenticated user's library.",
    responses={
        201: {"description": "Library entry created"},
        404: {"description": "Book not found"},
        409: {"description": "Book already in library"},
    },
)
def add_to_library(
    payload: LibraryAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryRead:
    """
    Add a book to the current user's library.

    Parameters:
        payload: Book ID and optional source.

    Returns:
        LibraryRead

    Raises:
        HTTPException 404: Book not found.
        HTTPException 409: Already in library.
    """
    book = db.get(Book, payload.book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    exists = db.scalar(
        select(Library).where(Library.user_id == current_user.id, Library.book_id == payload.book_id)
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book already in library")

    entry = Library(user_id=current_user.id, book_id=payload.book_id, source=payload.source or "manual")
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return LibraryRead.model_validate(entry)


# PUBLIC_INTERFACE
@router.get(
    "/{entry_id}",
    response_model=LibraryRead,
    summary="Get library entry",
    description="Retrieve a library entry by ID (must belong to the authenticated user).",
    responses={404: {"description": "Library entry not found"}},
)
def get_library_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryRead:
    """
    Get a library entry by ID for the current user.

    Parameters:
        entry_id: Library entry ID.

    Returns:
        LibraryRead

    Raises:
        HTTPException 404: If not found or not owned by user.
    """
    stmt = (
        select(Library)
        .options(selectinload(Library.book), selectinload(Library.user))
        .where(Library.id == entry_id, Library.user_id == current_user.id)
    )
    entry = db.execute(stmt).scalars().first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    return LibraryRead.model_validate(entry)


# PUBLIC_INTERFACE
@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove from library",
    description="Remove a library entry by ID (must belong to the authenticated user).",
    responses={204: {"description": "Library entry removed"}, 404: {"description": "Library entry not found"}},
)
def remove_from_library(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Remove a library entry by ID for the current user.

    Parameters:
        entry_id: Library entry ID.

    Returns:
        None (204)

    Raises:
        HTTPException 404: If not found or not owned by user.
    """
    entry = db.get(Library, entry_id)
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library entry not found")
    db.delete(entry)
    db.commit()
    return None
