from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.session import get_db
from src.models.user import User
from src.schemas.auth import (
    AuthResponse,
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    TokenPair,
)
from src.schemas.user import UserRead
from src.services import auth_service
from src.services.google_oauth import get_or_create_user_from_google, verify_google_id_token

router = APIRouter(prefix="/auth", tags=["Auth"])


def _build_auth_response(user: User, access: str, refresh: str) -> AuthResponse:
    """Helper to compose an AuthResponse object."""
    return AuthResponse(
        tokens=TokenPair(access_token=access, refresh_token=refresh, token_type="bearer"),
        user=UserRead.model_validate(user),
    )


# PUBLIC_INTERFACE
@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Password Login",
    description="Authenticate using email and password, returning an access/refresh token pair.",
    responses={
        200: {"description": "Authenticated successfully"},
        401: {"description": "Invalid credentials or inactive user"},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Authenticate a user by email and password.

    Parameters:
        payload (LoginRequest): Email and password.

    Returns:
        AuthResponse: Authentication tokens and user profile.

    Raises:
        HTTPException 401: If credentials are invalid or user is inactive.
    """
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not auth_service.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive")

    access, refresh = auth_service.create_token_pair_for_user(user)
    return _build_auth_response(user, access, refresh)


# PUBLIC_INTERFACE
@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh Token",
    description="Issue a new access/refresh token pair given a valid refresh token.",
    responses={
        200: {"description": "Tokens refreshed"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
def refresh_tokens(payload: RefreshRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Refresh token pair using a valid refresh token.

    Parameters:
        payload (RefreshRequest): Contains a refresh_token.

    Returns:
        AuthResponse: New token pair and user profile.

    Raises:
        HTTPException 401: If token invalid or user not found/inactive.
    """
    claims: Dict = auth_service.get_token_payload(payload.refresh_token, expected_type="refresh")
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")

    access, refresh = auth_service.create_token_pair_for_user(user)
    return _build_auth_response(user, access, refresh)


# PUBLIC_INTERFACE
@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Google Sign-In",
    description="Verify a Google ID token and sign-in/up the user, returning an access/refresh token pair.",
    responses={
        200: {"description": "Authenticated via Google"},
        400: {"description": "Invalid Google token or unverified email"},
        500: {"description": "Google OAuth not configured"},
    },
)
def google_sign_in(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Authenticate via Google ID token.

    Parameters:
        payload (GoogleLoginRequest): Contains Google id_token.
        settings (Settings): Application settings (GOOGLE_CLIENT_ID required).

    Returns:
        AuthResponse: Token pair and user profile.

    Raises:
        HTTPException 400: If token invalid or email not verified.
        HTTPException 500: If GOOGLE_CLIENT_ID not configured.
    """
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID.")

    try:
        claims = verify_google_id_token(payload.id_token, audience=settings.google_client_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Google ID token") from e

    email_verified = bool(claims.get("email_verified", False))
    if not email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unverified Google account email")

    try:
        user = get_or_create_user_from_google(db, claims)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    access, refresh = auth_service.create_token_pair_for_user(user)
    return _build_auth_response(user, access, refresh)
