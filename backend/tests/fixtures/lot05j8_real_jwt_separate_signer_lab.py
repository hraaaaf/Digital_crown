"""05.7-J8 FAKE: independent signer invokes REAL backend JWT/user/permission guards.

Entire module exists under backend/tests/fixtures only. Signer & verifier are
separate subprocesses, with disjoint private/public keys. Privileges and pin
installation are supplied by SAME test user, so this IS NOT an SCM-authorized
production signer and cannot authorize clinical data restore.
"""
from __future__ import annotations

import asyncio
import base64
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

FLAG = "LOT05J8_REAL_JWT_SIGNER_FAKE_ONLY"
AUDIENCE = "LOT05J8_FAKE_WORKER"
FAKE_PATH = "inputs/lot05j8.payload.fake"
_BODY = frozenset({"version", "owner", "audience", "path", "nonce", "issued", "expires"})


class J8Denied(PermissionError):
    pass


def _root(value):
    if type(value) is not str:
        raise J8Denied("ROOT_STRING_REQUIRED")
    root = Path(value)
    if (not root.is_absolute() or not root.is_dir()
            or not root.name.startswith("lot05j8_fake_")
            or root.is_symlink() or root.is_junction()):
        raise J8Denied("FAKE_ROOT_ONLY")
    return root


def _file(path, length):
    if path.is_symlink() or path.is_junction() or not path.is_file():
        raise J8Denied("FAKE_PIN_OR_PRIVATE_FILE_MISSING")
    if path.stat().st_nlink != 1:
        raise J8Denied("FAKE_KEY_HARDLINK_DENIED")
    raw = path.read_bytes()
    if len(raw) != length:
        raise J8Denied("FAKE_KEY_LENGTH_DENIED")
    return raw


def _canonical(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _auth_real(token, owner):
    """The actual unmodified backend auth dependency runs against fake SQLCipher."""
    if type(token) is not str or not token or type(owner) is not int or owner <= 0:
        raise J8Denied("AUTHENTICATED_FAKE_OWNER_REQUIRED")
    from backend import database
    dbpath = database.engine.url.database or ""
    if os.name == "nt" and len(dbpath) >= 3 and dbpath[0] == "/" and dbpath[2] == ":":
        dbpath = dbpath[1:]
    dbpath = Path(dbpath)
    if (database.engine.driver != "pysqlcipher"
            or not dbpath.is_absolute() or not dbpath.is_file()
            or dbpath.name != "fake_source.db"
            or not dbpath.parent.name.startswith("lot05e_fake_sqlcipher_")):
        raise J8Denied("GENUINE_FAKE_SQLCIPHER_ENGINE_REQUIRED")
    import backend
    import types
    if "backend.routers" not in sys.modules:
        pkg = types.ModuleType("backend.routers")
        pkg.__package__ = "backend.routers"
        pkg.__path__ = [str(Path(__file__).resolve().parents[2] / "routers")]
        sys.modules["backend.routers"] = pkg
        backend.routers = pkg
    from backend.routers import auth, legacy_migration_v15
    from sqlalchemy.orm import Session
    from starlette.requests import Request
    scope = {
        "type":"http", "http_version":"1.1", "method":"GET",
        "scheme":"http", "path":"/api/legacy-migration/preflight",
        "raw_path":b"/api/legacy-migration/preflight", "query_string":b"",
        "headers":[], "client":("127.0.0.1",10401), "server":("localhost",8005)}
    with Session(database.engine) as db:
        principal = asyncio.run(auth.get_current_user(
            request=Request(scope), token_header=token, db=db))
        auth.require_permission("settings")(current_user=principal)
        legacy_migration_v15._owner_only(principal=principal)
        if principal.id != owner:
            raise J8Denied("JWT_SUBJECT_OWNER_DISAGREEMENT")
        return principal.id


def sign(root, message):
    if type(message) is not dict or set(message) != {"jwt", "owner"}:
        raise J8Denied("SIGNING_REQUEST_INVALID")
    owner = _auth_real(message["jwt"], message["owner"])
    private = _file(root / "signer-private.fake", 32)
    now = int(time.time())
    body = {"version":8, "owner":owner, "audience":AUDIENCE, "path":FAKE_PATH,
            "nonce":secrets.token_hex(16), "issued":now, "expires":now+90}
    signature = Ed25519PrivateKey.from_private_bytes(private).sign(_canonical(body))
    # Do not return a public key: verifier must load preinstalled test fixture pin.
    return {"body":body, "signature":base64.b64encode(signature).decode("ascii"),
            "signer_pid":os.getpid()}


def verify(root, message):
    if type(message) is not dict or set(message) != {"envelope"}:
        raise J8Denied("WORKER_REQUEST_INVALID")
    env = message["envelope"]
    if type(env) is not dict or set(env) != {"body", "signature", "signer_pid"}:
        raise J8Denied("SIGNED_ENVELOPE_SHAPE_DENIED")
    body = env["body"]
    if type(body) is not dict or set(body) != _BODY:
        raise J8Denied("FAKE_CLAIMS_SHAPE_DENIED")
    pin = root / "installed-public"
    if pin.is_symlink() or pin.is_junction() or not pin.is_dir():
        raise J8Denied("INSTALLED_PIN_DIR_REQUIRED")
    public = _file(pin / "trusted-ed25519.fake", 32)
    owner_file = pin / "owner.fake"
    if owner_file.is_symlink() or owner_file.is_junction() or not owner_file.is_file() or owner_file.stat().st_nlink != 1:
        raise J8Denied("INSTALLED_OWNER_PIN_REQUIRED")
    try:
        pinned_owner = int(owner_file.read_text(encoding="ascii"))
    except (ValueError, UnicodeError, OSError) as exc:
        raise J8Denied("INSTALLED_OWNER_INVALID") from exc
    try:
        signature = base64.b64decode(env["signature"], validate=True)
        if len(signature) != 64:
            raise ValueError("signature length")
        Ed25519PublicKey.from_public_bytes(public).verify(signature, _canonical(body))
    except Exception as exc:
        raise J8Denied("UNTRUSTED_FAKE_SIGNATURE") from exc
    now = int(time.time())
    if (type(body["version"]) is not int or body["version"] != 8
            or type(body["owner"]) is not int or body["owner"] != pinned_owner
            or pinned_owner <= 0 or type(body["audience"]) is not str or body["audience"] != AUDIENCE
            or type(body["path"]) is not str or body["path"] != FAKE_PATH
            or type(body["nonce"]) is not str or len(body["nonce"]) != 32
            or any(ch not in "0123456789abcdef" for ch in body["nonce"])
            or type(body["issued"]) is not int or type(body["expires"]) is not int
            or body["expires"] - body["issued"] != 90
            or not body["issued"] <= now < body["expires"]):
        raise J8Denied("WORKER_PINNED_CLAIMS_REJECTED")
    ledger = root / "worker-replay.sqlite"
    if ledger.is_symlink() or ledger.is_junction() or (ledger.exists() and
       (not ledger.is_file() or ledger.stat().st_nlink != 1)):
        raise J8Denied("REPLAY_LEDGER_UNTRUSTED")
    try:
        with closing(sqlite3.connect(str(ledger), timeout=10, isolation_level=None)) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE IF NOT EXISTS consumed(nonce TEXT PRIMARY KEY)")
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT INTO consumed(nonce) VALUES(?)", (body["nonce"],))
                db.commit()
            except BaseException:
                db.rollback()
                raise
    except sqlite3.IntegrityError as exc:
        raise J8Denied("SIGNED_JOB_REPLAY_DENIED") from exc
    except sqlite3.DatabaseError as exc:
        raise J8Denied("REPLAY_LEDGER_BROKEN") from exc
    return {"accepted":True, "fake_only":True, "worker_pid":os.getpid(),
            "owner":pinned_owner}


def main():
    if os.getenv(FLAG) != "1" or len(sys.argv) != 3:
        raise J8Denied("J8_TEST_ENVIRONMENT_REQUIRED")
    root = _root(sys.argv[2])
    request = json.loads(sys.stdin.read(65536))
    if sys.argv[1] == "sign":
        output = sign(root, request)
    elif sys.argv[1] == "verify":
        output = verify(root, request)
    else:
        raise J8Denied("FAKE_ROLE_REQUIRED")
    print(json.dumps(output, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Do not expose authentication token, keys, SQLCipher secrets or full trace.
        safe_code = ("HTTP_" + str(exc.status_code)
                     if type(exc).__name__ == "HTTPException"
                     else type(exc).__name__)
        print("J8_DENIED_" + safe_code, file=sys.stderr)
        sys.exit(61)
