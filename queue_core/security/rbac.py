"""LOT08.2-B: fail-closed Queue Core human authorization policy (synthetic LAB only).

This is deliberately not an HTTP router, token issuer, or production operator
database. The caller MUST resolve a live session and its assignments from the
trusted local server-side identity store on EVERY operation or stream refresh.
Neither principal, tenant nor resource scope may come from a client assertion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class AuthorizationError(Exception):
    """Stable client-safe denial without revealing tenant, visit or token details."""

    def __init__(self, code: str, status_code: int = 403) -> None:
        self.code = code
        self.status_code = status_code
        super().__init__(code)


class Role(str, Enum):
    ADMIN = "admin"
    RECEPTION = "reception"
    STAFF = "staff"


class Permission(str, Enum):
    OPERATOR_MANAGE = "operator.manage"
    QUEUE_MANAGE = "queue.manage"
    RESOURCE_MANAGE = "resource.manage"
    DEVICE_MANAGE = "device.manage"
    AUDIT_READ = "audit.read"
    AUDIT_EXPORT = "audit.export"
    QUEUE_READ = "queue.read"
    VISIT_READ = "visit.read"
    VISIT_CREATE = "visit.create"
    VISIT_CHECK_IN = "visit.check_in"
    QR_ISSUE = "qr.issue"
    QR_REVOKE = "qr.revoke"
    QUEUE_CALL = "queue.call"
    QUEUE_RECALL = "queue.recall"
    QUEUE_CHAIR = "queue.chair"
    QUEUE_DONE = "queue.done"
    QUEUE_NO_SHOW = "queue.no_show"
    QUEUE_OVERRIDE = "queue.override"


_BASE = {
    Role.ADMIN: frozenset({
        Permission.OPERATOR_MANAGE, Permission.QUEUE_MANAGE,
        Permission.RESOURCE_MANAGE, Permission.DEVICE_MANAGE,
        Permission.AUDIT_READ, Permission.AUDIT_EXPORT,
    }),
    Role.RECEPTION: frozenset({
        Permission.QUEUE_READ, Permission.VISIT_READ, Permission.VISIT_CREATE,
        Permission.VISIT_CHECK_IN, Permission.QR_ISSUE, Permission.QR_REVOKE,
    }),
    Role.STAFF: frozenset({
        Permission.QUEUE_READ, Permission.VISIT_READ,
        Permission.QUEUE_CALL, Permission.QUEUE_RECALL,
    }),
}
_EXPLICIT_ONLY = frozenset({
    Permission.QUEUE_CHAIR, Permission.QUEUE_DONE,
    Permission.QUEUE_NO_SHOW, Permission.QUEUE_OVERRIDE,
})
_TENANT_ADMIN = _BASE[Role.ADMIN]
_VISIT_EXISTING = frozenset({
    Permission.VISIT_READ, Permission.VISIT_CHECK_IN,
    Permission.QR_ISSUE, Permission.QR_REVOKE,
    Permission.QUEUE_CALL, Permission.QUEUE_RECALL,
    Permission.QUEUE_CHAIR, Permission.QUEUE_DONE,
    Permission.QUEUE_NO_SHOW, Permission.QUEUE_OVERRIDE,
})
_RESOURCE_ACTIONS = frozenset({
    Permission.QUEUE_CALL, Permission.QUEUE_RECALL,
    Permission.QUEUE_CHAIR, Permission.QUEUE_DONE,
})
_QUEUE_ACTIONS = frozenset(Permission) - _TENANT_ADMIN


@dataclass(frozen=True, slots=True)
class VerifiedPrincipal:
    """Trusted resolver output, NEVER supplied by a browser or queue client."""

    actor_id: str
    tenant_id: str
    roles: frozenset[Role]
    queue_ids: frozenset[str] = frozenset()
    resource_ids: frozenset[str] = frozenset()
    explicit_permissions: frozenset[Permission] = frozenset()
    active: bool = True


@dataclass(frozen=True, slots=True)
class TargetScope:
    """Every referenced object scope must be derived via server-side lookup."""

    tenant_id: str
    queue_id: str | None = None
    visit_id: str | None = None
    visit_tenant_id: str | None = None
    visit_queue_id: str | None = None
    resource_id: str | None = None
    resource_tenant_id: str | None = None
    resource_queue_id: str | None = None


class QueueAuthorizer:
    """No decision cache: every check re-resolves token + live rights."""

    def __init__(
        self, resolve_session: Callable[[str], VerifiedPrincipal | None]
    ) -> None:
        self._resolve_session = resolve_session

    def require(
        self,
        token: str,
        action: Permission,
        target: TargetScope,
        *,
        reason: str | None = None,
    ) -> VerifiedPrincipal:
        if not isinstance(token, str) or not token:
            raise AuthorizationError("AUTH_REQUIRED", 401)
        try:
            principal = self._resolve_session(token)
        except Exception:
            # Resolver failure MUST fail closed; no leaked token or tenant ID.
            raise AuthorizationError("AUTH_REQUIRED", 401) from None
        if (
            not isinstance(principal, VerifiedPrincipal)
            or not principal.active
            or not isinstance(principal.actor_id, str) or not principal.actor_id
            or not isinstance(principal.tenant_id, str) or not principal.tenant_id
            or not isinstance(principal.roles, frozenset)
            or not principal.roles
            or not principal.roles.issubset(set(Role))
        ):
            raise AuthorizationError("AUTH_REQUIRED", 401)
        if not isinstance(action, Permission) or not isinstance(target, TargetScope):
            raise AuthorizationError("AUTHZ_DENIED")
        if not target.tenant_id or target.tenant_id != principal.tenant_id:
            raise AuthorizationError("AUTHZ_DENIED")

        # Never trust a client-provided tenant, visit or resource binding.
        if target.visit_id is not None or action in _VISIT_EXISTING:
            if (
                not target.visit_id
                or not target.visit_tenant_id
                or target.visit_tenant_id != target.tenant_id
                or not target.visit_queue_id
                or target.visit_queue_id != target.queue_id
            ):
                raise AuthorizationError("AUTHZ_DENIED")
        if target.resource_id is not None or action in _RESOURCE_ACTIONS:
            if (
                not target.resource_id
                or not target.resource_tenant_id
                or target.resource_tenant_id != target.tenant_id
                or not target.resource_queue_id
                or target.resource_queue_id != target.queue_id
            ):
                raise AuthorizationError("AUTHZ_DENIED")

        # Default role power is never an implicit operational Admin power.
        defaults = frozenset().union(*(_BASE[r] for r in principal.roles))
        if action in _EXPLICIT_ONLY:
            if action not in principal.explicit_permissions:
                raise AuthorizationError("AUTHZ_DENIED")
            if action is Permission.QUEUE_NO_SHOW and Role.RECEPTION not in principal.roles:
                raise AuthorizationError("AUTHZ_DENIED")
            if action in {Permission.QUEUE_CHAIR, Permission.QUEUE_DONE} and Role.STAFF not in principal.roles:
                raise AuthorizationError("AUTHZ_DENIED")
        elif action not in defaults:
            raise AuthorizationError("AUTHZ_DENIED")

        if action in _QUEUE_ACTIONS:
            if (
                not target.queue_id
                or target.queue_id not in principal.queue_ids
            ):
                raise AuthorizationError("AUTHZ_DENIED")
            if action in _RESOURCE_ACTIONS and target.resource_id not in principal.resource_ids:
                raise AuthorizationError("AUTHZ_DENIED")
        if action is Permission.QUEUE_OVERRIDE:
            if not isinstance(reason, str) or not reason.strip():
                raise AuthorizationError("OVERRIDE_REASON_REQUIRED")
        return principal
