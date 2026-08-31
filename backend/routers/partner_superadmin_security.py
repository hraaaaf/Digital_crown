from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

from backend import models
from backend.config import settings
from backend.routers.auth import require_superadmin

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _deny(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=403, detail={"code": code, "message": message})


def _explicit_bearer_type(request: Request) -> str | None:
    authorization = str(request.headers.get("authorization") or "").strip()
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        return str(jwt.get_unverified_claims(token).get("type") or "").strip() or None
    except (JWTError, ValueError, TypeError):
        return None


def _enforce_marketplace_control_plane_request(request: Request) -> None:
    """Fail closed on mobile SuperAdmin sessions and cookie CSRF for P10.

    The stronger passkey step-up implementation lives on the separate Superadmin
    hardening branch and is not present on Marketplace master yet. P10 therefore
    enforces only guarantees it can actually prove on this branch: web-session-only
    access plus an exact HTTPS Origin for ambient cookie-authenticated mutations.
    Explicit web Bearer tokens are not ambient browser authority and do not require
    Origin for CSRF protection.
    """
    bearer_type = _explicit_bearer_type(request)
    if bearer_type == "mobile":
        raise _deny(
            "MARKETPLACE_SUPERADMIN_WEB_REQUIRED",
            "Le control-plane Marketplace refuse les sessions mobiles.",
        )

    if request.method.upper() not in _MUTATING_METHODS:
        return

    authorization = str(request.headers.get("authorization") or "").strip()
    if authorization.lower().startswith("bearer "):
        return

    origin = str(request.headers.get("origin") or "").strip().rstrip("/").lower()
    if not origin:
        raise _deny(
            "MARKETPLACE_ORIGIN_REQUIRED",
            "Origine navigateur requise pour une mutation Marketplace par cookie.",
        )
    if not origin.startswith("https://"):
        raise _deny(
            "MARKETPLACE_ORIGIN_FORBIDDEN",
            "Origine HTTPS requise pour une mutation Marketplace par cookie.",
        )

    allowed = {
        item.strip().rstrip("/").lower()
        for item in str(getattr(settings, "ALLOWED_ORIGINS", "")).split(",")
        if item.strip()
    }
    if origin not in allowed:
        raise _deny(
            "MARKETPLACE_ORIGIN_FORBIDDEN",
            "Origine navigateur non autorisée pour le control-plane Marketplace.",
        )


def require_marketplace_superadmin(
    request: Request,
    current_user: models.User = Depends(require_superadmin),
) -> models.User:
    _enforce_marketplace_control_plane_request(request)
    return current_user
