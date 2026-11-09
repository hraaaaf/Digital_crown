"""LOT08.2-B/B-2: local operator persistence and live RBAC session resolver.

This is a deliberately isolated software/LAB component, not an HTTP service.
It extends the existing ACL-protected LOT08.2-A local-auth SQLite *file* so
recovery can atomically revoke ALL kinds of sessions. Never a clinical DB.
First tenant binding requires the existing elevated local-console guard and
an authenticated first-Admin session. No remote tenant bootstrap.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
import hmac
import re
import secrets
import sqlite3
import time

from .local_auth import (
    LocalIdentityError, LocalIdentityStore, LOCK_SECONDS, MAX_ATTEMPTS,
    SESSION_TTL_SECONDS, _derive_password, _fingerprint, _new_password,
    _random_secret, _username, _DUMMY_SALT,
)
from .rbac import Permission, QueueAuthorizer, Role, VerifiedPrincipal


class OperatorError(Exception):
    """Non-sensitive, stable error codes; never include credentials or IDs."""


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS operators (
        actor_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL,
        username TEXT NOT NULL, role TEXT NOT NULL
            CHECK (role IN ('admin','reception','staff')),
        enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
        is_bootstrap INTEGER NOT NULL DEFAULT 0 CHECK (is_bootstrap IN (0,1)),
        password_salt BLOB, password_digest TEXT,
        login_failures INTEGER NOT NULL DEFAULT 0,
        locked_until INTEGER NOT NULL DEFAULT 0,
        created_epoch INTEGER NOT NULL,
        UNIQUE(tenant_id, username),
        CHECK ((is_bootstrap=1 AND password_salt IS NULL
                AND password_digest IS NULL)
            OR (is_bootstrap=0 AND password_salt IS NOT NULL
                AND password_digest IS NOT NULL))
    )""",
    """CREATE UNIQUE INDEX IF NOT EXISTS one_bootstrap_operator
        ON operators(is_bootstrap) WHERE is_bootstrap=1""",
    """CREATE TRIGGER IF NOT EXISTS operator_bootstrap_immutable_update
        BEFORE UPDATE ON operators
        WHEN OLD.is_bootstrap=1 BEGIN
            SELECT RAISE(ABORT, 'BOOTSTRAP_ADMIN_IMMUTABLE');
        END""",
    """CREATE TRIGGER IF NOT EXISTS operator_bootstrap_immutable_delete
        BEFORE DELETE ON operators WHEN OLD.is_bootstrap=1 BEGIN
            SELECT RAISE(ABORT, 'BOOTSTRAP_ADMIN_IMMUTABLE');
        END""",
    """CREATE TRIGGER IF NOT EXISTS operator_keep_last_admin
        BEFORE UPDATE OF role,enabled ON operators
        WHEN OLD.role='admin' AND OLD.enabled=1 AND
            (NEW.role!='admin' OR NEW.enabled=0) AND
            (SELECT count(*) FROM operators WHERE tenant_id=OLD.tenant_id
             AND role='admin' AND enabled=1)=1
        BEGIN SELECT RAISE(ABORT, 'LAST_ADMIN_REQUIRED'); END""",
    """CREATE TABLE IF NOT EXISTS operator_assignments (
        actor_id TEXT NOT NULL REFERENCES operators(actor_id) ON DELETE CASCADE,
        kind TEXT NOT NULL CHECK (kind IN ('queue','resource')),
        scope_id TEXT NOT NULL,
        PRIMARY KEY(actor_id,kind,scope_id)
    )""",
    """CREATE TABLE IF NOT EXISTS operator_grants (
        actor_id TEXT NOT NULL REFERENCES operators(actor_id) ON DELETE CASCADE,
        permission TEXT NOT NULL, PRIMARY KEY(actor_id, permission)
    )""",
    """CREATE TABLE IF NOT EXISTS operator_sessions (
        digest TEXT PRIMARY KEY, actor_id TEXT NOT NULL
            REFERENCES operators(actor_id) ON DELETE CASCADE,
        issued_epoch INTEGER NOT NULL, expires_epoch INTEGER NOT NULL
    )""",
    """CREATE INDEX IF NOT EXISTS operator_sessions_actor
        ON operator_sessions(actor_id)""",
    """CREATE TABLE IF NOT EXISTS operator_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, epoch INTEGER NOT NULL,
        actor_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
        target_actor_id TEXT, action TEXT NOT NULL
    )""",
    """CREATE TRIGGER IF NOT EXISTS operator_audit_no_update
        BEFORE UPDATE ON operator_audit BEGIN
            SELECT RAISE(ABORT, 'APPEND_ONLY_AUDIT');
        END""",
    """CREATE TRIGGER IF NOT EXISTS operator_audit_no_delete
        BEFORE DELETE ON operator_audit BEGIN
            SELECT RAISE(ABORT, 'APPEND_ONLY_AUDIT');
        END""",
)

_EXPLICIT = frozenset({
    Permission.QUEUE_CHAIR, Permission.QUEUE_DONE,
    Permission.QUEUE_NO_SHOW, Permission.QUEUE_OVERRIDE,
})


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value):
        raise OperatorError("INVALID_IDENTIFIER")
    return value


def _validated_role(role: Role) -> Role:
    if not isinstance(role, Role):
        raise OperatorError("INVALID_ROLE")
    return role


def _scopes(values: Iterable[str]) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise OperatorError("INVALID_SCOPE")
    try:
        items = frozenset(_identifier(x) for x in values)
    except (TypeError, ValueError) as exc:
        raise OperatorError("INVALID_SCOPE") from exc
    if len(items) > 1000:
        raise OperatorError("SCOPE_LIMIT")
    return items


def _grants(values: Iterable[Permission], role: Role) -> frozenset[Permission]:
    if isinstance(values, (str, bytes)):
        raise OperatorError("INVALID_GRANT")
    try:
        items = frozenset(values)
    except TypeError as exc:
        raise OperatorError("INVALID_GRANT") from exc
    if not all(isinstance(x, Permission) and x in _EXPLICIT for x in items):
        raise OperatorError("INVALID_GRANT")
    if Permission.QUEUE_NO_SHOW in items and role is not Role.RECEPTION:
        raise OperatorError("INVALID_GRANT")
    if any(x in items for x in (Permission.QUEUE_CHAIR, Permission.QUEUE_DONE)) and role is not Role.STAFF:
        raise OperatorError("INVALID_GRANT")
    if Permission.QUEUE_OVERRIDE in items and role not in (Role.RECEPTION, Role.STAFF):
        raise OperatorError("INVALID_GRANT")
    return items


class LocalOperatorStore:
    """Same isolated SQLite/ACL boundary as LocalIdentityStore; no routes."""

    def __init__(
        self, auth: LocalIdentityStore, *, clock: Callable[[], float] = time.time,
    ) -> None:
        if not isinstance(auth, LocalIdentityStore):
            raise TypeError("AUTH_STORE_REQUIRED")
        self.auth = auth
        self._clock = clock

    def _now(self) -> int:
        return int(self._clock())

    def _install(self, c: sqlite3.Connection) -> None:
        for ddl in _SCHEMA:
            c.execute(ddl)

    @staticmethod
    def _audit(c: sqlite3.Connection, now: int, actor: str, tenant: str,
               target: str | None, action: str) -> None:
        c.execute(
            """INSERT INTO operator_audit
                (epoch,actor_id,tenant_id,target_actor_id,action)
                VALUES(?,?,?,?,?)""",
            (now, actor, tenant, target, action),
        )

    @staticmethod
    def _admin_session(c: sqlite3.Connection, token: str, now: int) -> bool:
        if not isinstance(token, str) or not token or len(token) > 256:
            return False
        row = c.execute(
            "SELECT expires_epoch FROM local_sessions WHERE digest=?",
            (_fingerprint(token, "session"),),
        ).fetchone()
        return row is not None and now < row["expires_epoch"]

    @staticmethod
    def _account(c: sqlite3.Connection, token: str, now: int):
        if not isinstance(token, str) or not token or len(token) > 256:
            return None
        # 08.2-A administrator has a distinct session format and table.
        if LocalOperatorStore._admin_session(c, token, now):
            return c.execute(
                "SELECT * FROM operators WHERE is_bootstrap=1 AND enabled=1"
            ).fetchone()
        return c.execute(
            """SELECT o.* FROM operator_sessions s
               JOIN operators o ON o.actor_id=s.actor_id
               WHERE s.digest=? AND s.expires_epoch>? AND o.enabled=1""",
            (_fingerprint(token, "operator_session"), now),
        ).fetchone()

    @staticmethod
    def _principal(c: sqlite3.Connection, token: str, now: int):
        row = LocalOperatorStore._account(c, token, now)
        if row is None:
            return None
        actor_id = row["actor_id"]
        assignments = c.execute(
            "SELECT kind,scope_id FROM operator_assignments WHERE actor_id=?",
            (actor_id,),
        ).fetchall()
        grants = c.execute(
            "SELECT permission FROM operator_grants WHERE actor_id=?",
            (actor_id,),
        ).fetchall()
        try:
            return VerifiedPrincipal(
                actor_id=actor_id, tenant_id=row["tenant_id"],
                roles=frozenset({Role(row["role"])}),
                queue_ids=frozenset(r["scope_id"] for r in assignments if r["kind"] == "queue"),
                resource_ids=frozenset(r["scope_id"] for r in assignments if r["kind"] == "resource"),
                explicit_permissions=frozenset(Permission(r["permission"]) for r in grants),
            )
        except (ValueError, TypeError):
            # Corrupt rights must not create a permissive principal.
            return None

    def resolve_session(self, token: str) -> VerifiedPrincipal | None:
        """Live DB lookup on EVERY authorization; no principal cache."""
        with self.auth._connect() as c:
            return self._principal(c, token, self._now())

    def authorizer(self) -> QueueAuthorizer:
        return QueueAuthorizer(self.resolve_session)

    def bind_first_admin(self, *, first_admin_session: str, tenant_id: str) -> str:
        """One-time privileged local-console binding; never trust client tenant IDs."""
        self.auth._guard()
        tenant = _identifier(tenant_id)
        now = self._now()
        with self.auth._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            if not self._admin_session(c, first_admin_session, now):
                raise OperatorError("AUTH_REQUIRED")
            seed = c.execute("SELECT username FROM local_admin WHERE id=1").fetchone()
            if seed is None:
                raise OperatorError("AUTH_REQUIRED")
            self._install(c)
            if c.execute("SELECT 1 FROM operators LIMIT 1").fetchone():
                raise OperatorError("ALREADY_PROVISIONED")
            actor_id = secrets.token_hex(16)
            c.execute(
                """INSERT INTO operators
                    (actor_id,tenant_id,username,role,is_bootstrap,created_epoch)
                    VALUES(?,?,?,'admin',1,?)""",
                (actor_id, tenant, seed["username"], now),
            )
            self._audit(c, now, actor_id, tenant, actor_id, "first_admin_bound")
            c.commit()
        return actor_id

    @staticmethod
    def _require_admin(c: sqlite3.Connection, token: str, now: int) -> VerifiedPrincipal:
        p = LocalOperatorStore._principal(c, token, now)
        if p is None:
            raise OperatorError("AUTH_REQUIRED")
        if Role.ADMIN not in p.roles:
            raise OperatorError("AUTHZ_DENIED")
        return p

    @staticmethod
    def _target(c: sqlite3.Connection, actor_id: str, tenant: str):
        key = _identifier(actor_id)
        row = c.execute(
            "SELECT * FROM operators WHERE actor_id=? AND tenant_id=?",
            (key, tenant),
        ).fetchone()
        if row is None:
            raise OperatorError("AUTHZ_DENIED")
        return row

    @staticmethod
    def _last_admin_guard(c: sqlite3.Connection, tenant: str) -> None:
        count = c.execute(
            "SELECT count(*) FROM operators WHERE tenant_id=? AND role='admin' AND enabled=1",
            (tenant,),
        ).fetchone()[0]
        if count < 1:
            raise OperatorError("LAST_ADMIN_REQUIRED")

    @staticmethod
    def _replace_links(c: sqlite3.Connection, actor_id: str, kind: str,
                       values: frozenset[str]) -> None:
        c.execute(
            "DELETE FROM operator_assignments WHERE actor_id=? AND kind=?",
            (actor_id, kind),
        )
        c.executemany(
            "INSERT INTO operator_assignments (actor_id,kind,scope_id) VALUES(?,?,?)",
            ((actor_id, kind, x) for x in sorted(values)),
        )

    @staticmethod
    def _invalidate(c: sqlite3.Connection, actor_id: str, bootstrap: bool) -> None:
        c.execute("DELETE FROM operator_sessions WHERE actor_id=?", (actor_id,))
        if bootstrap:
            c.execute("DELETE FROM local_sessions")

    def create_operator(
        self, admin_session: str, username: str, password: str, role: Role,
        *, queue_ids: Iterable[str] = (), resource_ids: Iterable[str] = (),
        grants: Iterable[Permission] = (),
    ) -> str:
        name = _username(username)
        _new_password(password)
        role = _validated_role(role)
        queues, resources = _scopes(queue_ids), _scopes(resource_ids)
        explicit = _grants(grants, role)
        salt = secrets.token_bytes(16)
        digest = _derive_password(password, salt)
        now = self._now()
        actor_id = secrets.token_hex(16)
        with self.auth._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            admin = self._require_admin(c, admin_session, now)
            c.execute(
                """INSERT INTO operators
                   (actor_id,tenant_id,username,role,password_salt,password_digest,created_epoch)
                   VALUES(?,?,?,?,?,?,?)""",
                (actor_id, admin.tenant_id, name, role.value, salt, digest, now),
            )
            self._replace_links(c, actor_id, "queue", queues)
            self._replace_links(c, actor_id, "resource", resources)
            c.executemany(
                "INSERT INTO operator_grants(actor_id,permission) VALUES(?,?)",
                ((actor_id, x.value) for x in sorted(explicit, key=lambda x: x.value)),
            )
            self._audit(c, now, admin.actor_id, admin.tenant_id, actor_id, "operator_created")
            c.commit()
        return actor_id

    def login_operator(self, tenant_id: str, username: str, password: str) -> str:
        tenant = _identifier(tenant_id)
        name = username.lower() if isinstance(username, str) else ""
        if not isinstance(password, str) or len(password) > 128 or len(password.encode("utf-8")) > 256:
            raise OperatorError("INVALID_CREDENTIALS")
        now = self._now()
        token = _random_secret()
        with self.auth._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM operator_sessions WHERE expires_epoch<=?", (now,))
            row = c.execute(
                "SELECT * FROM operators WHERE tenant_id=? AND username=?",
                (tenant, name),
            ).fetchone()
            # Dummy KDF even for unknown/disabled/bootstrap/locked users.
            valid_hash = bool(row and row["enabled"] and not row["is_bootstrap"]
                              and now >= row["locked_until"])
            salt = row["password_salt"] if valid_hash else _DUMMY_SALT
            expected = row["password_digest"] if valid_hash else "0" * 64
            supplied = _derive_password(password, salt)
            if not (valid_hash and hmac.compare_digest(supplied, expected)):
                if row and row["enabled"] and not row["is_bootstrap"] and now >= row["locked_until"]:
                    attempts = row["login_failures"] + 1
                    locked = now + LOCK_SECONDS if attempts >= MAX_ATTEMPTS else 0
                    c.execute(
                        """UPDATE operators SET login_failures=?,locked_until=?
                            WHERE actor_id=?""",
                        (attempts, locked, row["actor_id"]),
                    )
                c.commit()
                raise OperatorError("INVALID_CREDENTIALS")
            c.execute(
                "UPDATE operators SET login_failures=0,locked_until=0 WHERE actor_id=?",
                (row["actor_id"],),
            )
            c.execute(
                """INSERT INTO operator_sessions(digest,actor_id,issued_epoch,expires_epoch)
                   VALUES(?,?,?,?)""",
                (_fingerprint(token, "operator_session"), row["actor_id"],
                 now, now + SESSION_TTL_SECONDS),
            )
            self._audit(c, now, row["actor_id"], tenant, row["actor_id"], "operator_login")
            c.commit()
        return token

    def replace_rights(
        self, admin_session: str, actor_id: str, *,
        role: Role | None = None,
        queue_ids: Iterable[str] | None = None,
        resource_ids: Iterable[str] | None = None,
        grants: Iterable[Permission] | None = None,
    ) -> None:
        next_role = _validated_role(role) if role is not None else None
        queues = _scopes(queue_ids) if queue_ids is not None else None
        resources = _scopes(resource_ids) if resource_ids is not None else None
        now = self._now()
        with self.auth._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            admin = self._require_admin(c, admin_session, now)
            row = self._target(c, actor_id, admin.tenant_id)
            if row["is_bootstrap"]:
                raise OperatorError("BOOTSTRAP_ADMIN_IMMUTABLE")
            effective_role = next_role or Role(row["role"])
            if grants is None:
                current = [Permission(r["permission"]) for r in c.execute(
                    "SELECT permission FROM operator_grants WHERE actor_id=?", (actor_id,),
                )]
            else:
                current = grants
            explicit = _grants(current, effective_role)
            if next_role is not None:
                c.execute(
                    "UPDATE operators SET role=? WHERE actor_id=?",
                    (next_role.value, actor_id),
                )
            if queues is not None:
                self._replace_links(c, actor_id, "queue", queues)
            if resources is not None:
                self._replace_links(c, actor_id, "resource", resources)
            c.execute("DELETE FROM operator_grants WHERE actor_id=?", (actor_id,))
            c.executemany(
                "INSERT INTO operator_grants(actor_id,permission) VALUES(?,?)",
                ((actor_id, p.value) for p in sorted(explicit, key=lambda p: p.value)),
            )
            self._last_admin_guard(c, admin.tenant_id)
            self._invalidate(c, actor_id, False)
            self._audit(c, now, admin.actor_id, admin.tenant_id, actor_id, "rights_replaced")
            c.commit()

    def disable_operator(self, admin_session: str, actor_id: str) -> None:
        now = self._now()
        with self.auth._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            admin = self._require_admin(c, admin_session, now)
            row = self._target(c, actor_id, admin.tenant_id)
            if row["is_bootstrap"]:
                raise OperatorError("BOOTSTRAP_ADMIN_IMMUTABLE")
            c.execute("UPDATE operators SET enabled=0 WHERE actor_id=?", (actor_id,))
            self._last_admin_guard(c, admin.tenant_id)
            self._invalidate(c, actor_id, False)
            self._audit(c, now, admin.actor_id, admin.tenant_id, actor_id, "operator_disabled")
            c.commit()

    def reset_password(self, admin_session: str, actor_id: str, new_password: str) -> None:
        _new_password(new_password)
        salt = secrets.token_bytes(16)
        digest = _derive_password(new_password, salt)
        now = self._now()
        with self.auth._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            admin = self._require_admin(c, admin_session, now)
            row = self._target(c, actor_id, admin.tenant_id)
            if row["is_bootstrap"] or not row["enabled"]:
                raise OperatorError("AUTHZ_DENIED")
            c.execute(
                """UPDATE operators SET password_salt=?,password_digest=?,
                   login_failures=0,locked_until=0 WHERE actor_id=?""",
                (salt, digest, actor_id),
            )
            self._invalidate(c, actor_id, False)
            self._audit(c, now, admin.actor_id, admin.tenant_id, actor_id, "password_rotated")
            c.commit()

    def revoke_session(self, token: str) -> bool:
        if not isinstance(token, str) or not token or len(token) > 256:
            return False
        now = self._now()
        with self.auth._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            actor = self._account(c, token, now)
            if actor is None:
                c.commit()
                return False
            table, purpose = (
                ("local_sessions", "session") if actor["is_bootstrap"]
                else ("operator_sessions", "operator_session")
            )
            deleted = c.execute(
                f"DELETE FROM {table} WHERE digest=?",
                (_fingerprint(token, purpose),),
            ).rowcount
            if deleted:
                self._audit(c, now, actor["actor_id"], actor["tenant_id"],
                            actor["actor_id"], "operator_logout")
            c.commit()
        return deleted > 0
