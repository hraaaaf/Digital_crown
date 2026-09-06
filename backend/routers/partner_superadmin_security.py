from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

from backend import models
from backend.config import settings
from backend.routers.auth import require_superadmin

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _deny(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=403, detail={"code": code, "message": message})


def _explicit_bearer_claims(request: Request) -> dict:
    """Return unverified claims only for request-policy classification.

    Authorization has already been cryptographically validated by the
    ``require_superadmin`` dependency before this policy runs. These claims never
    establish identity or SuperAdmin authority; they only select the stricter
    mobile/WebAuthn branch of the control-plane policy.
    """
    authorization = str(request.headers.get("authorization") or "").strip()
    if not authorization.lower().startswith("bearer "):
        return {}
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return {}
    try:
        claims = jwt.get_unverified_claims(token)
        return claims if isinstance(claims, dict) else {}
    except (JWTError, ValueError, TypeError):
        return {}


def _enforce_marketplace_control_plane_request(request: Request) -> None:
    """Fail closed for P10 while allowing only WebAuthn-UV mobile sessions.

    Identity and SuperAdmin authority are validated by ``require_superadmin``.
    This additional request policy keeps ordinary durable mobile JWTs out of the
    global Marketplace control-plane. A mobile token is admitted only when it is
    the short-lived, device-bound WebAuthn session emitted by Digital Crown with
    ``biometric_uv=true``. Web Bearer and cookie/Origin behaviour is unchanged.
    """
    claims = _explicit_bearer_claims(request)
    bearer_type = str(claims.get("type") or "").strip() or None
    if bearer_type == "mobile" and claims.get("biometric_uv") is not True:
        raise _deny(
            "MARKETPLACE_SUPERADMIN_BIOMETRIC_REQUIRED",
            "Le control-plane Marketplace requiert une vérification biométrique récente sur mobile.",
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
