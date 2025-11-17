from __future__ import annotations

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, EmailStr, Field

from src.schemas.base import IDSchema, TimestampedSchema


class UserBase(PydBaseModel):
    """Shared properties for User entities (excludes password hash)."""
    email: EmailStr = Field(..., description="Unique email address")
    full_name: str | None = Field(default=None, description="Optional full name")
    avatar_url: str | None = Field(default=None, description="Optional avatar URL")
    is_active: bool = Field(default=True, description="Whether the user is active")
    is_superuser: bool = Field(default=False, description="Whether the user is a superuser")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """Payload for creating a new user (accepts plaintext password)."""
    password: str = Field(..., min_length=6, description="Plaintext password for account setup")


class UserUpdate(PydBaseModel):
    """Payload for updating user profile fields."""
    full_name: str | None = Field(default=None)
    avatar_url: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(default=None)


class UserRead(IDSchema, TimestampedSchema, UserBase):
    """Representation of a user returned by the API."""
    pass


class UserSummary(IDSchema):
    """Lightweight representation for embedding inside related models."""
    email: EmailStr
    full_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
