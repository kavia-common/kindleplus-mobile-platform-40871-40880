from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


# PUBLIC_INTERFACE
class TokenPair(BaseModel):
    """A pair of access and refresh tokens."""
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer")


# PUBLIC_INTERFACE
class AuthResponse(BaseModel):
    """Authentication response containing tokens and the authenticated user profile."""
    from src.schemas.user import UserRead  # local import to avoid circular at type-check time
    tokens: TokenPair
    user: "UserRead"


# PUBLIC_INTERFACE
class LoginRequest(BaseModel):
    """Request payload for password-based login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


# PUBLIC_INTERFACE
class RefreshRequest(BaseModel):
    """Request payload to refresh tokens using a refresh token."""
    refresh_token: str = Field(..., description="Valid refresh JWT token")


# PUBLIC_INTERFACE
class GoogleLoginRequest(BaseModel):
    """Request payload for Google sign-in using an ID token."""
    id_token: str = Field(..., description="Google ID token obtained on the client")
