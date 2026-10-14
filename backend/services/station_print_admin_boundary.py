"""LOT04.8-B2c privileged Station print settings boundary (no enable route).

These helpers reject delegated settings/admin and cross-site cookie mutations.
Physical device certification remains absent, so the only permitted mutation
is the safe transition to `disabled`.
"""
from __future__ import annotations

from urllib.parse import urlsplit


class StationPrintAdminDenied(PermissionError):
    pass


def require_cabinet_root_owner(
    *,
    actor_user_id: object,
    actor_employer_id: object,
    tenant_id: object,
) -> None:
    if (
        type(tenant_id) is not int or tenant_id <= 0
        or type(actor_user_id) is not int
        or actor_user_id != tenant_id
        or actor_employer_id is not None
    ):
        raise StationPrintAdminDenied("OWNER_REQUIRED")


def require_same_origin_mutation(
    *,
    expected_base: str,
    origin: str | None,
    fetch_site: str | None,
    has_auth_cookie: bool,
    has_bearer_token: bool,
) -> None:
    """Reject malicious browser origin, even if cookie is auto-attached.

    A cookie-authenticated mutation MUST have an explicit same-origin
    Origin header. A genuine bearer-only client without cookies may omit it.
    Reverse-proxy origin settings must be correct; mismatch denies, never
    trusts browser-controlled configuration fields.
    """
    if fetch_site not in (None, "same-origin", "none"):
        raise StationPrintAdminDenied("CROSS_SITE_FORBIDDEN")
    try:
        expected = urlsplit(expected_base)
        actual = urlsplit(origin) if origin is not None else None
        valid_base = (
            expected.scheme in ("http", "https") and expected.hostname
            and expected.username is None and expected.password is None
        )
        valid_origin = actual is not None and (
            actual.scheme == expected.scheme
            and actual.netloc == expected.netloc
            and actual.path in ("", "/")
            and not actual.query and not actual.fragment
            and actual.username is None and actual.password is None
        )
    except ValueError:
        valid_base = False
        valid_origin = False
    if not valid_base:
        raise StationPrintAdminDenied("TRUSTED_ORIGIN_REQUIRED")
    if origin is not None and not valid_origin:
        raise StationPrintAdminDenied("CROSS_SITE_FORBIDDEN")
    if has_auth_cookie and not valid_origin:
        raise StationPrintAdminDenied("ORIGIN_REQUIRED")
    if not has_auth_cookie and not has_bearer_token:
        raise StationPrintAdminDenied("AUTH_REQUIRED")
