from __future__ import annotations

import re
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import BASE_DIR, get_settings


def _ensure_sqlite_dir(url: str) -> None:
    """
    Ensure the directory for a SQLite file-based database exists.

    This is a safe no-op for non-SQLite URLs or in-memory SQLite DBs.
    """
    if not url.startswith("sqlite"):
        return

    # Skip in-memory DB
    if ":memory:" in url:
        return

    # Extract path after sqlite:///
    # Supports "sqlite:///relative/path.db" or absolute "sqlite:////abs/path.db"
    m = re.match(r"^sqlite:(?://)?/(.*)$", url)
    if not m:
        return

    db_path_str = m.group(1)
    # Handle possible extra leading slash for absolute paths
    db_path = Path("/" + db_path_str).resolve() if db_path_str.startswith("/") else Path(db_path_str).resolve()

    # If the path is relative (e.g., ./data/app.db), make it relative to backend_api root
    if not db_path.is_absolute():
        db_path = (BASE_DIR / db_path).resolve()

    db_path.parent.mkdir(parents=True, exist_ok=True)


def _create_engine() -> Engine:
    settings = get_settings()
    if settings.is_sqlite:
        _ensure_sqlite_dir(settings.database_url)
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}

    # Use pool_pre_ping to gracefully handle stale connections
    engine = create_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    return engine


# Engine and Session factory are module-level singletons
ENGINE: Engine = _create_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Yields:
        A SQLAlchemy Session bound to the application engine.
    Ensures:
        The session is closed after request processing to avoid leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Ensure proper cleanup
        db.close()
