from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from src.db.session import get_db
from src.models.book import Book
from src.models.library import Library
from src.models.purchase import Purchase
from src.models.user import User
from src.schemas.purchase import PurchaseCreate, PurchaseRead
from src.services.auth_service import get_current_user
from src.utils.pagination import PageMeta, Paginated, offset_limit, sanitize_pagination

router = APIRouter(prefix="/purchases", tags=["Purchases"])


def _query_user_purchases_base(user_id: str) -> Select:
    """Build a base select for a user's purchases with relationships preloaded."""
    return (
        select(Purchase)
        .options(
            selectinload(Purchase.book),
            selectinload(Purchase.user),
        )
        .where(Purchase.user_id == user_id)
    )


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=Paginated[PurchaseRead],
    summary="List purchases",
    description="List the authenticated user's purchases with pagination.",
)
def list_purchases(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Paginated[PurchaseRead]:
    """
    List purchases for the authenticated user.

    Parameters:
        page: Page number (1-based).
        page_size: Items per page.

    Returns:
        Paginated[PurchaseRead]: Paginated list of purchases.
    """
    page, page_size = sanitize_pagination(page, page_size)

    total: int = int(db.scalar(select(func.count(Purchase.id)).where(Purchase.user_id == current_user.id)) or 0)

    off, lim = offset_limit(page, page_size)
    stmt = _query_user_purchases_base(current_user.id).order_by(Purchase.created_at.desc()).offset(off).limit(lim)
    items: List[Purchase] = list(db.execute(stmt).scalars().all())

    meta = PageMeta.build(total=total, page=page, page_size=page_size)
    return Paginated[PurchaseRead](items=[PurchaseRead.model_validate(p) for p in items], meta=meta)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=PurchaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create purchase",
    description="Create a purchase for the authenticated user. Also adds the book to the user's library if not present.",
    responses={
        201: {"description": "Purchase created"},
        404: {"description": "Book not found"},
        409: {"description": "Book already purchased"},
    },
)
def create_purchase(
    payload: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseRead:
    """
    Create a new purchase for the current user.

    Parameters:
        payload: PurchaseCreate payload (user_id in payload is ignored; authenticated user is used).

    Returns:
        PurchaseRead: The created purchase.

    Raises:
        HTTPException 404: Book not found.
        HTTPException 409: Purchase already exists for this user/book.
    """
    book = db.get(Book, payload.book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    exists = db.scalar(
        select(Purchase).where(Purchase.user_id == current_user.id, Purchase.book_id == payload.book_id)
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book already purchased")

    purchase = Purchase(
        user_id=current_user.id,
        book_id=payload.book_id,
        price_cents=payload.price_cents,
        currency=payload.currency,
        transaction_id=payload.transaction_id,
        status=payload.status,
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    # Ensure book is in user's library as a result of purchase
    lib_exists = db.scalar(
        select(Library).where(Library.user_id == current_user.id, Library.book_id == payload.book_id)
    )
    if not lib_exists:
        lib_entry = Library(user_id=current_user.id, book_id=payload.book_id, source="purchase")
        db.add(lib_entry)
        db.commit()

    return PurchaseRead.model_validate(purchase)


# PUBLIC_INTERFACE
@router.get(
    "/{purchase_id}",
    response_model=PurchaseRead,
    summary="Get purchase",
    description="Retrieve a purchase by ID (must belong to the authenticated user).",
    responses={404: {"description": "Purchase not found"}},
)
def get_purchase(
    purchase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseRead:
    """
    Get purchase by ID for the current user.

    Parameters:
        purchase_id: Purchase identifier.

    Returns:
        PurchaseRead

    Raises:
        HTTPException 404: If not found or not owned by user.
    """
    stmt = (
        select(Purchase)
        .options(selectinload(Purchase.book), selectinload(Purchase.user))
        .where(Purchase.id == purchase_id, Purchase.user_id == current_user.id)
    )
    purchase = db.execute(stmt).scalars().first()
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")
    return PurchaseRead.model_validate(purchase)
