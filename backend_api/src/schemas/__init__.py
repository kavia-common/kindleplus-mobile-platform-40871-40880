from __future__ import annotations

from src.schemas.base import IDSchema, TimestampedSchema
from src.schemas.user import UserBase, UserCreate, UserUpdate, UserRead, UserSummary
from src.schemas.category import CategoryBase, CategoryCreate, CategoryUpdate, CategoryRead, CategorySummary
from src.schemas.book import BookBase, BookCreate, BookUpdate, BookRead, BookSummary
from src.schemas.wishlist import WishlistBase, WishlistCreate, WishlistRead
from src.schemas.purchase import PurchaseBase, PurchaseCreate, PurchaseRead
from src.schemas.library import LibraryBase, LibraryCreate, LibraryRead
from src.schemas.reading_progress import ReadingProgressBase, ReadingProgressCreate, ReadingProgressRead

__all__ = [
    # base
    "IDSchema",
    "TimestampedSchema",
    # user
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserSummary",
    # category
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryRead",
    "CategorySummary",
    # book
    "BookBase",
    "BookCreate",
    "BookUpdate",
    "BookRead",
    "BookSummary",
    # wishlist
    "WishlistBase",
    "WishlistCreate",
    "WishlistRead",
    # purchase
    "PurchaseBase",
    "PurchaseCreate",
    "PurchaseRead",
    # library
    "LibraryBase",
    "LibraryCreate",
    "LibraryRead",
    # reading progress
    "ReadingProgressBase",
    "ReadingProgressCreate",
    "ReadingProgressRead",
]
