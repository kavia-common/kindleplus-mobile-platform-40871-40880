from __future__ import annotations

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.core.config import settings
from src.api.routers.auth import router as auth_router
from src.api.routers.books import router as books_router
from src.api.routers.categories import router as categories_router
from src.api.routers.wishlist import router as wishlist_router
from src.api.routers.purchases import router as purchases_router
from src.api.routers.library import router as library_router
from src.api.routers.reading import router as reading_router
from src.api.routers.storage import router as storage_router
from src.api.routers.payments import router as payments_router
from src.api.routers.admin import router as admin_router

settings = settings  # module-level singleton imported above

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
    {
        "name": "Wishlist",
        "description": "Endpoints for managing the authenticated user's wishlist.",
    },
    {
        "name": "Purchases",
        "description": "Endpoints for managing purchases and viewing order history.",
    },
    {
        "name": "Library",
        "description": "Endpoints for managing and listing the authenticated user's library.",
    },
    {
        "name": "Reading",
        "description": "Endpoints for tracking and updating reading progress.",
    },
    {
        "name": "Storage",
        "description": "Endpoints for requesting presigned upload/download URLs for book assets.",
    },
    {
        "name": "Payments",
        "description": "Endpoints for creating payment sessions and receiving payment webhooks.",
    },
    {
        "name": "Admin",
        "description": "Admin analytics and management endpoints.",
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
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(books_router)
app.include_router(wishlist_router)
app.include_router(purchases_router)
app.include_router(library_router)
app.include_router(reading_router)

# New routers
app.include_router(storage_router, prefix="/storage", tags=["Storage"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


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
