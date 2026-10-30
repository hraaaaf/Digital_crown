"""LOT06 C05B-03E physical-event evidence collector, TEST-ONLY.

This tool NEVER cuts power, reboots a host, certifies durable clinical receipts,
or accesses a Digital Crown cabinet DB. It prepares exclusively synthetic
SQLCipher/AES-GCM media on an operator-designated isolated path. An independent
witness MUST be copied off the device before an external physical experiment.
Even a successful cold recovery is NOT self-attested as a physical power loss.

Ref: https://www.sqlite.org/pragma.html#pragma_synchronous
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import sys
import time
from datetime import datetime, timezone

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlcipher3 import dbapi2 as sqlcipher

BENCH_PREFIX = "lot06c05b03e-"
PAYLOAD = b"DC-C05B03E-SYNTHETIC-TEST-IMAGE-NO-PATIENT"
POLICIES = {"NORMAL": 1, "FULL": 2}
MANIFEST = "pre_event_manifest.json"
PRIVATE = "lab-secrets.private.json"
CLINICAL_CERTIFIED = False


class EvidenceRejected(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _guard():
    if not (os.environ.get("ENVIRONMENT") == "test"
            and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
            and os.environ.get("DC06C05B03E_TEST_ONLY") == "1"):
        raise EvidenceRejected("ISOLATED_LAB_ONLY")


def _root_guard(root: Path):
    _guard()
    root = Path(root).absolute()
    if not root.name.startswith(BENCH_PREFIX):
        raise EvidenceRejected("ISOLATED_ROOT_NAME_REQUIRED")
    if root.is_symlink() or not root.parent.is_dir():
        raise EvidenceRejected("INVALID_ISOLATED_ROOT")
    if root.exists() and not root.is_dir():
        raise EvidenceRejected("INVALID_ISOLATED_ROOT")
    return root


def _atomic_private_file(path: Path, data: bytes):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(str(path), flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    os.chmod(path, 0o600)


def _sync_dir(root: Path):
    if os.name != "posix":
        raise EvidenceRejected("NON_POSIX_DIRECTORY_BARRIER_UNVERIFIED")
    fd = os.open(str(root), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _open_db(root: Path, key: str, mode: str):
    if mode not in POLICIES:
        raise EvidenceRejected("INVALID_POLICY")
    db = sqlcipher.connect(str(root / "bench.sqlcipher"), isolation_level=None, timeout=15)
    try:
        db.execute("PRAGMA key = \"" + key + "\"")
        if not db.execute("PRAGMA cipher_version").fetchone():
            raise EvidenceRejected("SQLCIPHER_DRIVER_REQUIRED")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=" + mode)
        db.execute("PRAGMA wal_autocheckpoint=0")
        if (db.execute("PRAGMA journal_mode").fetchone()[0].lower() != "wal"
                or db.execute("PRAGMA synchronous").fetchone()[0] != POLICIES[mode]):
            raise EvidenceRejected("WRITER_POLICY_INCORRECT")
        return db
    except BaseException:
        db.close()
        raise


def prepare(root: Path, mode: str):
    """Return (public witness, open SQLCipher handle). Caller owns the handle.

    Holding the handle open retains an active WAL writer process for the operator
    to interrupt physically. For isolated pytest tests, closing it gives ONLY a
    software-restart check (not a meaningful on-disk WAL power-failure rehearsal).
    """
    root = _root_guard(root)
    if mode not in POLICIES:
        raise EvidenceRejected("INVALID_POLICY")
    if os.name != "posix":
        raise EvidenceRejected("NON_POSIX_DIRECTORY_BARRIER_UNVERIFIED")
    if root.exists() and any(root.iterdir()):
        raise EvidenceRejected("LAB_ROOT_NOT_EMPTY")
    root.mkdir(mode=0o700, exist_ok=True)
    os.chmod(root, 0o700)
    db_key, media_key = secrets.token_hex(32), secrets.token_hex(32)
    private = json.dumps({"db_key": db_key, "media_key": media_key},
                         sort_keys=True).encode("utf-8")
    _atomic_private_file(root / PRIVATE, private)
    _sync_dir(root)

    capture = "BENCH-" + secrets.token_hex(8)
    receipt = "RECEIPT-TEST-" + secrets.token_hex(12)
    iv = secrets.token_bytes(12)
    aad = capture.encode("ascii")
    encrypted = b"DCE1" + iv + AESGCM(bytes.fromhex(media_key)).encrypt(
        iv, PAYLOAD, aad,
    )
    _atomic_private_file(root / "encrypted-test-media.bin", encrypted)
    _sync_dir(root)

    db = _open_db(root, db_key, mode)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE metadata (
            capture TEXT PRIMARY KEY, declared_writer_sync TEXT NOT NULL,
            media_digest TEXT NOT NULL, receipt_id TEXT NOT NULL UNIQUE)""")
        db.execute("""CREATE TABLE receipts (
            capture TEXT PRIMARY KEY, receipt_id TEXT NOT NULL UNIQUE,
            media_digest TEXT NOT NULL)""")
        db.execute("CREATE TABLE audit (receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)")
        db.execute("CREATE TABLE outbox (receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)")
        digest = hashlib.sha256(PAYLOAD).hexdigest()
        db.execute("INSERT INTO metadata VALUES(?,?,?,?)", (capture, mode, digest, receipt))
        db.execute("INSERT INTO receipts VALUES(?,?,?)", (capture, receipt, digest))
        db.execute("INSERT INTO audit VALUES(?,?)", (receipt, "BENCH_COMMITTED"))
        db.execute("INSERT INTO outbox VALUES(?,?)", (receipt, "MEDIA_PRESENT"))
        db.commit()

        witness = {
            "schema": "LOT06_C05B03E_PRE_EVENT_V1",
            "capture": capture,
            "receipt": receipt,
            "writer_policy_declared": mode,
            "media_digest": digest,
            "ciphertext_sha256": hashlib.sha256(encrypted).hexdigest(),
            "device_platform_observed": platform.system(),
            "os_release_observed": platform.release(),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "evidence_type": "SYNTHETIC_PRE_EVENT_COMMIT",
            "operator_power_interruption_observed": False,
            "independent_external_witness_verified": False,
            "clinical_receipt_durable_certified": False,
        }
        # A local copy is convenient but is NEVER an independent witness:
        # operator must export the stdout JSON onto separate storage.
        _atomic_private_file(
            root / MANIFEST,
            (json.dumps(witness, sort_keys=True, indent=2) + "\n").encode("utf-8"),
        )
        _sync_dir(root)
        return witness, db
    except BaseException:
        db.rollback()
        db.close()
        raise


def recover(root: Path, external_witness: Path):
    """Cold-restart verification, not an unreviewed clinical/power certification."""
    root = _root_guard(root)
    external_witness = Path(external_witness).absolute()
    if external_witness.is_symlink() or not external_witness.is_file():
        raise EvidenceRejected("EXTERNAL_WITNESS_REQUIRED")
    if external_witness == root or root in external_witness.parents:
        raise EvidenceRejected("EXTERNAL_WITNESS_REQUIRED")
    try:
        witness = json.loads(external_witness.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceRejected("EXTERNAL_WITNESS_INVALID") from exc
    if (not isinstance(witness, dict)
            or witness.get("schema") != "LOT06_C05B03E_PRE_EVENT_V1"
            or witness.get("writer_policy_declared") not in POLICIES
            or witness.get("evidence_type") != "SYNTHETIC_PRE_EVENT_COMMIT"):
        raise EvidenceRejected("EXTERNAL_WITNESS_INVALID")
    required = ("capture", "receipt", "media_digest", "ciphertext_sha256")
    if not all(isinstance(witness.get(field), str) and witness[field] for field in required):
        raise EvidenceRejected("EXTERNAL_WITNESS_INVALID")

    try:
        private = json.loads((root / PRIVATE).read_text(encoding="utf-8"))
        db_key, media_key = private["db_key"], private["media_key"]
        if (len(db_key) != 64 or len(media_key) != 64
                or any(c not in "0123456789abcdef" for c in db_key + media_key)):
            raise ValueError("bad lab key")
    except (ValueError, KeyError, OSError, TypeError) as exc:
        raise EvidenceRejected("BENCH_KEYS_UNAVAILABLE") from exc

    try:
        db = _open_db(root, db_key, witness["writer_policy_declared"])
        try:
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise EvidenceRejected("SQLCIPHER_INTEGRITY_FAILED")
            metadata = db.execute("SELECT capture,declared_writer_sync,media_digest,receipt_id FROM metadata").fetchall()
            receipts = db.execute("SELECT capture,receipt_id,media_digest FROM receipts").fetchall()
            audits = db.execute("SELECT receipt_id,event FROM audit").fetchall()
            outboxes = db.execute("SELECT receipt_id,event FROM outbox").fetchall()
        finally:
            db.close()
    except EvidenceRejected:
        raise
    except Exception as exc:
        raise EvidenceRejected("SQLCIPHER_RECOVERY_FAILED") from exc

    expected = (witness["capture"], witness["writer_policy_declared"],
                witness["media_digest"], witness["receipt"])
    if (metadata != [expected]
            or receipts != [(witness["capture"], witness["receipt"], witness["media_digest"])]
            or audits != [(witness["receipt"], "BENCH_COMMITTED")]
            or outboxes != [(witness["receipt"], "MEDIA_PRESENT")]):
        raise EvidenceRejected("RECEIPT_AUDIT_OUTBOX_NOT_RECOVERED")

    try:
        blob = (root / "encrypted-test-media.bin").read_bytes()
        if (blob[:4] != b"DCE1"
                or hashlib.sha256(blob).hexdigest() != witness["ciphertext_sha256"]):
            raise EvidenceRejected("MEDIA_INTEGRITY_FAILED")
        clear = AESGCM(bytes.fromhex(media_key)).decrypt(
            blob[4:16], blob[16:], witness["capture"].encode("ascii"))
        if hashlib.sha256(clear).hexdigest() != witness["media_digest"] or clear != PAYLOAD:
            raise EvidenceRejected("MEDIA_INTEGRITY_FAILED")
    except (OSError, InvalidTag, ValueError) as exc:
        raise EvidenceRejected("MEDIA_INTEGRITY_FAILED") from exc

    # Even after a real power loss this is ONLY software recovery evidence.
    # Independently witnessed power event, VFS/drive hardware and clinician
    # approvals must be reviewed outside this tool.
    return {
        "status": "RECOVERY_OBSERVED_EVENT_UNVERIFIED",
        "writer_policy_declared": witness["writer_policy_declared"],
        "sqlcipher_integrity": "PASS",
        "receipt_audit_outbox": "PASS",
        "encrypted_media_integrity": "PASS",
        "external_witness_file_checked": True,
        "independent_witness_storage_verified": False,
        "physical_power_loss_verified": False,
        "vfs_xsync_or_drive_flush_verified": False,
        "windows_ntfs_verified": False,
        "clinical_durable_receipt_certified": False,
        "product_ready": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="LAB-only external-event SQLCipher witness; never cuts power")
    parser.add_argument("phase", choices=["prepare", "recover"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--mode", choices=sorted(POLICIES), default="FULL")
    parser.add_argument("--witness", type=Path, help="Independent copied pre-event witness, for recovery")
    parser.add_argument("--hold", action="store_true",
                        help="Keep SQLCipher connection open, operator must arrange external interruption")
    args = parser.parse_args(argv)
    try:
        if args.phase == "prepare":
            manifest, db = prepare(args.root, args.mode)
            try:
                print(json.dumps({
                    "status": "ARMED_TEST_ONLY_NO_PHYSICAL_EVENT",
                    "pre_event_witness": manifest,
                    "instructions": "Copy witness to independent storage before any externally supervised test",
                }, sort_keys=True), flush=True)
                if args.hold:
                    print("LAB_HOLD_ACTIVE: awaiting EXTERNAL operator-controlled action, NOT invoking shutdown", flush=True)
                    while True:
                        time.sleep(2)
            finally:
                db.close()
        else:
            if args.witness is None:
                raise EvidenceRejected("EXTERNAL_WITNESS_REQUIRED")
            result = recover(args.root, args.witness)
            print(json.dumps(result, sort_keys=True))
        return 0
    except EvidenceRejected as exc:
        print(json.dumps({"status": "NO_GO", "reason": exc.code,
                          "clinical_durable_receipt_certified": False,
                          "product_ready": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
