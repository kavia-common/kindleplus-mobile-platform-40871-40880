from __future__ import annotations

import secrets
from typing import Any, Dict, Tuple

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.user import User
from src.services.auth_service import get_password_hash


# PUBLIC_INTERFACE
def verify_google_id_token(id_token: str, audience: str) -> Dict[str, Any]:
    """Verify a Google ID token and return its claims if valid.

    Args:
        id_token: Google ID token obtained on the client.
        audience: Expected Google OAuth Client ID (configured in environment).

    Returns:
        dict: Verified token claims.

    Raises:
        ValueError: If token verification fails.
    """
    request = google_requests.Request()
    claims = google_id_token.verify_oauth2_token(id_token, request, audience=audience)
    return dict(claims)


def _extract_profile(claims: Dict[str, Any]) -> Tuple[str, bool, str | None, str | None]:
    """Extract email, verification flag, name, and avatar from Google claims."""
    email = claims.get("email") or ""
    email_verified = bool(claims.get("email_verified", False))
    name = claims.get("name")
    picture = claims.get("picture")
    return email, email_verified, name, picture


# PUBLIC_INTERFACE
def get_or_create_user_from_google(db: Session, claims: Dict[str, Any]) -> User:
    """Find or create a User corresponding to Google ID token claims.

    Behavior:
        - If a user with the claim email exists, returns it (optionally updates name/avatar).
        - Otherwise, creates a new user with a random generated password (hashed).

    Args:
        db: SQLAlchemy session.
        claims: Verified Google ID token claims.

    Returns:
        User: Existing or newly created user.
    """
    email, _verified, name, picture = _extract_profile(claims)
    if not email:
        raise ValueError("Google token missing required email claim")

    user = db.scalar(select(User).where(User.email == email))
    if user:
        # Optionally update profile fields if not set
        updated = False
        if name and user.full_name != name:
            user.full_name = name
            updated = True
        if picture and user.avatar_url != picture:
            user.avatar_url = picture
            updated = True
        if updated:
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    # Create a new user with a securely generated random password
    random_pw = secrets.token_urlsafe(32)
    user = User(
        email=email,
        hashed_password=get_password_hash(random_pw),
        full_name=name,
        avatar_url=picture,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
