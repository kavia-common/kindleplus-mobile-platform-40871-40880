from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from src.services.storage_service import get_storage
from src.services.auth_service import get_token_payload

router = APIRouter()


class PresignRequest(BaseModel):
    key: str = Field(..., description="Object key/path in storage")
    expires_in: int = Field(600, description="Expiration in seconds (max 3600)")


class PresignUploadResponse(BaseModel):
    url: str
    fields: dict = {}


class PresignDownloadResponse(BaseModel):
    url: str


def _auth_required(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        claims = get_token_payload(token, expected_type="access")
        return claims
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post(
    "/presign/upload",
    response_model=PresignUploadResponse,
    summary="Get presigned upload URL",
    description="Issue a presigned URL to upload a file to configured storage backend.",
    tags=["Storage"],
)
def presign_upload(req: PresignRequest, auth=Depends(_auth_required)):
    if req.expires_in > 3600 or req.expires_in <= 0:
        raise HTTPException(status_code=400, detail="Invalid expires_in")
    storage = get_storage()
    url, fields = storage.presign_upload(req.key, req.expires_in)
    return PresignUploadResponse(url=url, fields=fields)


@router.post(
    "/presign/download",
    response_model=PresignDownloadResponse,
    summary="Get presigned download URL",
    description="Issue a presigned URL to download a file from configured storage backend.",
    tags=["Storage"],
)
def presign_download(req: PresignRequest, auth=Depends(_auth_required)):
    if req.expires_in > 3600 or req.expires_in <= 0:
        raise HTTPException(status_code=400, detail="Invalid expires_in")
    storage = get_storage()
    url = storage.presign_download(req.key, req.expires_in)
    return PresignDownloadResponse(url=url)


# Local backend helpers (stub) to demonstrate protected download
@router.get("/local/download", summary="Local download (stub)")
def local_download(key: str, exp: int, sig: str):
    # In production, serve file after validating signature
    return {"status": "ok", "key": key}


@router.get("/local/upload", summary="Local upload (stub)")
def local_upload(key: str, exp: int, sig: str):
    return {"status": "ok", "key": key}
