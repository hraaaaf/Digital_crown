"""LOT05.7-J4: isolated adversarial file path + signed FAKE job laboratory.

NOT an application worker. No real user, patient, auth, key vault, SCM or
clinical restore. No imports into runtime service/routers. Windows handles and
persistent machine keys remain explicitly OUT OF SCOPE.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import stat
import time

FLAG = "LOT05J4_SIGNED_JOB_NTFS_FAKE_ONLY"
PAYLOAD = b"J4_DISPOSABLE_FAKE_PAYLOAD"
_NAME = "inputs/payload.fake"
_WORKER = "J4_FAKE_WORKER"
_KEYS = frozenset({"version", "nonce", "owner", "worker", "path",
                   "sha256", "issued", "expires"})


class J4Denied(PermissionError):
    pass


def _root(root: Path) -> Path:
    if (os.getenv(FLAG) != "1" or not isinstance(root, Path)
            or not root.is_absolute() or not root.name.startswith("lot05j4_fake_")
            or root.is_symlink() or root.is_junction() or not root.is_dir()):
        raise J4Denied("FAKE_ROOT_REQUIRED")
    return root


def _valid_key(key: object) -> bytes:
    if type(key) is not bytes or len(key) != 32:
        raise J4Denied("EPHEMERAL_FAKE_HMAC_KEY_REQUIRED")
    return key


def _owner(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise J4Denied("EXPLICIT_FAKE_OWNER_REQUIRED")
    return value


def _path_part_safe(path: Path) -> None:
    if path.is_symlink() or path.is_junction():
        raise J4Denied("REPARSE_OR_SYMLINK_DENIED")
    try:
        info = path.lstat()
    except OSError as exc:
        raise J4Denied("FAKE_PATH_UNREADABLE") from exc
    if info.st_nlink != 1 and stat.S_ISREG(info.st_mode):
        raise J4Denied("HARDLINK_DENIED")
    if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
        raise J4Denied("UNSUPPORTED_FAKE_PATH_TYPE")


def safe_fake_read(root: Path, *, attack_hook=None) -> bytes:
    """Recheck path, then compare open handle identity against pre-check.

    Evidence of rejection on synthetic races only, NOT full Windows TOCTOU
    prevention: Path checks and os.open are NOT Windows reparse-safe handles.
    """
    base = _root(root)
    folder = base / "inputs"
    target = folder / "payload.fake"
    try:
        _path_part_safe(base)
        _path_part_safe(folder)
        _path_part_safe(target)
        if not folder.is_dir() or not target.is_file():
            raise J4Denied("FAKE_SOURCE_REQUIRED")
        if (folder.resolve(strict=True) != base.resolve(strict=True) / "inputs"
                or target.resolve(strict=True) != base.resolve(strict=True) / _NAME):
            raise J4Denied("FAKE_PATH_ESCAPED")
        before = target.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise J4Denied("FAKE_FILE_NOT_REGULAR")
        if attack_hook is not None:
            attack_hook()
        # Exposes precisely the intended race boundary to adversarial tests.
        _path_part_safe(base)
        _path_part_safe(folder)
        _path_part_safe(target)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(target, flags)
        try:
            opened = os.fstat(fd)
            if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                    or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)):
                raise J4Denied("PATH_SWAP_DETECTED")
            result = os.read(fd, 1024)
            if os.read(fd, 1) or not hmac.compare_digest(result, PAYLOAD):
                raise J4Denied("FAKE_PAYLOAD_MISMATCH")
            return result
        finally:
            os.close(fd)
    except J4Denied:
        raise
    except (OSError, ValueError) as exc:
        raise J4Denied("FAKE_FILE_INSPECTION_FAILED") from exc


def _canonical(document: dict) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def sign_fake_job(root: Path, *, owner: object, key: object,
                  now: object, nonce: str | None = None) -> dict:
    _root(root)
    _owner(owner)
    _valid_key(key)
    if type(now) is not int or now <= 0:
        raise J4Denied("FAKE_CLOCK_REQUIRED")
    data = safe_fake_read(root)
    token = secrets.token_hex(16) if nonce is None else nonce
    if type(token) is not str or len(token) != 32 or any(c not in "0123456789abcdef" for c in token):
        raise J4Denied("FAKE_NONCE_INVALID")
    body = {"version": 1, "nonce": token, "owner": owner, "worker": _WORKER,
            "path": _NAME, "sha256": hashlib.sha256(data).hexdigest(),
            "issued": now, "expires": now + 120}
    mac = hmac.new(key, _canonical(body), hashlib.sha256).hexdigest()
    return {"body": body, "mac": mac}


def _validate_envelope(envelope: object, *, key: bytes, owner: int, now: int) -> dict:
    if type(envelope) is not dict or set(envelope) != {"body", "mac"}:
        raise J4Denied("FAKE_ENVELOPE_INVALID")
    body, mac = envelope["body"], envelope["mac"]
    if (type(body) is not dict or set(body) != _KEYS or type(mac) is not str
            or len(mac) != 64 or any(c not in "0123456789abcdef" for c in mac)):
        raise J4Denied("FAKE_ENVELOPE_INVALID")
    good = hmac.new(key, _canonical(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(good, mac):
        raise J4Denied("FAKE_JOB_SIGNATURE_INVALID")
    if (type(body["version"]) is not int or body["version"] != 1
            or type(body["owner"]) is not int or body["owner"] != owner
            or body["worker"] != _WORKER or type(body["worker"]) is not str
            or body["path"] != _NAME or type(body["path"]) is not str
            or type(body["nonce"]) is not str or len(body["nonce"]) != 32
            or any(c not in "0123456789abcdef" for c in body["nonce"])
            or type(body["sha256"]) is not str or len(body["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in body["sha256"])
            or type(body["issued"]) is not int or type(body["expires"]) is not int
            or body["issued"] <= 0 or body["expires"] - body["issued"] != 120
            or not (body["issued"] <= now < body["expires"])):
        raise J4Denied("FAKE_JOB_CLAIMS_INVALID")
    return body


def _ledger(root: Path) -> Path:
    path = root / "j4_replays.sqlite"
    if path.exists():
        _path_part_safe(path)
        if not path.is_file():
            raise J4Denied("LEDGER_NOT_REGULAR")
    return path


def consume_fake_job(root: Path, envelope: object, *, owner: object,
                     key: object, now: object, attack_hook=None) -> bytes:
    """Verifies fake job and commits its nonce once, with SQLite uniqueness.

    The HMAC key and owner are caller-supplied fake values, NOT actual
    authenticated JWT principal or SCM-only machine secret.
    """
    _root(root)
    trusted_owner = _owner(owner)
    secret = _valid_key(key)
    if type(now) is not int or now <= 0:
        raise J4Denied("FAKE_CLOCK_REQUIRED")
    body = _validate_envelope(envelope, key=secret, owner=trusted_owner, now=now)
    data = safe_fake_read(root, attack_hook=attack_hook)
    if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), body["sha256"]):
        raise J4Denied("FAKE_CONTENT_DIGEST_CHANGED")
    location = _ledger(root)
    try:
        with closing(sqlite3.connect(str(location), timeout=10, isolation_level=None)) as db:
            db.execute("PRAGMA busy_timeout=10000")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE IF NOT EXISTS nonces (nonce TEXT PRIMARY KEY, owner INTEGER NOT NULL)")
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT INTO nonces(nonce, owner) VALUES(?,?)",
                           (body["nonce"], trusted_owner))
                db.commit()
            except BaseException:
                db.rollback()
                raise
        return data
    except sqlite3.IntegrityError as exc:
        raise J4Denied("SIGNED_JOB_REPLAY_DENIED") from exc
    except sqlite3.DatabaseError as exc:
        raise J4Denied("SIGNED_JOB_LEDGER_UNAVAILABLE") from exc
