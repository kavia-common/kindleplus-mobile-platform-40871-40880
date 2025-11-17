from __future__ import annotations

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.core.config import get_settings
from src.api.routers.auth import router as auth_router
from src.api.routers.books import router as books_router
from src.api.routers.categories import router as categories_router

settings = get_settings()

openapi_tags = [
    {
        "name": "Health",
        "description": "Health checks and diagnostic endpoints for the service.",
    },
    {
        "name": "Auth",
        "description": "Authentication endpoints: password login, token refresh, and Google OAuth sign-in.",
    },
    {
        "name": "Books",
        "description": "Catalog endpoints for managing and browsing books (search, filters, pagination).",
    },
    {
        "name": "Categories",
        "description": "Endpoints for managing and listing book categories.",
    },
]

app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
    openapi_tags=openapi_tags,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
)

# Configure CORS
allow_origins: List[str] = settings.cors_origins if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(books_router)


class HealthResponse(BaseModel):
    """Health response payload."""
    status: str = Field(default="ok", description="Static health status indicating the API is running.")
    environment: str = Field(default=settings.environment, description="Current environment name.")


# PUBLIC_INTERFACE
@app.get("/", response_model=HealthResponse, summary="Health Check", tags=["Health"])
def health_check() -> HealthResponse:
    """
    Root health check.

    Returns:
        HealthResponse: Static service health and environment info.
    """
    return HealthResponse(status="ok", environment=settings.environment)
