from __future__ import annotations

import hashlib
import hmac
import time

from backend.config import settings


PREVIEW_TOKEN_TTL_SECONDS = 10 * 60


def _signature(employer_id: int, rel_path: str, expires_at: int) -> str:
    normalized = rel_path.replace("\\", "/").lstrip("/")
    message = f"{int(employer_id)}\n{normalized}\n{int(expires_at)}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).hexdigest()


def create_document_preview_token(employer_id: int, rel_path: str, *, now: int | None = None) -> str:
    issued = int(time.time() if now is None else now)
    expires_at = issued + PREVIEW_TOKEN_TTL_SECONDS
    return f"{expires_at}.{_signature(employer_id, rel_path, expires_at)}"


def verify_document_preview_token(
    token: str | None,
    employer_id: int,
    rel_path: str,
    *,
    now: int | None = None,
) -> bool:
    if not token:
        return False
    try:
        raw_expiry, supplied = token.split(".", 1)
        expires_at = int(raw_expiry)
    except (ValueError, TypeError):
        return False
    current = int(time.time() if now is None else now)
    if expires_at < current or expires_at > current + PREVIEW_TOKEN_TTL_SECONDS + 60:
        return False
    expected = _signature(employer_id, rel_path, expires_at)
    return hmac.compare_digest(supplied, expected)
