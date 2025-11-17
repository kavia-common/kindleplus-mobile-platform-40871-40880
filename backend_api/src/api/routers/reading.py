from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel as PydBaseModel
from pydantic import Field
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from src.db.session import get_db
from src.models.book import Book
from src.models.reading_progress import ReadingProgress
from src.models.user import User
from src.schemas.reading_progress import ReadingProgressRead
from src.services.auth_service import get_current_user
from src.utils.pagination import PageMeta, Paginated, offset_limit, sanitize_pagination

router = APIRouter(prefix="/reading", tags=["Reading"])


class ReadingProgressUpsertRequest(PydBaseModel):
    """Payload for creating or updating reading progress for a specific book."""
    progress_percent: float | None = Field(default=None, ge=0.0, le=100.0, description="0.0 to 100.0")
    current_chapter: str | None = Field(default=None, description="Current chapter identifier")
    current_location: str | None = Field(default=None, description="Current reading location pointer")
    is_completed: bool | None = Field(default=None, description="Mark as completed (true/false)")


def _query_user_progress_base(user_id: str) -> Select:
    """Build a base select for a user's reading progress with relationships preloaded."""
    return (
        select(ReadingProgress)
        .options(
            selectinload(ReadingProgress.book),
            selectinload(ReadingProgress.user),
        )
        .where(ReadingProgress.user_id == user_id)
    )


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=Paginated[ReadingProgressRead],
    summary="List reading progress",
    description="List the authenticated user's reading progress with pagination. Optionally filter by completion status.",
)
def list_reading_progress(
    is_completed: Optional[bool] = Query(
        default=None, description="If provided, filter by completion status (true/false)"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Paginated[ReadingProgressRead]:
    """
    List reading progress entries for the current user.

    Parameters:
        is_completed: Optional filter by completion status.
        page: Page number (1-based).
        page_size: Items per page.

    Returns:
        Paginated[ReadingProgressRead]
    """
    page, page_size = sanitize_pagination(page, page_size)

    base = _query_user_progress_base(current_user.id)
    count_stmt: Select
    if is_completed is not None:
        base = base.where(ReadingProgress.is_completed == bool(is_completed))
        count_stmt = select(func.count(ReadingProgress.id)).where(
            ReadingProgress.user_id == current_user.id, ReadingProgress.is_completed == bool(is_completed)
        )
    else:
        count_stmt = select(func.count(ReadingProgress.id)).where(ReadingProgress.user_id == current_user.id)

    total: int = int(db.scalar(count_stmt) or 0)

    off, lim = offset_limit(page, page_size)
    stmt = base.order_by(ReadingProgress.updated_at.desc()).offset(off).limit(lim)
    items: List[ReadingProgress] = list(db.execute(stmt).scalars().all())

    meta = PageMeta.build(total=total, page=page, page_size=page_size)
    return Paginated[ReadingProgressRead](items=[ReadingProgressRead.model_validate(r) for r in items], meta=meta)


# PUBLIC_INTERFACE
@router.get(
    "/{book_id}",
    response_model=ReadingProgressRead,
    summary="Get progress for book",
    description="Retrieve reading progress for a specific book in the authenticated user's library.",
    responses={404: {"description": "Reading progress not found"}},
)
def get_progress_for_book(
    book_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadingProgressRead:
    """
    Get reading progress for a given book.

    Parameters:
        book_id: Target book identifier.

    Returns:
        ReadingProgressRead

    Raises:
        HTTPException 404: If no progress exists for this book/user.
    """
    stmt = (
        select(ReadingProgress)
        .options(selectinload(ReadingProgress.book), selectinload(ReadingProgress.user))
        .where(ReadingProgress.user_id == current_user.id, ReadingProgress.book_id == book_id)
    )
    progress = db.execute(stmt).scalars().first()
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading progress not found")
    return ReadingProgressRead.model_validate(progress)


# PUBLIC_INTERFACE
@router.put(
    "/{book_id}",
    response_model=ReadingProgressRead,
    summary="Upsert reading progress",
    description="Create or update reading progress for a specific book. Returns 201 if created, 200 if updated.",
    responses={
        200: {"description": "Reading progress updated"},
        201: {"description": "Reading progress created"},
        404: {"description": "Book not found"},
    },
)
def upsert_progress_for_book(
    book_id: str,
    payload: ReadingProgressUpsertRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadingProgressRead:
    """
    Create or update reading progress for the current user and a given book.

    Parameters:
        book_id: Target book ID.
        payload: One or more progress fields to set.

    Behavior:
        - If a progress record exists, updates provided fields.
        - Otherwise, creates a new record with provided fields (unspecified fields use defaults).

    Returns:
        ReadingProgressRead

    Raises:
        HTTPException 404: Book not found.
    """
    # Validate book exists
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Check for existing progress
    progress = db.scalar(
        select(ReadingProgress).where(
            ReadingProgress.user_id == current_user.id,
            ReadingProgress.book_id == book_id,
        )
    )

    created = False
    if not progress:
        progress = ReadingProgress(user_id=current_user.id, book_id=book_id)
        created = True

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(progress, field, value)

    db.add(progress)
    db.commit()
    db.refresh(progress)

    if created:
        response.status_code = status.HTTP_201_CREATED
    return ReadingProgressRead.model_validate(progress)
