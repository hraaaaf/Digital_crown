"""Synthetic-only, local SQLite durable CAS experiment for Digital Crown LOT06-M.

No network, patients, clinical ACK, independent trust root, real witness, or production
integration. Process-crash tests are NOT power-cut/SSD fsync or anti-rollback proof.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

AUTHORITY = "dc06m-cas-synthetic-only"
EPOCH = "SYNTHETIC_ONLY"
DOMAIN = b"DC06M|durable-sqlite-cas-lab|v1\x00"
GENESIS_MAC = "0" * 64
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_EVENT = 2048
MAX_LEDGER_RECORDS = 256
EVENT_KEYS = frozenset({"authority_id", "epoch", "scope", "op_id", "before_seq", "before_mac", "after_seq", "after_mac", "manifest_digest", "phase", "key_id"})


class CasRefusal(ValueError):
    """Fail-closed operation; never an accepted transition."""


def canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def event_bytes(e: dict[str, Any]) -> bytes:
    if type(e) is not dict or set(e) != EVENT_KEYS:
        raise CasRefusal("SCHEMA_REFUSE")
    if (e["authority_id"] != AUTHORITY or e["epoch"] != EPOCH
            or type(e["scope"]) is not str or not HEX32.fullmatch(e["scope"])
            or type(e["op_id"]) is not str or not HEX32.fullmatch(e["op_id"])
            or type(e["before_seq"]) is not int or not 0 <= e["before_seq"] < 1000000
            or type(e["after_seq"]) is not int or e["after_seq"] != e["before_seq"] + 1
            or type(e["before_mac"]) is not str or not HEX64.fullmatch(e["before_mac"])
            or type(e["after_mac"]) is not str or not HEX64.fullmatch(e["after_mac"])
            or type(e["manifest_digest"]) is not str or not HEX64.fullmatch(e["manifest_digest"])
            or type(e["phase"]) is not str or e["phase"] != "VERIFIED_SYNTHETIC"
            or type(e["key_id"]) is not str or not HEX32.fullmatch(e["key_id"])):
        raise CasRefusal("EVENT_REFUSE")
    raw = canonical(e)
    if len(raw) > MAX_EVENT:
        raise CasRefusal("EVENT_TOO_LARGE")
    return raw


def event(scope: str, op_id: str, before_seq: int, before_mac: str, after_mac: str) -> dict[str, Any]:
    """Pure deterministic fixture constructor; no real identity or patient values."""
    return {"authority_id": AUTHORITY, "epoch": EPOCH, "scope": scope, "op_id": op_id,
            "before_seq": before_seq, "before_mac": before_mac, "after_seq": before_seq + 1,
            "after_mac": after_mac, "manifest_digest": hashlib.sha256(b"synthetic-no-patient-media").hexdigest(),
            "phase": "VERIFIED_SYNTHETIC", "key_id": "1" * 32}


def signer_pub(signer: Ed25519PrivateKey) -> bytes:
    return signer.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                           format=serialization.PublicFormat.Raw)


def _require_lab_path(path: Path) -> None:
    """Defence in depth: cannot open/initialize app DB or non-temporary path."""
    if (not isinstance(path, Path) or path.name != "witness-synthetic.sqlite"
            or not path.is_absolute() or path.is_symlink()
            or not path.parent.name.startswith("dc06m-cas-synthetic-")
            or not path.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())):
        raise CasRefusal("NON_DISPOSABLE_LAB_PATH_REFUSE")


def _connect(path: Path) -> sqlite3.Connection:
    # mode=rw: a missing witness file must not silently initialize/rebase to genesis.
    _require_lab_path(path)
    conn = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=10.0)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA synchronous=FULL")  # process crash guarantee only, not physical power-loss evidence.
    if conn.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
        conn.close()
        raise CasRefusal("JOURNAL_MODE_NOT_DELETE")
    if conn.execute("PRAGMA synchronous").fetchone()[0] != 2:
        conn.close()
        raise CasRefusal("SYNC_NOT_FULL")
    return conn


def initialize(path: Path, scope: str, public_key: bytes) -> None:
    _require_lab_path(path)
    if type(scope) is not str or not HEX32.fullmatch(scope) or len(public_key) != 32:
        raise CasRefusal("ENROLLMENT_REFUSE")
    if path.exists():
        # Lab admission requires explicit one-time enrollment. No silent epoch reset.
        raise CasRefusal("WITNESS_ALREADY_EXISTS_REFUSE")
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)
    try:
        if conn.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
            raise CasRefusal("JOURNAL_MODE_REFUSE")
        conn.execute("PRAGMA synchronous=FULL")
        conn.executescript("""
        CREATE TABLE authority_head (
            authority TEXT NOT NULL, epoch TEXT NOT NULL, scope TEXT NOT NULL,
            seq INTEGER NOT NULL, mac TEXT NOT NULL, public_key BLOB NOT NULL,
            PRIMARY KEY (authority,epoch,scope)
        );
        CREATE TABLE decisions (
            authority TEXT NOT NULL, epoch TEXT NOT NULL, scope TEXT NOT NULL,
            op_id TEXT NOT NULL, request_bytes BLOB NOT NULL, receipt_bytes BLOB NOT NULL,
            seq_from INTEGER NOT NULL, seq_to INTEGER NOT NULL,
            PRIMARY KEY (authority,epoch,scope,op_id),
            UNIQUE (authority,epoch,scope,seq_to)
        );
        """)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO authority_head VALUES (?,?,?,?,?,?)",
                     (AUTHORITY, EPOCH, scope, 0, GENESIS_MAC, public_key))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def _receipt(e: dict[str, Any], request: bytes, signer: Ed25519PrivateKey) -> bytes:
    body = {"protocol": "DC06M_SQLITE_CAS_SYNTHETIC_V1", "decision": "ACCEPTED_LAB_NOT_CLINICAL",
            "authority_id": AUTHORITY, "epoch": EPOCH, "scope": e["scope"],
            "op_id": e["op_id"], "before_seq": e["before_seq"], "before_mac": e["before_mac"],
            "after_seq": e["after_seq"], "after_mac": e["after_mac"],
            "request_sha256": hashlib.sha256(request).hexdigest(), "manifest_digest": e["manifest_digest"]}
    signed = DOMAIN + canonical(body)
    packet = {"payload_b64": base64.b64encode(signed).decode("ascii"),
              "signature_b64": base64.b64encode(signer.sign(signed)).decode("ascii"),
              "signer_pin_sha256": hashlib.sha256(signer_pub(signer)).hexdigest()}
    return canonical(packet)


def verify_receipt(receipt: bytes, pub: bytes) -> dict[str, Any]:
    try:
        if len(receipt) > 4096 or len(pub) != 32:
            raise CasRefusal("RECEIPT_SIZE_REFUSE")
        p = json.loads(receipt)
        if set(p) != {"payload_b64", "signature_b64", "signer_pin_sha256"} or canonical(p) != receipt:
            raise CasRefusal("RECEIPT_SCHEMA_REFUSE")
        msg = base64.b64decode(p["payload_b64"], validate=True)
        signature = base64.b64decode(p["signature_b64"], validate=True)
        if (len(signature) != 64 or hashlib.sha256(pub).hexdigest() != p["signer_pin_sha256"]
                or not msg.startswith(DOMAIN)):
            raise CasRefusal("RECEIPT_PIN_REFUSE")
        Ed25519PublicKey.from_public_bytes(pub).verify(signature, msg)
        body = json.loads(msg[len(DOMAIN):])
        if canonical(body) != msg[len(DOMAIN):] or body.get("decision") != "ACCEPTED_LAB_NOT_CLINICAL":
            raise CasRefusal("RECEIPT_BODY_REFUSE")
        return body
    except CasRefusal:
        raise
    except (InvalidSignature, ValueError, KeyError, TypeError, UnicodeError, binascii.Error) as exc:
        raise CasRefusal("RECEIPT_VERIFY_REFUSE") from exc


def apply(path: Path, e: dict[str, Any], signer: Ed25519PrivateKey, *, failpoint: str = "") -> bytes:
    """Durable witness-domain local transaction, never an authorization to a clinic."""
    request = event_bytes(e)
    conn = _connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")  # cross-PROCESS serialization against same SQLite file
        head = conn.execute("SELECT seq,mac,public_key FROM authority_head WHERE authority=? AND epoch=? AND scope=?",
                            (AUTHORITY, EPOCH, e["scope"])).fetchone()
        if head is None or head[2] != signer_pub(signer):
            raise CasRefusal("UNKNOWN_SCOPE_OR_SIGNER_REFUSE")
        # Refuse extending ANY damaged or noncanonical existing ledger, not just a forged HEAD.
        _audit_connection(conn, e["scope"], head[2])
        found = conn.execute("SELECT request_bytes,receipt_bytes FROM decisions WHERE authority=? AND epoch=? AND scope=? AND op_id=?",
                             (AUTHORITY, EPOCH, e["scope"], e["op_id"])).fetchone()
        if found:
            if found[0] != request:
                raise CasRefusal("OP_ID_REBIND_REFUSE")
            # Identical replay always returns exact original receipt, even if HEAD advanced.
            b = verify_receipt(found[1], head[2])
            if b["request_sha256"] != hashlib.sha256(request).hexdigest() or b["op_id"] != e["op_id"]:
                raise CasRefusal("REPLAY_RECEIPT_MISMATCH")
            conn.commit()
            return bytes(found[1])
        if e["before_seq"] != head[0] or e["before_mac"] != head[1]:
            raise CasRefusal("STALE_OR_FORK_REFUSE")
        if head[0] >= MAX_LEDGER_RECORDS:
            raise CasRefusal("LEDGER_LIMIT_REFUSE")
        signed_receipt = _receipt(e, request, signer)  # generated within transaction
        conn.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?,?,?)",
                     (AUTHORITY, EPOCH, e["scope"], e["op_id"], request, signed_receipt,
                      e["before_seq"], e["after_seq"]))
        conn.execute("UPDATE authority_head SET seq=?,mac=? WHERE authority=? AND epoch=? AND scope=?",
                     (e["after_seq"], e["after_mac"], AUTHORITY, EPOCH, e["scope"]))
        if failpoint == "before_commit":
            os._exit(86)  # real process death while SQLite transaction uncommitted
        conn.commit()  # only AFTER this point can receipt be returned
        if failpoint == "after_commit":
            os._exit(87)  # durable commit, simulated lost ACK
        return signed_receipt
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def lookup(path: Path, scope: str, op_id: str, pub: bytes) -> bytes | None:
    """Read a decision; does not independently authenticate the freshest remote head."""
    if not HEX32.fullmatch(scope) or not HEX32.fullmatch(op_id):
        raise CasRefusal("LOOKUP_REFUSE")
    conn = _connect(path)
    try:
        conn.execute("BEGIN")  # consistent snapshot across audit and subsequent lookup
        _audit_connection(conn, scope, pub)
        record = conn.execute("SELECT request_bytes,receipt_bytes FROM decisions WHERE authority=? AND epoch=? AND scope=? AND op_id=?",
                              (AUTHORITY, EPOCH, scope, op_id)).fetchone()
        if record is None:
            return None
        request = json.loads(record[0])
        if event_bytes(request) != record[0]:
            raise CasRefusal("LEDGER_REQUEST_REFUSE")
        body = verify_receipt(record[1], pub)
        if (body["request_sha256"] != hashlib.sha256(record[0]).hexdigest()
                or any(body[k] != request[v] for k,v in (("scope","scope"),("op_id","op_id"),
                          ("before_seq","before_seq"),("after_seq","after_seq"),
                          ("before_mac","before_mac"),("after_mac","after_mac"),
                          ("manifest_digest","manifest_digest")))):
            raise CasRefusal("LEDGER_RECEIPT_MISMATCH")
        return bytes(record[1])
    finally:
        conn.close()


def _audit_connection(conn: sqlite3.Connection, scope: str, independent_pin: bytes) -> tuple[int, str, int]:
    """Validate all 256-or-fewer local records under one transaction snapshot."""
    head = conn.execute("SELECT seq,mac,public_key FROM authority_head WHERE authority=? AND epoch=? AND scope=?",
                        (AUTHORITY, EPOCH, scope)).fetchone()
    if head is None or head[2] != independent_pin or len(independent_pin) != 32:
        raise CasRefusal("HEAD_OR_PIN_REFUSE")
    rows = conn.execute("SELECT op_id,request_bytes,receipt_bytes,seq_from,seq_to FROM decisions WHERE authority=? AND epoch=? AND scope=? ORDER BY seq_to LIMIT ?",
                        (AUTHORITY, EPOCH, scope, MAX_LEDGER_RECORDS + 1)).fetchall()
    if len(rows) > MAX_LEDGER_RECORDS:
        raise CasRefusal("LEDGER_LIMIT_REFUSE")
    last_seq, last_mac = 0, GENESIS_MAC
    for op_id, raw, receipt, src, dst in rows:
        try:
            e = json.loads(raw)
            admitted = event_bytes(e)
        except (ValueError, TypeError, KeyError, UnicodeError) as exc:
            raise CasRefusal("LEDGER_EVENT_REFUSE") from exc
        if (admitted != raw or e["op_id"] != op_id or e["scope"] != scope
                or src != last_seq or dst != src + 1 or e["before_seq"] != src
                or e["after_seq"] != dst or e["before_mac"] != last_mac):
            raise CasRefusal("LEDGER_CHAIN_REFUSE")
        b = verify_receipt(receipt, independent_pin)
        if b["request_sha256"] != hashlib.sha256(raw).hexdigest() or any(
            b[k] != e[k] for k in ("before_seq", "before_mac", "after_seq", "after_mac", "op_id", "scope", "manifest_digest")):
            raise CasRefusal("LEDGER_SIGNATURE_BINDING_REFUSE")
        last_seq, last_mac = dst, e["after_mac"]
    if (last_seq, last_mac) != (head[0], head[1]):
        raise CasRefusal("HEAD_LEDGER_DIVERGENCE")
    return last_seq, last_mac, len(rows)


def audit(path: Path, scope: str, independent_pin: bytes) -> tuple[int, str, int]:
    """Audit local ledger integrity; old DB + old pin can still pass after rollback."""
    if type(scope) is not str or not HEX32.fullmatch(scope):
        raise CasRefusal("AUDIT_SCOPE_REFUSE")
    conn = _connect(path)
    try:
        conn.execute("BEGIN")  # consistent snapshot over head and complete bounded ledger
        return _audit_connection(conn, scope, independent_pin)
    except CasRefusal:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise CasRefusal("AUDIT_REFUSE") from exc
    finally:
        conn.close()

def _child() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-child", action="store_true", required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--failpoint", choices=["", "before_commit", "after_commit"], default="")
    args = parser.parse_args()
    data = json.load(sys.stdin)  # ephemeral synthetic TEST key through PIPE, not env, file or stdout
    key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(data["test_private_b64"], validate=True))
    if args.gate:
        # Test-only marker proves BOTH independently launched child processes reached barrier.
        (args.gate.parent / ("ready-" + str(os.getpid()))).touch()
        end = time.monotonic() + 10
        while not args.gate.exists():
            if time.monotonic() > end:
                raise RuntimeError("GATE_TIMEOUT")
            time.sleep(0.005)
    try:
        receipt = apply(args.db, data["event"], key, failpoint=args.failpoint)
        print(json.dumps({"status": "DECIDED_LAB_ONLY", "receipt_b64": base64.b64encode(receipt).decode("ascii")}))
    except CasRefusal as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}))


if __name__ == "__main__":
    _child()
