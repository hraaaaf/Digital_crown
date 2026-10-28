"""Isolated DR-04 rehearsal: separate processes + file SQLCipher + Media Core AES-GCM.

This is NOT the guarded LOT06-B LAB service, not a clinical receipt nor a
power-cut guarantee. Only synthetic bytes and a private temporary directory.
Fail closed if SQLCipher3 is missing; never substitute plaintext SQLite.
"""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import os
from pathlib import Path
import re
import sys

from PIL import Image


TENANT, PATIENT = 31, 73  # synthetic fixture IDs, never user records
CAPTURE, DEVICE = "synthetic-DR-04", "synthetic-device"
RECEIPT = "SYNTH-DR-RECEIPT-01"
REASON = "LAB_UNSCHEDULED"
PRIMARY = """
CREATE TABLE IF NOT EXISTS synthetic_receipts (
    tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
    receipt_id TEXT NOT NULL UNIQUE, asset_id INTEGER NOT NULL UNIQUE,
    patient INTEGER NOT NULL, digest TEXT NOT NULL, size INTEGER NOT NULL,
    PRIMARY KEY(tenant, device, capture)
);
CREATE TABLE IF NOT EXISTS synthetic_audit (
    receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL,
    patient_only_reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS synthetic_outbox (
    receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL
);
"""


def _require_key(name: str) -> str:
    value = os.environ.get(name, "")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise RuntimeError("SYNTHETIC_TEST_KEY_REQUIRED")
    return value


def _open(root: Path, *, incorrect: bool = False):
    try:
        from sqlcipher3 import dbapi2 as sqlcipher
    except ImportError as exc:
        raise RuntimeError("SQLCIPHER_DRIVER_REQUIRED_NO_PLAINTEXT_FALLBACK") from exc
    key = "a" * 64 if incorrect else _require_key("DC06B_TEST_SQLCIPHER_KEY")
    con = sqlcipher.connect(str(root / "isolated-ledger.db"))
    try:
        con.execute(f"PRAGMA key = '{key}'")
        if not con.execute("PRAGMA cipher_version").fetchone():
            raise RuntimeError("SQLCIPHER_CIPHER_VERSION_UNAVAILABLE")
        con.execute("PRAGMA journal_mode=DELETE")
        con.execute("PRAGMA synchronous=FULL")
        # Actually try opening the encrypted page; PRAGMA key alone is not proof.
        con.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
    except Exception:
        con.close()
        raise
    return con


def _png(color: tuple[int, int, int]) -> bytes:
    output = BytesIO()
    Image.new("RGB", (8, 8), color=color).save(output, format="PNG")
    return output.getvalue()


def _blob(root: Path, payload: bytes) -> Path:
    from backend.services.clinical_asset_storage import _storage_key
    digest = hashlib.sha256(payload).hexdigest()
    return root / "media" / _storage_key(TENANT, digest)


def _store(root: Path, content: bytes) -> str:
    from backend.services.clinical_asset_storage import _atomic_write, _encrypt_payload
    digest = hashlib.sha256(content).hexdigest()
    path = _blob(root, content)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, _encrypt_payload(content, TENANT, digest))
    if path.read_bytes().startswith(content[:8]):
        raise RuntimeError("PLAINTEXT_MEDIA_WRITE")
    return digest


def _schema(con) -> None:
    for statement in PRIMARY.strip().split(";"):
        if statement.strip():
            con.execute(statement)
    con.commit()


def _assert_integrity(root: Path, con):
    from backend.services.clinical_asset_storage import _decrypt_payload
    rows = con.execute(
        "SELECT receipt_id,asset_id,patient,digest,size FROM synthetic_receipts "
        "WHERE tenant=? AND device=? AND capture=?",
        (TENANT, DEVICE, CAPTURE),
    ).fetchall()
    assert len(rows) == 1, "RECEIPT_NOT_UNIQUE"
    rid, asset_id, patient, digest, size = rows[0]
    assert rid == RECEIPT and asset_id == 1 and patient == PATIENT
    payload = _png((15, 45, 75))
    assert digest == hashlib.sha256(payload).hexdigest() and size == len(payload)
    path = _blob(root, payload)
    raw = path.read_bytes()
    assert raw.startswith(b"DCM1") and payload not in raw, "PLAINTEXT_MEDIA_ON_DISK"
    restored = _decrypt_payload(raw, TENANT, digest)
    assert restored == payload and hashlib.sha256(restored).hexdigest() == digest
    assert con.execute(
        "SELECT event,patient_only_reason FROM synthetic_audit WHERE receipt_id=?",
        (rid,),
    ).fetchone() == ("LAB_ACQUISITION_COMMITTED", REASON)
    assert con.execute(
        "SELECT event FROM synthetic_outbox WHERE receipt_id=?", (rid,)
    ).fetchone() == ("LAB_MEDIA_READY",)
    assert con.execute("SELECT COUNT(*) FROM synthetic_receipts").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM synthetic_audit").fetchone()[0] == 1
    assert con.execute("SELECT COUNT(*) FROM synthetic_outbox").fetchone()[0] == 1
    # File must be encrypted SQLCipher, never SQLite's recognizable plaintext header.
    header = (root / "isolated-ledger.db").read_bytes()[:16]
    assert header and header != b"SQLite format 3\x00", "PLAINTEXT_SQLITE_HEADER"


def _run(root: Path, phase: str):
    os.environ["CABINET_MASTER_KEY_HEX"] = _require_key("DC06B_TEST_MEDIA_KEY")
    if phase == "wrong-key":
        try:
            with _open(root, incorrect=True) as con:
                con.execute("SELECT COUNT(*) FROM synthetic_receipts").fetchone()
        except Exception:
            print("WRONG_SQLCIPHER_KEY_BLOCKED")
            return 0
        raise AssertionError("WRONG_KEY_WAS_ACCEPTED")
    if phase == "tamper":
        p = _blob(root, _png((15, 45, 75)))
        raw = bytearray(p.read_bytes())
        raw[-1] ^= 0x01
        p.write_bytes(raw)
        print("SYNTHETIC_MEDIA_CORRUPTED")
        return 0
    if phase == "verify-tampered":
        try:
            with _open(root) as con:
                _assert_integrity(root, con)
        except Exception:
            print("TAMPER_INTEGRITY_BLOCKED")
            return 0
        raise AssertionError("TAMPER_WAS_ACCEPTED")

    with _open(root) as con:
        if phase == "write":
            _schema(con)
            payload = _png((15, 45, 75))
            digest = _store(root, payload)  # ciphertext fsync BEFORE SQL commit
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO synthetic_receipts VALUES(?,?,?,?,?,?,?,?)",
                (TENANT, DEVICE, CAPTURE, RECEIPT, 1, PATIENT, digest, len(payload)),
            )
            con.execute(
                "INSERT INTO synthetic_audit VALUES(?,?,?)",
                (RECEIPT, "LAB_ACQUISITION_COMMITTED", REASON),
            )
            con.execute(
                "INSERT INTO synthetic_outbox VALUES(?,?)",
                (RECEIPT, "LAB_MEDIA_READY"),
            )
            con.commit()
            print("FILE_SQLCIPHER_AND_AESGCM_RECEIPT_COMMITTED")
        elif phase == "verify":
            _assert_integrity(root, con)
            print("RESTARTED_PROCESS_VERIFIED_RECEIPT_AND_MEDIA")
        elif phase == "replay":
            _assert_integrity(root, con)
            # Synthetic ledger replay never appends duplicate rows.
            assert con.execute(
                "SELECT receipt_id FROM synthetic_receipts WHERE "
                "tenant=? AND device=? AND capture=?",
                (TENANT, DEVICE, CAPTURE),
            ).fetchone() == (RECEIPT,)
            print("RESTART_REPLAY_SAME_RECEIPT")
        elif phase == "interrupt":
            payload = _png((95, 75, 35))
            digest = _store(root, payload)
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO synthetic_receipts VALUES(?,?,?,?,?,?,?,?)",
                (TENANT, DEVICE, "pending-interrupted", "SYNTH-INTERRUPTED",
                 2, PATIENT, digest, len(payload)),
            )
            con.execute(
                "INSERT INTO synthetic_audit VALUES(?,?,?)",
                ("SYNTH-INTERRUPTED", "LAB_ACQUISITION_COMMITTED", REASON),
            )
            # Abrupt OS process exit without SQL COMMIT. This is NOT a power cut.
            os._exit(73)
        elif phase == "verify-interrupted":
            _assert_integrity(root, con)
            assert con.execute(
                "SELECT COUNT(*) FROM synthetic_receipts WHERE capture='pending-interrupted'"
            ).fetchone()[0] == 0
            assert con.execute(
                "SELECT COUNT(*) FROM synthetic_audit WHERE receipt_id='SYNTH-INTERRUPTED'"
            ).fetchone()[0] == 0
            assert _blob(root, _png((95, 75, 35))).is_file()
            print("UNCOMMITTED_RECEIPT_ROLLED_BACK_ENCRYPTED_ORPHAN_QUARANTINED")
        else:
            raise AssertionError("UNKNOWN_SYNTHETIC_TEST_PHASE")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", choices=[
        "write", "verify", "replay", "interrupt", "verify-interrupted",
        "wrong-key", "tamper", "verify-tampered",
    ], required=True)
    opts = parser.parse_args()
    opts.root.mkdir(parents=True, exist_ok=True)
    try:
        sys.exit(_run(opts.root, opts.phase))
    except Exception as exc:
        # Never log synthetic keys, plaintext content, or patient-specific data.
        print("DURABILITY_REHEARSAL_FAIL", type(exc).__name__, file=sys.stderr)
        sys.exit(2)
