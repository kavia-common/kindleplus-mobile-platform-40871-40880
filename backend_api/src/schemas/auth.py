"""Authentication-related request and response schemas for the KindlePlus backend API."""
from pydantic import BaseModel, Field, ConfigDict

from .user import UserRead

# PUBLIC_INTERFACE
class TokenPair(BaseModel):
    """
    A pair of access and refresh tokens.
    """
    access_token: str = Field(..., description="Short-lived access token used for API calls")
    refresh_token: str = Field(..., description="Long-lived refresh token for rotating tokens")
    token_type: str = Field("bearer", description="Authorization token type; always 'bearer'")

    model_config = ConfigDict(from_attributes=True)


# PUBLIC_INTERFACE
class LoginRequest(BaseModel):
    """
    Request payload for password-based login.
    """
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    model_config = ConfigDict(from_attributes=True)


# PUBLIC_INTERFACE
class RefreshRequest(BaseModel):
    """
    Request payload to refresh tokens using a refresh token.
    """
    refresh_token: str = Field(..., description="Valid refresh JWT token")
    model_config = ConfigDict(from_attributes=True)


# PUBLIC_INTERFACE
class GoogleLoginRequest(BaseModel):
    """
    Request payload for Google sign-in using an ID token.
    """
    id_token: str = Field(..., description="Google ID token obtained on the client")
    model_config = ConfigDict(from_attributes=True)


# PUBLIC_INTERFACE
class AuthResponse(BaseModel):
    """
    Authentication response containing tokens and the authenticated user profile.
    """
    tokens: TokenPair = Field(..., description="Access and refresh tokens")
    user: UserRead = Field(..., description="Authenticated user information")

    model_config = ConfigDict(from_attributes=True)


# This config disables __getattr__ dynamic attribute fallback for old BaseModel.
# You may have legacy models requiring this flag. If not needed, omit.
# class Config:
#     arbitrary_types_allowed = True
