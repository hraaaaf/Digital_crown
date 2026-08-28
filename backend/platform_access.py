from __future__ import annotations

from typing import Any

from backend.config import settings


PLATFORM_LICENSE_PERMISSIONS = frozenset(
    {
        "license.read",
        "license.create_trial",
        "license.create_paid",
        "license.extend",
        "license.suspend",
        "license.revoke",
        "license.manage_devices",
        "license.change_release_channel",
        "admin.read",
        "admin.create",
        "admin.update_permissions",
        "admin.disable",
        "audit.read",
    }
)


def _user_is_enabled(user: Any) -> bool:
    return bool(
        user is not None
        and getattr(user, "is_active", False)
        and not getattr(user, "is_archived", False)
        and not getattr(user, "is_suspended", False)
    )


def is_platform_superadmin(user: Any) -> bool:
    """Return True only for the immutable configured platform owner id.

    Email/username/role strings are deliberately not a root of trust.
    """
    configured_id = int(getattr(settings, "SUPERADMIN_USER_ID", 0) or 0)
    if configured_id <= 0 or not _user_is_enabled(user):
        return False
    try:
        return int(getattr(user, "id")) == configured_id
    except (TypeError, ValueError):
        return False


def has_platform_permission(user: Any, permission: str) -> bool:
    """Check explicit platform permission without inheriting cabinet ADMIN rights."""
    if permission not in PLATFORM_LICENSE_PERMISSIONS or not _user_is_enabled(user):
        return False
    if is_platform_superadmin(user):
        return True

    permissions = getattr(user, "permissions", None) or {}
    if not isinstance(permissions, dict):
        return False
    return permissions.get(permission) is True
