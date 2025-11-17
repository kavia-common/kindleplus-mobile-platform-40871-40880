from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings, Settings
from src.db.session import get_db
from src.models.user import User

# Password hashing context
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme declaration (used by dependencies if needed)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# PUBLIC_INTERFACE
def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt via passlib."""
    return _pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hashed value."""
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Intentionally avoid leaking details
        return False


def _create_token(
    subject: str,
    *,
    expires_minutes: int,
    token_type: str,
    cfg: Optional[Settings] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a JWT token with the given subject and expiry."""
    cfg = cfg or settings

    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(
        payload,
        cfg.secret_key,
        algorithm=cfg.jwt_algorithm,
    )
    return token


# PUBLIC_INTERFACE
def create_access_token(subject: str, *, cfg: Optional[Settings] = None, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """Create a short-lived access token."""
    cfg = cfg or settings
    return _create_token(
        subject,
        expires_minutes=cfg.access_token_expire_minutes,
        token_type="access",
        cfg=cfg,
        extra_claims=extra_claims,
    )


# PUBLIC_INTERFACE
def create_refresh_token(subject: str, *, cfg: Optional[Settings] = None, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """Create a long-lived refresh token."""
    cfg = cfg or settings
    return _create_token(
        subject,
        expires_minutes=cfg.refresh_token_expire_minutes,
        token_type="refresh",
        cfg=cfg,
        extra_claims=extra_claims,
    )


# PUBLIC_INTERFACE
def create_token_pair_for_user(user: User, *, cfg: Optional[Settings] = None) -> Tuple[str, str]:
    """Create an access and refresh token pair for a given user."""
    cfg = cfg or settings
    access = create_access_token(user.id, cfg=cfg, extra_claims={"email": user.email, "is_superuser": user.is_superuser})
    refresh = create_refresh_token(user.id, cfg=cfg)
    return access, refresh


# PUBLIC_INTERFACE
def decode_token(token: str, *, cfg: Optional[Settings] = None) -> Dict[str, Any]:
    """Decode and validate a JWT token, returning the payload if valid."""
    cfg = cfg or settings
    try:
        payload = jwt.decode(token, cfg.secret_key, algorithms=[cfg.jwt_algorithm])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e


# PUBLIC_INTERFACE
def get_token_payload(token: str, *, expected_type: Optional[str] = None, cfg: Optional[Settings] = None) -> Dict[str, Any]:
    """Decode a token and (optionally) assert its type."""
    payload = decode_token(token, cfg=cfg)
    if expected_type is not None and payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return payload


# PUBLIC_INTERFACE
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that resolves the current authenticated user from a bearer token."""
    payload = get_token_payload(token, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user
