"""Isolated local-first bootstrap and session store for Queue Core (LOT08.2-A).

Only opaque, random credentials are returned. Authentication/recovery hashes
and minimal audit facts are persisted in a dedicated SQLite file, NEVER inside
Digital Crown clinical databases. No network listener or actual Windows
installer is implemented in this sublot.

The privileged Windows-console guard is intentionally required inside every
bootstrap/enroll/recovery method, not just in the CLI. Tests inject a guard
only against temporary synthetic databases.
"""
from __future__ import annotations

import hashlib
import hmac
from contextlib import contextmanager
from pathlib import Path
import re
import secrets
import sqlite3
import time
from collections.abc import Callable


class LocalIdentityError(Exception):
    """Stable, non-sensitive error code; never include a token or password."""


BOOTSTRAP_TTL_SECONDS = 600
SESSION_TTL_SECONDS = 8 * 3600
MAX_ATTEMPTS = 5
LOCK_SECONDS = 900
_PASSWORD_SCRYPT_N = 1 << 15
# A dummy hash prevents the account-existence path from skipping its KDF.
_DUMMY_SALT = bytes.fromhex("a8ee25fd3fe27a336c2d6a2f692bd917")


def _random_secret() -> str:
    return secrets.token_urlsafe(32)


def _fingerprint(value: str, purpose: str) -> str:
    return hashlib.sha256((purpose + "\x00" + value).encode("utf-8")).hexdigest()


def _derive_password(value: str, salt: bytes) -> str:
    return hashlib.scrypt(
        value.encode("utf-8"), salt=salt, n=_PASSWORD_SCRYPT_N,
        r=8, p=1, dklen=32, maxmem=64 * 1024 * 1024,
    ).hex()


def _new_password(value: str) -> None:
    if (not isinstance(value, str) or not 14 <= len(value) <= 128
            or "\x00" in value or len(value.encode("utf-8")) > 256):
        raise LocalIdentityError("PASSWORD_POLICY")


def _username(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9._-]{3,64}", value):
        raise LocalIdentityError("USERNAME_POLICY")
    return value.lower()


class LocalIdentityStore:
    """Single-server, single-admin seed until multi-user authorization in 08.2-B.

    The future service must establish filesystem ACLs and authenticate each
    request before invoking this store. No file is created by importing it.
    """

    def __init__(
        self, db_path: str | Path, *,
        local_guard: Callable[[], None] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        from .windows_console import require_local_windows_admin_console
        self.path = Path(db_path)
        self._guard = local_guard or require_local_windows_admin_console
        self._clock = clock

    def _now(self) -> int:
        return int(self._clock())

    @contextmanager
    def _connect(self, *, initialize: bool = False):
        if not initialize and not self.path.is_file():
            raise LocalIdentityError("LOCAL_AUTH_NOT_INITIALIZED")
        # The Windows CLI prepares an ACL-restricted directory before creating
        # the file. This store does not silently create parent directories.
        connection = sqlite3.connect(
            str(self.path), timeout=5, isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA secure_delete=ON")
        connection.execute("PRAGMA synchronous=FULL")
        try:
            yield connection
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _schema(connection: sqlite3.Connection) -> None:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS auth_meta (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                challenge_digest TEXT,
                challenge_expires INTEGER,
                challenge_failures INTEGER NOT NULL DEFAULT 0,
                recovery_digest TEXT,
                recovery_failures INTEGER NOT NULL DEFAULT 0,
                recovery_locked_until INTEGER NOT NULL DEFAULT 0,
                login_failures INTEGER NOT NULL DEFAULT 0,
                login_locked_until INTEGER NOT NULL DEFAULT 0
            );
            INSERT OR IGNORE INTO auth_meta (id) VALUES (1);
            CREATE TABLE IF NOT EXISTS local_admin (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                username TEXT NOT NULL UNIQUE,
                password_salt BLOB NOT NULL,
                password_digest TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS local_sessions (
                digest TEXT PRIMARY KEY NOT NULL,
                issued_epoch INTEGER NOT NULL,
                expires_epoch INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS local_auth_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epoch INTEGER NOT NULL,
                action TEXT NOT NULL,
                outcome TEXT NOT NULL
            );
        """)

    @staticmethod
    def _audit(c: sqlite3.Connection, now: int, action: str, outcome: str) -> None:
        c.execute(
            "INSERT INTO local_auth_audit (epoch, action, outcome) VALUES (?, ?, ?)",
            (now, action, outcome),
        )

    def begin_bootstrap(self) -> str:
        """Issue a 10-minute, one-time, high-entropy challenge at local console."""
        self._guard()
        now = self._now()
        challenge = _random_secret()
        with self._connect(initialize=True) as c:
            self._schema(c)
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM local_admin WHERE id=1").fetchone():
                raise LocalIdentityError("BOOTSTRAP_ALREADY_CLAIMED")
            c.execute(
                """UPDATE auth_meta
                   SET challenge_digest=?, challenge_expires=?, challenge_failures=0
                   WHERE id=1""",
                (_fingerprint(challenge, "bootstrap"), now + BOOTSTRAP_TTL_SECONDS),
            )
            self._audit(c, now, "bootstrap_issued", "ok")
            c.commit()
        return challenge  # caller must show once and never log/store it

    def enroll_first_admin(self, challenge: str, username: str, password: str) -> str:
        """Consume challenge and create exactly one administrator atomically.

        Returns the recovery secret ONCE; NEVER store it in a normal backup.
        """
        self._guard()
        name = _username(username)
        _new_password(password)
        now = self._now()
        salt = secrets.token_bytes(16)
        digest = _derive_password(password, salt)
        recovery = _random_secret()
        result = "BOOTSTRAP_INVALID"
        with self._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM local_admin WHERE id=1").fetchone():
                raise LocalIdentityError("BOOTSTRAP_ALREADY_CLAIMED")
            state = c.execute("SELECT * FROM auth_meta WHERE id=1").fetchone()
            if state is None:
                raise LocalIdentityError("LOCAL_AUTH_NOT_INITIALIZED")
            if state["challenge_failures"] >= MAX_ATTEMPTS:
                result = "BOOTSTRAP_LOCKED"
            elif (
                state["challenge_digest"] is None
                or state["challenge_expires"] is None
                or now >= state["challenge_expires"]
                or not isinstance(challenge, str)
                or not hmac.compare_digest(
                    _fingerprint(challenge, "bootstrap"), state["challenge_digest"]
                )
            ):
                c.execute(
                    "UPDATE auth_meta SET challenge_failures=challenge_failures+1 WHERE id=1"
                )
                self._audit(c, now, "bootstrap_claim", "denied")
            else:
                c.execute(
                    "INSERT INTO local_admin (id, username, password_salt, password_digest)"
                    " VALUES (1, ?, ?, ?)",
                    (name, salt, digest),
                )
                c.execute(
                    """UPDATE auth_meta SET challenge_digest=NULL,
                       challenge_expires=NULL, challenge_failures=0,
                       recovery_digest=?, recovery_failures=0,
                       recovery_locked_until=0, login_failures=0,
                       login_locked_until=0 WHERE id=1""",
                    (_fingerprint(recovery, "recovery"),),
                )
                self._audit(c, now, "bootstrap_claim", "ok")
                result = "ok"
            c.commit()
        if result != "ok":
            raise LocalIdentityError(result)
        return recovery

    def login(self, username: str, password: str) -> str:
        """Opaque session issue; no public network listener exists in 08.2-A."""
        now = self._now()
        name = username.lower() if isinstance(username, str) else ""
        if not isinstance(password, str) or len(password) > 128 or len(password.encode("utf-8")) > 256:
            raise LocalIdentityError("INVALID_CREDENTIALS")
        result = "INVALID_CREDENTIALS"
        session = _random_secret()
        with self._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            meta = c.execute("SELECT * FROM auth_meta WHERE id=1").fetchone()
            admin = c.execute("SELECT * FROM local_admin WHERE id=1").fetchone()
            if meta is None or admin is None:
                raise LocalIdentityError("LOCAL_AUTH_NOT_INITIALIZED")
            # Expired session digests are not retained forever. Prune within
            # the same serialized login transaction, even on denied logins.
            c.execute(
                "DELETE FROM local_sessions WHERE expires_epoch <= ?", (now,)
            )
            if now < meta["login_locked_until"]:
                result = "TEMPORARILY_LOCKED"
            else:
                # Constant-time comparison of password hashes; always run KDF.
                salt = admin["password_salt"] if name == admin["username"] else _DUMMY_SALT
                expected = admin["password_digest"] if name == admin["username"] else "0" * 64
                supplied = _derive_password(password, salt)
                if hmac.compare_digest(supplied, expected) and name == admin["username"]:
                    c.execute(
                        "UPDATE auth_meta SET login_failures=0,login_locked_until=0 WHERE id=1"
                    )
                    c.execute(
                        "INSERT INTO local_sessions (digest, issued_epoch, expires_epoch)"
                        " VALUES (?, ?, ?)",
                        (_fingerprint(session, "session"), now, now + SESSION_TTL_SECONDS),
                    )
                    self._audit(c, now, "login", "ok")
                    result = "ok"
                else:
                    attempts = meta["login_failures"] + 1
                    locked = now + LOCK_SECONDS if attempts >= MAX_ATTEMPTS else 0
                    c.execute(
                        "UPDATE auth_meta SET login_failures=?, login_locked_until=? WHERE id=1",
                        (attempts, locked),
                    )
                    self._audit(c, now, "login", "denied")
            c.commit()
        if result != "ok":
            raise LocalIdentityError(result)
        return session

    def session_valid(self, session: str) -> bool:
        if not isinstance(session, str) or not session:
            return False
        with self._connect() as c:
            row = c.execute(
                "SELECT expires_epoch FROM local_sessions WHERE digest=?",
                (_fingerprint(session, "session"),),
            ).fetchone()
        return row is not None and self._now() < row["expires_epoch"]

    def revoke_session(self, session: str) -> bool:
        if not isinstance(session, str) or not session:
            return False
        now = self._now()
        with self._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            cursor = c.execute(
                "DELETE FROM local_sessions WHERE digest=?",
                (_fingerprint(session, "session"),),
            )
            if cursor.rowcount:
                self._audit(c, now, "logout", "ok")
            c.commit()
            return cursor.rowcount > 0

    def recover_admin(self, recovery_secret: str, new_password: str) -> str:
        """Local elevated console only; rotate recovery and revoke all sessions.

        Atomic: a previous offline secret cannot be used after recovery.
        """
        self._guard()
        _new_password(new_password)
        now = self._now()
        salt = secrets.token_bytes(16)
        password_digest = _derive_password(new_password, salt)
        new_recovery = _random_secret()
        result = "RECOVERY_INVALID"
        with self._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            meta = c.execute("SELECT * FROM auth_meta WHERE id=1").fetchone()
            admin = c.execute("SELECT 1 FROM local_admin WHERE id=1").fetchone()
            if meta is None or admin is None:
                raise LocalIdentityError("LOCAL_AUTH_NOT_INITIALIZED")
            if now < meta["recovery_locked_until"]:
                result = "RECOVERY_LOCKED"
            elif (
                not isinstance(recovery_secret, str)
                or not meta["recovery_digest"]
                or not hmac.compare_digest(
                    _fingerprint(recovery_secret, "recovery"), meta["recovery_digest"]
                )
            ):
                attempts = meta["recovery_failures"] + 1
                locked = now + LOCK_SECONDS if attempts >= MAX_ATTEMPTS else 0
                c.execute(
                    "UPDATE auth_meta SET recovery_failures=?, recovery_locked_until=? WHERE id=1",
                    (attempts, locked),
                )
                self._audit(c, now, "recovery", "denied")
            else:
                c.execute(
                    "UPDATE local_admin SET password_salt=?, password_digest=? WHERE id=1",
                    (salt, password_digest),
                )
                c.execute("DELETE FROM local_sessions")
                c.execute(
                    """UPDATE auth_meta SET recovery_digest=?,
                       recovery_failures=0, recovery_locked_until=0,
                       login_failures=0, login_locked_until=0,
                       challenge_digest=NULL, challenge_expires=NULL WHERE id=1""",
                    (_fingerprint(new_recovery, "recovery"),),
                )
                self._audit(c, now, "recovery", "ok")
                result = "ok"
            c.commit()
        if result != "ok":
            raise LocalIdentityError(result)
        return new_recovery

    def is_initialized(self) -> bool:
        with self._connect() as c:
            return c.execute("SELECT 1 FROM local_admin WHERE id=1").fetchone() is not None
