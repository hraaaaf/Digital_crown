"""LOT06-B file-backed SQLCipher / real AES-GCM Media Core process-restart probe.

TEST-ONLY: this DOES NOT enable the guarded LAB HTTP transfer on disk,
and manually inserts an isolated synthetic receipt for integrity testing.
No actual clinical patient, enrolment, SQLCipher migration, or production setup.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import os
from pathlib import Path
import sqlite3
import sys

from PIL import Image
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool


TENANT = 901
PATIENT = 902
DEVICE = "lab-sqlcipher-test-device"
CAPTURE = "lab-sqlcipher-test-capture"
RECEIPT = "LAB-SQLCIPHER-RESTART-SYNTHETIC"


def require_test(tmp: Path) -> tuple[Path, Path]:
    if (os.environ.get("ENVIRONMENT") != "test" or
            os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true" or
            not os.environ.get("DC06B_SQLCIPHER_PROOF_KEY") or
            not os.environ.get("CABINET_MASTER_KEY_HEX")):
        raise RuntimeError("ISOLATED_SQLCIPHER_PROOF_DISABLED")
    tmp = tmp.resolve()
    if "pytest-" not in str(tmp) and "lot06b-durable-" not in str(tmp):
        raise RuntimeError("UNSAFE_SQLCIPHER_TEST_PATH")
    return tmp / "lab-media.db", tmp / "media"


def connect_db(path: Path, *, wrong_key: bool = False):
    from sqlcipher3 import dbapi2 as sqlcipher
    secret = os.environ["DC06B_SQLCIPHER_PROOF_KEY"]
    if wrong_key:
        secret = "wrong" + secret
    if len(secret) < 32 or not secret.isascii() or not secret.isalnum():
        raise RuntimeError("INVALID_TEST_SECRET")
    conn = sqlcipher.connect(str(path))
    conn.execute("PRAGMA key = '" + secret + "'")
    version = conn.execute("PRAGMA cipher_version").fetchone()
    if not version or not version[0]:
        conn.close()
        raise RuntimeError("SQLCIPHER_NOT_ACTIVE")
    conn.execute("PRAGMA foreign_keys=OFF")  # synthetic asset IDs, no real patients
    return conn


def engine_for(path: Path):
    # SQLAlchemy invokes the actual sqlcipher3 DBAPI for EVERY connection.
    engine = create_engine(
        "sqlite://",
        creator=lambda: connect_db(path),
        poolclass=NullPool,
        future=True,
    )
    return engine


def synthetic_png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (8, 8), (21, 47, 96)).save(output, format="PNG")
    return output.getvalue()


def write(path: Path, root: Path):
    from backend.models_media_core import ClinicalAsset
    from backend.services.clinical_asset_storage import store_clinical_asset_bytes
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab

    if path.exists():
        raise RuntimeError("SQLCIPHER_PROOF_ALREADY_EXISTS")
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = engine_for(path)
    try:
        # Explicit minimal TEST ledger schema. No production migrations.
        ClinicalAsset.__table__.create(bind=engine)
        lab.metadata.create_all(bind=engine)
        with Session(engine, expire_on_commit=False) as db:
            asset = ClinicalAsset(
                id=1001, employer_id=TENANT, patient_id=PATIENT,
                asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
                provenance_json={"ingestion_channel": "SYNTHETIC_RESTART_TEST"},
            )
            db.add(asset)
            db.flush()
            png = synthetic_png()
            saved = store_clinical_asset_bytes(
                db, employer_id=TENANT, patient_id=PATIENT,
                asset_id=asset.id, content=png, media_root=root,
            )
            assert not saved.deduplicated
            assert saved.asset.sha256 == hashlib.sha256(png).hexdigest()
            rid = RECEIPT
            db.execute(insert(lab.receipts).values(
                tenant=TENANT, device=DEVICE, capture=CAPTURE,
                receipt_id=rid, asset_id=asset.id,
                patient=PATIENT, digest=asset.sha256,
            ))
            db.execute(insert(lab.audit).values(
                receipt_id=rid, event="LAB_ACQUISITION_COMMITTED",
                patient_only_reason="LAB_UNSCHEDULED",
            ))
            db.execute(insert(lab.outbox).values(
                receipt_id=rid, event="LAB_MEDIA_READY",
            ))
            db.commit()
    finally:
        engine.dispose()
    if path.read_bytes().startswith(b"SQLite format 3"):
        raise AssertionError("PLAIN_SQLITE_DB_FORBIDDEN")
    if not list(root.rglob("*.dcm")):
        raise AssertionError("ENCRYPTED_BLOB_MISSING")
    print("SQLCIPHER_MEDIA_COMMITTED_BEFORE_PROCESS_EXIT")


def verify(path: Path, root: Path, *, expect_tampered: bool = False):
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab
    from backend.services.clinical_asset_storage import (
        ClinicalAssetStorageError, read_clinical_asset_bytes,
    )

    if not path.exists():
        raise AssertionError("DURABLE_DB_MISSING_AFTER_RESTART")
    if path.read_bytes().startswith(b"SQLite format 3"):
        raise AssertionError("SQLCIPHER_DB_IS_PLAINTEXT")
    # Plain sqlite3 cannot read the encrypted database.
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as plain:
        try:
            plain.execute("SELECT name FROM sqlite_master").fetchone()
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("PLAIN_SQLITE_READ_BYPASS")

    engine = engine_for(path)
    try:
        with Session(engine) as db:
            assert db.execute(select(lab.receipts)).rowcount != 999  # fetch below
            assert len(db.execute(select(lab.receipts)).all()) == 1
            assert len(db.execute(select(lab.audit)).all()) == 1
            assert len(db.execute(select(lab.outbox)).all()) == 1
            if expect_tampered:
                try:
                    lab._receipt(db, tenant=TENANT, device=DEVICE, capture=CAPTURE)
                except lab.TransferLabRejected as exc:
                    if exc.reason != "RECEIPT_INTEGRITY_BLOCKED":
                        raise
                else:
                    raise AssertionError("TAMPERED_CIPHERTEXT_WAS_ACCEPTED")
                print("SQLCIPHER_MEDIA_TAMPER_REJECTED_AFTER_NEW_PROCESS")
                return
            receipt = lab._receipt(
                db, tenant=TENANT, device=DEVICE, capture=CAPTURE
            )
            assert receipt and receipt["status"] == "LAB_SERVER_RECEIPT"
            assert receipt["asset_id"] == 1001
            assert receipt["patient_id"] == PATIENT
            assert receipt["server_confirmed"] is False
            assert receipt["sha256"] == hashlib.sha256(synthetic_png()).hexdigest()
            payload = read_clinical_asset_bytes(
                db, employer_id=TENANT, patient_id=PATIENT,
                asset_id=1001, media_root=root,
            )
            assert payload == synthetic_png()
            for tenant, patient in ((TENANT + 1, PATIENT), (TENANT, PATIENT + 1)):
                try:
                    read_clinical_asset_bytes(
                        db, employer_id=tenant, patient_id=patient,
                        asset_id=1001, media_root=root,
                    )
                except ClinicalAssetStorageError:
                    pass
                else:
                    raise AssertionError("CROSS_SCOPE_MEDIA_LEAK")
            assert db.execute(select(lab.audit.c.patient_only_reason)).scalar_one() == "LAB_UNSCHEDULED"
            print("SQLCIPHER_MEDIA_PROCESS_RESTART_RECEIPT_VERIFIED")
    finally:
        engine.dispose()


def corrupt(path: Path, root: Path):
    files = list(root.rglob("*.dcm"))
    if len(files) != 1:
        raise RuntimeError("EXPECTED_ONE_SYNTHETIC_ENCRYPTED_BLOB")
    original = files[0].read_bytes()
    if not original.startswith(b"DCM1"):
        raise RuntimeError("AESGCM_ENVELOPE_MISSING")
    altered = bytearray(original)
    altered[-1] ^= 0x01
    files[0].write_bytes(altered)
    print("SQLCIPHER_MEDIA_SYNTHETIC_CIPHERTEXT_CORRUPTED")


def reject_wrong_key(path: Path):
    try:
        with connect_db(path, wrong_key=True) as conn:
            conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
    except Exception:
        print("SQLCIPHER_WRONG_DB_KEY_REJECTED")
    else:
        raise AssertionError("SQLCIPHER_WRONG_KEY_ACCEPTED")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: <write|verify|wrong-key|corrupt|verify-tamper> <tmp>")
    mode, directory = sys.argv[1:]
    path, root = require_test(Path(directory))
    if mode == "write":
        write(path, root)
    elif mode == "verify":
        verify(path, root)
    elif mode == "wrong-key":
        reject_wrong_key(path)
    elif mode == "corrupt":
        corrupt(path, root)
    elif mode == "verify-tamper":
        verify(path, root, expect_tampered=True)
    else:
        raise RuntimeError("INVALID_TEST_STAGE")


if __name__ == "__main__":
    main()
