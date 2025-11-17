from __future__ import annotations

import uuid
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class IDMixin:
    """Adds a string UUID primary key column named 'id'."""
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )


class TimestampMixin:
    """Adds created_at and updated_at timestamp columns with server-side defaults."""
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class BaseModel(Base, IDMixin, TimestampMixin):
    """
    Base ORM model to inherit for all persistent entities.
    Includes:
    - UUID primary key 'id'
    - created_at and updated_at timestamps
    """
    __abstract__ = True
