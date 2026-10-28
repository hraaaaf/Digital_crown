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


def _core_engine(root: Path):
    """Actual ClinicalAsset model on an independent TEST-only SQLCipher file."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool

    def connect():
        from sqlcipher3 import dbapi2 as sqlcipher
        key = _require_key("DC06B_TEST_SQLCIPHER_KEY")
        con = sqlcipher.connect(str(root / "clinical-asset-lab.db"))
        try:
            con.execute(f"PRAGMA key = '{key}'")
            if not con.execute("PRAGMA cipher_version").fetchone():
                raise RuntimeError("SQLCIPHER_CIPHER_VERSION_UNAVAILABLE")
            con.execute("PRAGMA foreign_keys=OFF")  # synthetic user IDs only
            con.execute("PRAGMA journal_mode=DELETE")
            con.execute("PRAGMA synchronous=FULL")
            con.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
        except Exception:
            con.close()
            raise
        return con

    return create_engine("sqlite://", creator=connect, poolclass=NullPool, future=True)


def _core_phase(root: Path, phase: str):
    """Reopen the real ClinicalAsset + LAB tables, NEVER use lab.transfer."""
    if (os.environ.get("ENVIRONMENT") != "test"
            or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true"):
        raise RuntimeError("ISOLATED_MEDIA_CORE_RESTART_DISABLED")
    from sqlalchemy import insert, select
    from sqlalchemy.orm import Session
    from backend.models_media_core import ClinicalAsset
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab
    from backend.services.clinical_asset_storage import (
        ClinicalAssetStorageError, read_clinical_asset_bytes,
        store_clinical_asset_bytes,
    )

    media_root = root / "clinical-media"
    os.environ["MEDIA_ROOT"] = str(media_root)
    png = _png((21, 47, 96))
    digest = hashlib.sha256(png).hexdigest()
    core_device, core_capture = "synthetic-core-device", "synthetic-core-capture"
    core_receipt = "SYNTHETIC-ACTUAL-MODEL"
    if phase == "core-tamper":
        blobs = list(media_root.rglob("*.dcm"))
        assert len(blobs) == 1, "CLINICAL_MEDIA_COUNT_MISMATCH"
        raw = bytearray(blobs[0].read_bytes())
        assert raw.startswith(b"DCM1"), "CLINICAL_MEDIA_ENVELOPE_MISSING"
        raw[-1] ^= 1
        blobs[0].write_bytes(raw)
        print("CLINICAL_ASSET_CIPHERTEXT_TAMPERED")
        return 0

    engine = _core_engine(root)
    try:
        if phase == "core-write":
            ClinicalAsset.__table__.create(bind=engine)
            lab.metadata.create_all(bind=engine)
        with Session(engine, expire_on_commit=False) as db:
            if phase == "core-write":
                asset = ClinicalAsset(
                    id=1001, employer_id=TENANT, patient_id=PATIENT,
                    asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
                    provenance_json={"ingestion_channel": "SYNTHETIC_DR04_CONVERGENCE"},
                )
                db.add(asset)
                db.flush()
                saved = store_clinical_asset_bytes(
                    db, employer_id=TENANT, patient_id=PATIENT,
                    asset_id=asset.id, content=png, media_root=media_root,
                )
                assert not saved.deduplicated
                assert saved.asset.sha256 == digest
                db.execute(insert(lab.receipts).values(
                    tenant=TENANT, device=core_device, capture=core_capture,
                    receipt_id=core_receipt, asset_id=asset.id,
                    patient=PATIENT, digest=digest,
                ))
                db.execute(insert(lab.audit).values(
                    receipt_id=core_receipt, event="LAB_ACQUISITION_COMMITTED",
                    patient_only_reason=REASON,
                ))
                db.execute(insert(lab.outbox).values(
                    receipt_id=core_receipt, event="LAB_MEDIA_READY",
                ))
                db.commit()
                assert (root / "clinical-asset-lab.db").read_bytes()[:16] != b"SQLite format 3\x00"
                print("ACTUAL_CLINICAL_ASSET_MODEL_SQLCIPHER_COMMITTED")
                return 0

            # This proof must NEVER relax the real production LAB guard.
            os.environ["DC_V15_06_TRANSFER_LAB"] = "1"
            try:
                lab.guard(db)
            except lab.TransferLabRejected as exc:
                assert exc.reason == "ISOLATED_TRANSFER_DISABLED"
            else:
                raise AssertionError("PERSISTENT_LAB_GUARD_BYPASSED")
            assert len(db.execute(select(lab.receipts)).all()) == 1
            assert len(db.execute(select(lab.audit)).all()) == 1
            assert len(db.execute(select(lab.outbox)).all()) == 1

            if phase == "core-verify-tampered":
                try:
                    lab._receipt(db, tenant=TENANT,
                                 device=core_device, capture=core_capture)
                except lab.TransferLabRejected as exc:
                    assert exc.reason == "RECEIPT_INTEGRITY_BLOCKED"
                else:
                    raise AssertionError("TAMPERED_ACTUAL_MODEL_ACCEPTED")
                print("ACTUAL_CLINICAL_ASSET_RECEIPT_TAMPER_REJECTED")
                return 0

            assert phase == "core-verify"
            receipt = lab._receipt(
                db, tenant=TENANT, device=core_device, capture=core_capture
            )
            assert receipt and receipt["status"] == "LAB_SERVER_RECEIPT"
            assert receipt["asset_id"] == 1001 and receipt["patient_id"] == PATIENT
            assert receipt["sha256"] == digest and receipt["server_confirmed"] is False
            assert read_clinical_asset_bytes(
                db, employer_id=TENANT, patient_id=PATIENT,
                asset_id=1001, media_root=media_root,
            ) == png
            for tenant, patient in ((TENANT + 1, PATIENT), (TENANT, PATIENT + 1)):
                try:
                    read_clinical_asset_bytes(
                        db, employer_id=tenant, patient_id=patient,
                        asset_id=1001, media_root=media_root,
                    )
                except ClinicalAssetStorageError:
                    pass
                else:
                    raise AssertionError("CROSS_SCOPE_CLINICAL_MEDIA_LEAK")
            assert db.execute(select(lab.audit.c.patient_only_reason)).scalar_one() == REASON
            print("ACTUAL_CLINICAL_ASSET_MODEL_VERIFIED_AFTER_PROCESS_RESTART")
            return 0
    finally:
        engine.dispose()


def _run(root: Path, phase: str):
    os.environ["CABINET_MASTER_KEY_HEX"] = _require_key("DC06B_TEST_MEDIA_KEY")
    if phase.startswith("core-"):
        return _core_phase(root, phase)
    if phase == "wrong-key":
        # A missing SQLCipher module must NOT be counted as a bad-key success.
        from sqlcipher3 import dbapi2 as sqlcipher
        try:
            with _open(root, incorrect=True) as con:
                con.execute("SELECT COUNT(*) FROM synthetic_receipts").fetchone()
        except sqlcipher.DatabaseError:
            print("WRONG_SQLCIPHER_KEY_BLOCKED")
            return 0
        raise AssertionError("WRONG_KEY_WAS_ACCEPTED")
    if phase == "wrong-media-key":
        # Use the original disk path, never a newly-derived path under the
        # wrong key: this must prove AES-GCM tag rejection, not missing file.
        from backend.services.clinical_asset_storage import (
            ClinicalAssetIntegrityError, _read_verified_path,
        )
        payload = _png((15, 45, 75))
        files = list((root / "media").rglob("*.dcm"))
        assert len(files) == 3, "SYNTHETIC_MEDIA_COUNT_MISMATCH"
        # Among these three ciphertexts is the original committed blob; all
        # must fail authentication with the distinct test media key.
        for file in files:
            assert file.read_bytes().startswith(b"DCM1"), "MEDIA_ENVELOPE_MISSING"
            try:
                _read_verified_path(
                    file, employer_id=TENANT,
                    digest=hashlib.sha256(payload).hexdigest(), byte_size=len(payload),
                )
            except ClinicalAssetIntegrityError:
                continue
            raise AssertionError("WRONG_MEDIA_AESGCM_KEY_ACCEPTED")
        print("WRONG_MEDIA_AESGCM_KEY_BLOCKED")
        return 0
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
        elif phase == "interrupt-pre-sql":
            # Crash after encrypted file fsync but BEFORE ANY SQL transaction.
            _store(root, _png((105, 65, 25)))
            os._exit(74)
        elif phase == "verify-pre-sql":
            _assert_integrity(root, con)
            assert con.execute(
                "SELECT COUNT(*) FROM synthetic_receipts WHERE capture='pending-before-sql'"
            ).fetchone()[0] == 0
            assert _blob(root, _png((105, 65, 25))).is_file()
            print("PRE_SQL_PROCESS_CRASH_NO_AUTHORITATIVE_RECEIPT")
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
            con.execute(
                "INSERT INTO synthetic_outbox VALUES(?,?)",
                ("SYNTH-INTERRUPTED", "LAB_MEDIA_READY"),
            )
            # Abrupt OS process exit with ALL 3 SQL inserts, before SQL COMMIT. This is NOT a power cut.
            os._exit(73)
        elif phase == "verify-interrupted":
            _assert_integrity(root, con)
            assert con.execute(
                "SELECT COUNT(*) FROM synthetic_receipts WHERE capture='pending-interrupted'"
            ).fetchone()[0] == 0
            assert con.execute(
                "SELECT COUNT(*) FROM synthetic_audit WHERE receipt_id='SYNTH-INTERRUPTED'"
            ).fetchone()[0] == 0
            assert con.execute(
                "SELECT COUNT(*) FROM synthetic_outbox WHERE receipt_id='SYNTH-INTERRUPTED'"
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
        "write", "verify", "replay", "interrupt-pre-sql", "verify-pre-sql",
        "interrupt", "verify-interrupted", "wrong-key", "wrong-media-key", "tamper",
        "verify-tampered", "core-write", "core-verify", "core-tamper",
        "core-verify-tampered",
    ], required=True)
    opts = parser.parse_args()
    opts.root.mkdir(parents=True, exist_ok=True)
    try:
        sys.exit(_run(opts.root, opts.phase))
    except Exception as exc:
        # Never log synthetic keys, plaintext content, or patient-specific data.
        print("DURABILITY_REHEARSAL_FAIL", type(exc).__name__, file=sys.stderr)
        sys.exit(2)
