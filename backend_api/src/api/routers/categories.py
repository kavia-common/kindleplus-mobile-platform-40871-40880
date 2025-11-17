from __future__ import annotations

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.category import Category
from src.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from src.utils.pagination import PageMeta, Paginated, offset_limit, sanitize_pagination

router = APIRouter(prefix="/categories", tags=["Categories"])


def _slugify(value: str) -> str:
    """
    Convert a string into a URL-friendly slug.

    - Lowercase
    - Replace non-alphanumeric with hyphens
    - Collapse multiple hyphens
    - Trim leading/trailing hyphens
    """
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "category"


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=Paginated[CategoryRead],
    summary="List categories",
    description="List all categories with optional search and pagination.",
)
def list_categories(
    q: Optional[str] = Query(default=None, description="Search query (matches name or slug)"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> Paginated[CategoryRead]:
    """
    List categories with optional text search and pagination.

    Parameters:
        q: Optional search string (matches name or slug).
        page: Page number (1-based).
        page_size: Items per page.

    Returns:
        Paginated[CategoryRead]: Paginated list of categories.
    """
    page, page_size = sanitize_pagination(page, page_size)

    filters = []
    if q:
        like = f"%{q}%"
        filters.append(or_(Category.name.ilike(like), Category.slug.ilike(like)))

    base_stmt = select(Category)
    if filters:
        base_stmt = base_stmt.where(*filters)

    # Count total
    count_stmt = select(func.count()).select_from(
        select(Category.id).where(*filters).subquery() if filters else select(Category.id).subquery()
    )
    total: int = int(db.execute(count_stmt).scalar() or 0)

    off, lim = offset_limit(page, page_size)
    stmt = base_stmt.order_by(Category.name.asc()).offset(off).limit(lim)
    items: List[Category] = list(db.execute(stmt).scalars().all())

    meta = PageMeta.build(total=total, page=page, page_size=page_size)
    return Paginated[CategoryRead](items=[CategoryRead.model_validate(c) for c in items], meta=meta)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new category. If slug is not provided it is generated from the name.",
    responses={201: {"description": "Category created"}, 409: {"description": "Slug already exists"}},
)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryRead:
    """
    Create a category.

    Parameters:
        payload: CategoryCreate object containing name and optional slug.

    Returns:
        The created Category.
    """
    slug = payload.slug or _slugify(payload.name)

    # Check uniqueness of slug
    exists_stmt = select(Category).where(Category.slug == slug)
    if db.scalar(exists_stmt):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category slug already exists")

    category = Category(name=payload.name, slug=slug)
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryRead.model_validate(category)


# PUBLIC_INTERFACE
@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Get category by ID",
    description="Retrieve a single category by its ID.",
    responses={404: {"description": "Category not found"}},
)
def get_category(category_id: str, db: Session = Depends(get_db)) -> CategoryRead:
    """
    Retrieve a category by its identifier.

    Parameters:
        category_id: Category ID (UUID string).

    Returns:
        CategoryRead
    """
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return CategoryRead.model_validate(category)


# PUBLIC_INTERFACE
@router.get(
    "/slug/{slug}",
    response_model=CategoryRead,
    summary="Get category by slug",
    description="Retrieve a single category by its slug.",
    responses={404: {"description": "Category not found"}},
)
def get_category_by_slug(slug: str, db: Session = Depends(get_db)) -> CategoryRead:
    """
    Retrieve a category by its slug.

    Parameters:
        slug: Category slug.

    Returns:
        CategoryRead
    """
    category = db.scalar(select(Category).where(Category.slug == slug))
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return CategoryRead.model_validate(category)


# PUBLIC_INTERFACE
@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update category",
    description="Update category fields. If slug is not provided but name is changed, a new slug is generated from the name.",
    responses={404: {"description": "Category not found"}, 409: {"description": "Slug already exists"}},
)
def update_category(category_id: str, payload: CategoryUpdate, db: Session = Depends(get_db)) -> CategoryRead:
    """
    Update a category.

    Parameters:
        category_id: Category ID.
        payload: Fields to update.

    Returns:
        Updated Category.
    """
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and (data["name"] is not None):
        category.name = data["name"]

    # Determine slug changes
    if "slug" in data:
        new_slug = data["slug"] or _slugify(category.name)
    elif "name" in data and data["name"]:
        new_slug = _slugify(data["name"])
    else:
        new_slug = category.slug

    if new_slug != category.slug:
        # Enforce uniqueness
        exists_stmt = select(Category).where(Category.slug == new_slug, Category.id != category.id)
        if db.scalar(exists_stmt):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category slug already exists")
        category.slug = new_slug

    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryRead.model_validate(category)


# PUBLIC_INTERFACE
@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Delete a category by ID.",
    responses={204: {"description": "Category deleted"}, 404: {"description": "Category not found"}},
)
def delete_category(category_id: str, db: Session = Depends(get_db)) -> Response:
    """
    Delete category.

    Parameters:
        category_id: Category ID.

    Returns:
        None (204)
    """
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
