"""Cloudflare R2 (S3-Compatible Zero-Egress) Storage Service with Local Filesystem Fallback.

Features:
1. Zero-Egress Cloudflare R2 Object Storage (`boto3` / `aioboto3` S3 API):
   - Uploads and downloads candidate voice notes (`.ogg`, `.mp3`), handwritten essay images
     (`.jpg`, `.png`, `.webp`), and generated PDF certificates (`.pdf`).
2. Automatic Local Filesystem Fallback (`storage/media/`, `storage/reports/`):
   - When R2 credentials are placeholders or `boto3` is unavailable in offline/dev environments,
     seamlessly stores and retrieves files on the local disk without raising configuration errors.
3. Dual Sync & Async Compatibility:
   - `upload_bytes` and `download_bytes` return `AwaitableStr` and `AwaitableBytes` (subclasses
     of `str` and `bytes`), so callers can invoke them either synchronously (`url = svc.upload_bytes(...)`)
     or asynchronously (`url = await svc.upload_bytes(...)`).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import boto3
    from botocore.config import Config as BotoConfig
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore[assignment]
    BotoConfig = Any  # type: ignore[misc,assignment]

    class BotoCoreError(Exception):  # type: ignore[no-redef]
        pass

    class ClientError(Exception):  # type: ignore[no-redef]
        pass


try:
    import aioboto3
except ImportError:  # pragma: no cover
    aioboto3 = None  # type: ignore[assignment]

from app.core.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

_PLACEHOLDER_PREFIXES = ("your_", "placeholder", "change-this", "example")


class AwaitableStr(str):
    """A `str` subclass that can be used directly as a string OR awaited in async contexts."""

    def __await__(self):  # type: ignore[override]
        async def _coro() -> str:
            return str(self)

        return _coro().__await__()


class AwaitableBytes(bytes):
    """A `bytes` subclass that can be used directly as bytes OR awaited in async contexts."""

    def __await__(self):  # type: ignore[override]
        async def _coro() -> bytes:
            return bytes(self)

        return _coro().__await__()


def _is_placeholder_credential(value: str | None) -> bool:
    """Return True if a credential string is empty or uses a template placeholder."""
    if not value or not value.strip():
        return True
    lower = value.strip().lower()
    return any(lower.startswith(prefix) or prefix in lower for prefix in _PLACEHOLDER_PREFIXES)


def sanitize_storage_key(key: str) -> str:
    """Normalize an object storage key and prevent directory traversal (`..`)."""
    cleaned = key.strip().replace("\\", "/").lstrip("/")
    parts = [part for part in cleaned.split("/") if part and part not in {".", ".."}]
    if not parts:
        raise ValueError(f"Invalid storage key: '{key}'")
    return "/".join(parts)


class R2StorageService:
    """Cloudflare R2 S3-compatible storage service with automatic local filesystem fallback."""

    def __init__(
        self,
        *,
        account_id: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        bucket_name: str | None = None,
        endpoint_url: str | None = None,
        public_domain: str | None = None,
        base_local_dir: str | Path | None = None,
        s3_client: Any | None = None,
        force_local: bool = False,
    ) -> None:
        self.account_id = account_id if account_id is not None else settings.R2_ACCOUNT_ID
        self.access_key_id = (
            access_key_id if access_key_id is not None else settings.R2_ACCESS_KEY_ID
        )
        self.secret_access_key = (
            secret_access_key
            if secret_access_key is not None
            else settings.R2_SECRET_ACCESS_KEY
        )
        self.bucket_name = bucket_name or settings.R2_BUCKET_NAME
        self.endpoint_url = endpoint_url or settings.R2_ENDPOINT_URL
        self.public_domain = (public_domain or settings.R2_PUBLIC_DOMAIN).rstrip("/")

        self.base_local_dir = Path(base_local_dir) if base_local_dir else (BASE_DIR / "storage")
        self.media_dir = self.base_local_dir / "media"
        self.reports_dir = self.base_local_dir / "reports"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self._s3_client = s3_client
        self.force_local = force_local

    @property
    def is_r2_configured(self) -> bool:
        """Return True when real Cloudflare R2 credentials or an explicit S3 client are provided."""
        if self.force_local:
            return False
        if self._s3_client is not None:
            return True
        if boto3 is None:
            return False
        return not (
            _is_placeholder_credential(self.account_id)
            or _is_placeholder_credential(self.access_key_id)
            or _is_placeholder_credential(self.secret_access_key)
            or _is_placeholder_credential(self.endpoint_url)
        )

    @property
    def s3_client(self) -> Any:
        """Lazy-initialize the `boto3` S3 client configured for Cloudflare R2."""
        if self._s3_client is None:
            if boto3 is None:
                raise RuntimeError("boto3 is not installed; cannot create R2 S3 client.")
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name="auto",
                config=BotoConfig(signature_version="s3v4"),
            )
        return self._s3_client

    def _resolve_local_path(self, key: str) -> Path:
        """Map an object key to a safe path inside `storage/media/` or `storage/reports/`."""
        clean_key = sanitize_storage_key(key)
        if clean_key.startswith(("media/", "reports/")):
            target = self.base_local_dir / clean_key
        elif clean_key.endswith(".pdf"):
            target = self.reports_dir / clean_key
        else:
            target = self.media_dir / clean_key
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def get_public_url(self, key: str) -> str:
        """Construct the public CDN/R2 URL for a stored object key."""
        clean_key = sanitize_storage_key(key)
        return f"{self.public_domain}/{clean_key}"

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> AwaitableStr:
        """Upload raw bytes to Cloudflare R2 (or local storage fallback) and return the public URL.

        Returns an `AwaitableStr` so both `url = service.upload_bytes(...)` and
        `url = await service.upload_bytes(...)` work seamlessly.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray.")
        raw_bytes = bytes(data)
        clean_key = sanitize_storage_key(key)

        if self.is_r2_configured:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=clean_key,
                    Body=raw_bytes,
                    ContentType=content_type,
                )
                return AwaitableStr(self.get_public_url(clean_key))
            except (BotoCoreError, ClientError, Exception) as exc:
                logger.warning(
                    "Cloudflare R2 upload failed for key '%s' (%s); falling back to local storage.",
                    clean_key,
                    exc,
                )

        local_path = self._resolve_local_path(clean_key)
        local_path.write_bytes(raw_bytes)
        return AwaitableStr(self.get_public_url(clean_key))

    def download_bytes(self, key: str) -> AwaitableBytes:
        """Download object bytes from Cloudflare R2 (or local storage fallback).

        Returns an `AwaitableBytes` so both `raw = service.download_bytes(key)` and
        `raw = await service.download_bytes(key)` work seamlessly.
        """
        clean_key = sanitize_storage_key(key)

        if self.is_r2_configured:
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=clean_key,
                )
                body = response["Body"]
                data = body.read() if hasattr(body, "read") else bytes(body)
                return AwaitableBytes(data)
            except (BotoCoreError, ClientError, Exception) as exc:
                logger.warning(
                    "Cloudflare R2 download failed for key '%s' (%s); checking local fallback.",
                    clean_key,
                    exc,
                )

        local_path = self._resolve_local_path(clean_key)
        if local_path.exists():
            return AwaitableBytes(local_path.read_bytes())

        direct_path = self.base_local_dir / clean_key
        if direct_path.exists():
            return AwaitableBytes(direct_path.read_bytes())

        raise FileNotFoundError(f"Storage object not found for key: '{clean_key}'")

    async def upload_bytes_async(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Explicit async wrapper for uploading bytes to Cloudflare R2 / local storage."""
        return str(self.upload_bytes(data=data, key=key, content_type=content_type))

    async def download_bytes_async(self, key: str) -> bytes:
        """Explicit async wrapper for downloading bytes from Cloudflare R2 / local storage."""
        return bytes(self.download_bytes(key=key))


_default_storage_service: R2StorageService | None = None


def get_storage_service() -> R2StorageService:
    """Return a cached singleton instance of `R2StorageService`."""
    global _default_storage_service
    if _default_storage_service is None:
        _default_storage_service = R2StorageService()
    return _default_storage_service
