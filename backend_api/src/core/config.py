from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel


# Resolve important paths
# config.py is at backend_api/src/core -> base_dir = backend_api
BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env from backend_api root if present
load_dotenv(BASE_DIR / ".env", override=False)


class Settings(BaseModel):
    """
    Application settings loaded from environment variables with safe defaults.
    This class is used by the application, DB session, and Alembic configuration.

    Note:
    - Do not hardcode environment-specific information in code.
    - Provide values via .env (see .env.example) or environment variables.
    """

    project_name: str = os.getenv("PROJECT_NAME", "KindlePlus Backend API")
    description: str = os.getenv(
        "PROJECT_DESCRIPTION",
        "Backend API for the KindlePlus mobile platform providing auth, catalog, "
        "purchases, wishlist, and file storage integrations.",
    )
    environment: str = os.getenv("ENVIRONMENT", "development")
    version: str = os.getenv("APP_VERSION", "0.1.0")

    # A secret used for cryptographic operations (JWT etc.) – must be set in production!
    secret_key: str = os.getenv("SECRET_KEY", "change-me")

    # Comma-separated list, e.g. "http://localhost:3000,https://myapp.com"
    cors_origins: List[str] = []

    # Database URL, e.g.:
    #   Postgres: postgresql+psycopg://user:password@host:5432/dbname
    #   SQLite:   sqlite:///./data/app.db  (relative to backend_api) or absolute
    database_url: str = ""

    docs_url: str = os.getenv("DOCS_URL", "/docs")
    redoc_url: str = os.getenv("REDOC_URL", "/redoc")
    openapi_url: str = os.getenv("OPENAPI_URL", "/openapi.json")

    def __init__(self, **data):
        # Parse CORS
        cors_raw = os.getenv("CORS_ORIGINS", "*").strip()
        if cors_raw in ("", "*"):
            data["cors_origins"] = ["*"]
        else:
            data["cors_origins"] = [o.strip() for o in cors_raw.split(",") if o.strip()]

        # Compute DB URL with safe default (SQLite) if not provided
        db_url_env = os.getenv("DATABASE_URL", "").strip()
        if not db_url_env:
            sqlite_default = self._default_sqlite_url()
            data["database_url"] = sqlite_default
        else:
            data["database_url"] = db_url_env

        super().__init__(**data)

    def _default_sqlite_url(self) -> str:
        """Return a SQLite database URL pointing to backend_api/data/app.db."""
        data_dir = BASE_DIR / "data"
        # We do not create directories here; DB session module ensures directory existence if needed.
        db_file = (data_dir / "app.db").resolve()
        return f"sqlite:///{db_file}"

    @property
    def is_sqlite(self) -> bool:
        """Return True if the configured database URL uses SQLite."""
        return self.database_url.startswith("sqlite")


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Get a cached Settings instance loaded from environment variables and .env."""
    return _get_settings_cached()


@lru_cache(maxsize=1)
def _get_settings_cached() -> Settings:
    return Settings()
