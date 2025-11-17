from __future__ import annotations

from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict, EmailStr, Field

from src.schemas.user import UserRead


class LoginRequest(PydBaseModel):
    """Request payload for password-based login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class RefreshRequest(PydBaseModel):
    """Request payload to refresh tokens using a refresh token."""
    refresh_token: str = Field(..., description="Valid refresh JWT token")


class GoogleLoginRequest(PydBaseModel):
    """Request payload for Google sign-in using an ID token."""
    id_token: str = Field(..., description="Google ID token obtained on the client")


class TokenPair(PydBaseModel):
    """A pair of access and refresh tokens."""
    access_token: str = Field(..., description="Short-lived access token used for API calls")
    refresh_token: str = Field(..., description="Long-lived refresh token for rotating tokens")
    token_type: str = Field(default="bearer", description='Authorization token type; always "bearer"')


class TokenPayload(PydBaseModel):
    """Decoded JWT payload contents used internally."""
    sub: str = Field(..., description="Subject identifier (User ID)")
    type: str = Field(..., description='Token type; either "access" or "refresh"')
    exp: int = Field(..., description="Expiry timestamp (epoch seconds)")
    iat: int = Field(..., description="Issued at timestamp (epoch seconds)")

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(PydBaseModel):
    """Authentication response containing tokens and the authenticated user profile."""
    tokens: TokenPair = Field(..., description="Access and refresh tokens")
    user: UserRead = Field(..., description="Authenticated user information")

    model_config = ConfigDict(from_attributes=True)
