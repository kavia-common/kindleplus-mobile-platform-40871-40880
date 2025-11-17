from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from src.db.session import get_db
from src.models.book import Book
from src.models.category import Category
from src.schemas.book import BookCreate, BookRead, BookUpdate
from src.utils.pagination import PageMeta, Paginated, offset_limit, sanitize_pagination

router = APIRouter(prefix="/books", tags=["Books"])


def _apply_book_filters(
    base_stmt,
    *,
    q: Optional[str],
    author: Optional[str],
    category_id: Optional[str],
    category_slug: Optional[str],
    price_min: Optional[int],
    price_max: Optional[int],
):
    """Apply filters to a given SQLAlchemy select() for books; returns (stmt, used_join)."""
    conditions = []

    if q:
        like = f"%{q}%"
        conditions.append(or_(Book.title.ilike(like), Book.author.ilike(like), Book.description.ilike(like)))
    if author:
        conditions.append(Book.author.ilike(f"%{author}%"))
    if price_min is not None:
        conditions.append(Book.price_cents >= int(price_min))
    if price_max is not None:
        conditions.append(Book.price_cents <= int(price_max))

    used_join = False
    if category_id or category_slug:
        # Join to categories for filtering
        base_stmt = base_stmt.join(Book.categories)
        used_join = True
        if category_id:
            conditions.append(Category.id == category_id)
        if category_slug:
            conditions.append(Category.slug == category_slug)

    if conditions:
        base_stmt = base_stmt.where(and_(*conditions))
    return base_stmt, used_join


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=Paginated[BookRead],
    summary="List books",
    description="List books with search and filters for category, author, and price. Supports pagination.",
)
def list_books(
    q: Optional[str] = Query(default=None, description="Search text across title, author, and description"),
    author: Optional[str] = Query(default=None, description="Filter by author (partial match)"),
    category_id: Optional[str] = Query(default=None, description="Filter by category ID"),
    category_slug: Optional[str] = Query(default=None, description="Filter by category slug"),
    price_min: Optional[int] = Query(default=None, ge=0, description="Minimum price in cents"),
    price_max: Optional[int] = Query(default=None, ge=0, description="Maximum price in cents"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> Paginated[BookRead]:
    """
    List books with search, filters, and pagination.

    Parameters:
        q: Search string across title, author, description.
        author: Filter by author (partial match).
        category_id: Filter books that belong to this category ID.
        category_slug: Filter books that belong to this category slug.
        price_min: Minimum price (cents).
        price_max: Maximum price (cents).
        page: Page number.
        page_size: Items per page.

    Returns:
        Paginated[BookRead]: Paginated list of books.
    """
    page, page_size = sanitize_pagination(page, page_size)

    # Build base select
    base = select(Book).options(selectinload(Book.categories))
    base, used_join = _apply_book_filters(
        base, q=q, author=author, category_id=category_id, category_slug=category_slug, price_min=price_min, price_max=price_max
    )

    # Count distinct books under same filters (avoid duplicates because of joins)
    count_base = select(func.count(func.distinct(Book.id)))
    if used_join:
        count_base = count_base.select_from(Book).join(Book.categories)
    else:
        count_base = count_base.select_from(Book)

    count_base, _ = _apply_book_filters(
        count_base,
        q=q,
        author=author,
        category_id=category_id,
        category_slug=category_slug,
        price_min=price_min,
        price_max=price_max,
    )
    total: int = int(db.execute(count_base).scalar() or 0)

    off, lim = offset_limit(page, page_size)
    stmt = base.order_by(Book.created_at.desc()).offset(off).limit(lim)
    items: List[Book] = list(db.execute(stmt).scalars().all())

    meta = PageMeta.build(total=total, page=page, page_size=page_size)
    return Paginated[BookRead](items=[BookRead.model_validate(b) for b in items], meta=meta)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create book",
    description="Create a new book entry in the catalog.",
)
def create_book(payload: BookCreate, db: Session = Depends(get_db)) -> BookRead:
    """
    Create a book.

    Parameters:
        payload: BookCreate payload.

    Returns:
        The created Book.
    """
    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return BookRead.model_validate(book)


# PUBLIC_INTERFACE
@router.get(
    "/{book_id}",
    response_model=BookRead,
    summary="Get book by ID",
    description="Retrieve a single book by its ID.",
    responses={404: {"description": "Book not found"}},
)
def get_book(book_id: str, db: Session = Depends(get_db)) -> BookRead:
    """
    Retrieve a book by ID.

    Parameters:
        book_id: Book ID (UUID string).

    Returns:
        BookRead
    """
    stmt = select(Book).options(selectinload(Book.categories)).where(Book.id == book_id)
    book = db.execute(stmt).scalars().first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return BookRead.model_validate(book)


# PUBLIC_INTERFACE
@router.patch(
    "/{book_id}",
    response_model=BookRead,
    summary="Update book",
    description="Update mutable fields of a book.",
    responses={404: {"description": "Book not found"}},
)
def update_book(book_id: str, payload: BookUpdate, db: Session = Depends(get_db)) -> BookRead:
    """
    Update a book.

    Parameters:
        book_id: Book ID.
        payload: Partial update payload.

    Returns:
        Updated Book.
    """
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(book, field, value)

    db.add(book)
    db.commit()
    db.refresh(book)
    return BookRead.model_validate(book)


# PUBLIC_INTERFACE
@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book",
    description="Delete a book by ID.",
    responses={204: {"description": "Book deleted"}, 404: {"description": "Book not found"}},
)
def delete_book(book_id: str, db: Session = Depends(get_db)) -> None:
    """
    Delete a book.

    Parameters:
        book_id: Book ID.

    Returns:
        None (204)
    """
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    db.delete(book)
    db.commit()
    return None
