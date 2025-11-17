"""
Model package exports and convenience imports for ORM entities.
"""

from src.db.base import Base  # Declarative base
from src.models.base import BaseModel, IDMixin, TimestampMixin
from src.models.associations import book_category_association
from src.models.user import User
from src.models.category import Category
from src.models.book import Book
from src.models.wishlist import Wishlist
from src.models.purchase import Purchase
from src.models.library import Library
from src.models.reading_progress import ReadingProgress

__all__ = [
    "Base",
    "BaseModel",
    "IDMixin",
    "TimestampMixin",
    # Association tables
    "book_category_association",
    # ORM models
    "User",
    "Category",
    "Book",
    "Wishlist",
    "Purchase",
    "Library",
    "ReadingProgress",
]
