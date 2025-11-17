from __future__ import annotations
import hmac
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol, Optional, Tuple
from urllib.parse import urlencode

from ..core.config import settings


class StorageBackend(Protocol):
    # PUBLIC_INTERFACE
    def presign_upload(self, key: str, expires_in: int = 600) -> Tuple[str, dict]:
        """Return (url, fields/headers) for uploading a file to storage."""

    # PUBLIC_INTERFACE
    def presign_download(self, key: str, expires_in: int = 600) -> str:
        """Return a signed URL for downloading a file."""


@dataclass
class LocalStorage(StorageBackend):
    base_dir: str

    def _full_path(self, key: str) -> str:
        key = key.lstrip("/").replace("..", "")
        return os.path.join(self.base_dir, key)

    def presign_upload(self, key: str, expires_in: int = 600) -> Tuple[str, dict]:
        # Local backend: emulate a presigned URL pattern to be used by a separate upload service
        # For this template, we provide a non-functional placeholder URL pointing to app endpoint.
        expiry = int((datetime.now(timezone.utc) + timedelta(seconds=expires_in)).timestamp())
        token = hmac.new(b"local", key.encode("utf-8"), hashlib.sha256).hexdigest()
        url = f"/storage/local/upload?key={key}&exp={expiry}&sig={token}"
        return url, {}

    def presign_download(self, key: str, expires_in: int = 600) -> str:
        expiry = int((datetime.now(timezone.utc) + timedelta(seconds=expires_in)).timestamp())
        sig = hmac.new(b"local", key.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"/storage/local/download?key={key}&exp={expiry}&sig={sig}"


@dataclass
class S3Storage(StorageBackend):
    bucket: str
    region: Optional[str]
    access_key_id: Optional[str]
    secret_access_key: Optional[str]

    def presign_upload(self, key: str, expires_in: int = 600) -> Tuple[str, dict]:
        # Placeholder minimal presign (client can PUT). For production use boto3
        base = f"https://{self.bucket}.s3{('-' + self.region) if self.region else ''}.amazonaws.com/{key}"
        params = {"X-Amz-Expires": expires_in}
        return f"{base}?{urlencode(params)}", {}

    def presign_download(self, key: str, expires_in: int = 600) -> str:
        base = f"https://{self.bucket}.s3{('-' + self.region) if self.region else ''}.amazonaws.com/{key}"
        params = {"X-Amz-Expires": expires_in}
        return f"{base}?{urlencode(params)}"


@dataclass
class GCSStorage(StorageBackend):
    bucket: str
    credentials_json: Optional[str]

    def presign_upload(self, key: str, expires_in: int = 600) -> Tuple[str, dict]:
        base = f"https://storage.googleapis.com/{self.bucket}/{key}"
        return f"{base}?GoogleAccessId=placeholder&Expires={expires_in}", {}

    def presign_download(self, key: str, expires_in: int = 600) -> str:
        base = f"https://storage.googleapis.com/{self.bucket}/{key}"
        return f"{base}?GoogleAccessId=placeholder&Expires={expires_in}"


# PUBLIC_INTERFACE
def get_storage() -> StorageBackend:
    """Return a storage backend instance based on configuration."""
    backend = settings.STORAGE_BACKEND.lower()
    if backend == "s3":
        return S3Storage(
            bucket=settings.S3_BUCKET or "",
            region=settings.S3_REGION,
            access_key_id=settings.S3_ACCESS_KEY_ID,
            secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        )
    if backend == "gcs":
        return GCSStorage(bucket=settings.GCS_BUCKET or "", credentials_json=settings.GCS_CREDENTIALS_JSON)
    # default local
    os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    return LocalStorage(base_dir=settings.STORAGE_LOCAL_DIR)
