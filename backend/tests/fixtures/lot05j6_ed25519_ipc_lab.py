"""J6 separate-process Ed25519 signer and verifier, synthetic FAKE orders.

A test sends a JSON document to a disposable signer subprocess, which makes
an in-memory private Ed25519 key. A DIFFERENT verifier process only receives
the chosen/pinned public key and the signed envelope. The test is responsible
for pinning the key; no real trusted signer, SCM or clinical user is attested.
"""
from __future__ import annotations

import base64
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
from cryptography.hazmat.primitives import serialization

FLAG = "LOT05J6_ED25519_IPC_FAKE_ONLY"
AUDIENCE = "LOT05J6_DISPOSABLE_FAKE_WORKER"
PATH = "inputs/fake-ticket-payload"
PAYLOAD = b"LOT05J6_SIGNED_FAKE_ONLY"
BODY_KEYS = {"nonce", "owner", "audience", "path", "sha256", "issued", "expires"}


class IPCDenied(PermissionError):
    pass


def canon(document):
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def check_body(body, owner, now):
    if (type(body) is not dict or set(body) != BODY_KEYS
            or type(owner) is not int or owner <= 0
            or type(now) is not int or now <= 0
            or type(body["owner"]) is not int or body["owner"] != owner
            or body["audience"] != AUDIENCE or body["path"] != PATH
            or type(body["audience"]) is not str or type(body["path"]) is not str
            or type(body["nonce"]) is not str or len(body["nonce"]) != 32
            or any(c not in "0123456789abcdef" for c in body["nonce"])
            or type(body["sha256"]) is not str
            or body["sha256"] != hashlib.sha256(PAYLOAD).hexdigest()
            or type(body["issued"]) is not int
            or type(body["expires"]) is not int
            or body["expires"] - body["issued"] != 120
            or body["issued"] <= 0
            or not (body["issued"] <= now < body["expires"])):
        raise IPCDenied("J6_FAKE_CLAIMS_DENIED")


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def raw(text):
    if type(text) is not str:
        raise IPCDenied("J6_BASE64_TYPE_DENIED")
    try:
        return base64.b64decode(text, validate=True)
    except Exception as exc:
        raise IPCDenied("J6_BASE64_MALFORMED") from exc


def signer(request):
    if set(request) != {"body"}:
        raise IPCDenied("J6_SIGN_REQUEST_INVALID")
    body = request["body"]
    # Signer has no trustworthy access to source authentication. Only FAKE.
    check_body(body, body.get("owner") if type(body) is dict else None,
               body.get("issued") if type(body) is dict else None)
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)
    return {"envelope": {"body": body, "sig": b64(key.sign(canon(body)))},
            "public_key": b64(pub), "signer_pid": os.getpid()}


def _root(path):
    root = Path(path)
    if (not root.is_absolute() or not root.name.startswith("lot05j6_fake_")
            or root.is_symlink() or root.is_junction() or not root.is_dir()):
        raise IPCDenied("J6_SIGNED_LEDGER_FAKE_ROOT_REQUIRED")
    return root


def verify(request):
    if type(request) is not dict or set(request) != {
            "envelope", "trusted_pub", "owner", "now", "root"}:
        raise IPCDenied("J6_VERIFY_REQUEST_INVALID")
    env = request["envelope"]
    if type(env) is not dict or set(env) != {"body", "sig"}:
        raise IPCDenied("J6_ENVELOPE_INVALID")
    pub = raw(request["trusted_pub"])
    sig = raw(env["sig"])
    if len(pub) != 32 or len(sig) != 64:
        raise IPCDenied("J6_ED25519_SIZE_DENIED")
    try:
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, canon(env["body"]))
    except Exception as exc:
        raise IPCDenied("J6_ED25519_SIGNATURE_DENIED") from exc
    check_body(env["body"], request["owner"], request["now"])
    root = _root(request["root"])
    ledger = root / "j6-nonces.sqlite"
    if ledger.is_symlink() or ledger.is_junction():
        raise IPCDenied("J6_LEDGER_REDIRECT_DENIED")
    if ledger.exists() and (not ledger.is_file() or ledger.stat().st_nlink != 1):
        raise IPCDenied("J6_LEDGER_HARDLINK_DENIED")
    try:
        with closing(sqlite3.connect(str(ledger), timeout=10, isolation_level=None)) as db:
            db.execute("PRAGMA busy_timeout=10000")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE IF NOT EXISTS tickets(nonce TEXT PRIMARY KEY)")
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT INTO tickets(nonce) VALUES(?)", (env["body"]["nonce"],))
                db.commit()
            except BaseException:
                db.rollback()
                raise
    except sqlite3.IntegrityError as exc:
        raise IPCDenied("J6_SIGNED_NONCE_REPLAY") from exc
    except sqlite3.DatabaseError as exc:
        raise IPCDenied("J6_LEDGER_NOT_AVAILABLE") from exc
    return {"accepted": True, "verifier_pid": os.getpid(), "fake_only": True}


def main():
    if os.environ.get(FLAG) != "1" or len(sys.argv) != 2:
        raise IPCDenied("J6_ED25519_FAKE_ONLY_DISABLED")
    request = json.loads(sys.stdin.read(65536))
    if sys.argv[1] == "sign":
        answer = signer(request)
    elif sys.argv[1] == "verify":
        answer = verify(request)
    else:
        raise IPCDenied("J6_UNKNOWN_ROLE")
    print(json.dumps(answer, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (IPCDenied, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print("J6_DENIED_" + type(exc).__name__, file=sys.stderr)
        sys.exit(61)
