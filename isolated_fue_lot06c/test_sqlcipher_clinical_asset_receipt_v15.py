"""LOT06-C05B-03B: true ClinicalAsset ORM + AES-GCM + SQLCipher SQL commit FUE.

Independent synthetic rehearsal on *one encrypted on-prem file*. No clinical
migration, real device/staff authentication, LAB persistent transfer, or API.
A crash/rollback may leave an encrypted orphan; it must never leave a receipt.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

from PIL import Image
from io import BytesIO
import pytest
from sqlalchemy.orm import Session

from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_storage import (
    store_clinical_asset_bytes, read_clinical_asset_bytes,
)
from backend.services.imaging_clinical_asset_verifier_v15 import (
    verify_device_capture_media_binding, MediaBindingRejected,
)
from tools.imaging_gateway.qa_durable_receipt_restart_lab import _core_engine

TENANT, PATIENT, STAFF = 31, 73, 81
DEVICE, REASON = "synthetic-sqlcipher-device", "LAB_UNSCHEDULED"
SCHEMA = (
    """CREATE TABLE c05b03b_approved (
        tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
        digest TEXT NOT NULL, byte_size INTEGER NOT NULL, patient INTEGER NOT NULL,
        staff INTEGER NOT NULL, version INTEGER NOT NULL, asset_id INTEGER NOT NULL,
        reason TEXT NOT NULL, approved INTEGER NOT NULL,
        PRIMARY KEY (tenant,device,capture))""",
    """CREATE TABLE c05b03b_receipts (
        tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
        receipt_id TEXT NOT NULL UNIQUE, digest TEXT NOT NULL,
        byte_size INTEGER NOT NULL, patient INTEGER NOT NULL,
        staff INTEGER NOT NULL, version INTEGER NOT NULL, asset_id INTEGER NOT NULL UNIQUE,
        reason TEXT NOT NULL, PRIMARY KEY (tenant,device,capture))""",
    """CREATE TABLE c05b03b_audit (
        receipt_id TEXT PRIMARY KEY NOT NULL, event TEXT NOT NULL)""",
    """CREATE TABLE c05b03b_outbox (
        receipt_id TEXT PRIMARY KEY NOT NULL, event TEXT NOT NULL)""",
)


def _guard():
    if not (
        os.environ.get("ENVIRONMENT") == "test"
        and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
        and os.environ.get("DC06C05B03B_TEST_ONLY") == "1"
    ):
        raise RuntimeError("C05B03B_ISOLATED_ONLY")


def _png() -> bytes:
    output = BytesIO()
    Image.new("RGB", (8, 8), (32, 96, 156)).save(output, format="PNG")
    return output.getvalue()


def _root_engine(root: Path):
    _guard()
    return _core_engine(root)


def _claim(capture: str, asset_id: int) -> tuple:
    data = _png()
    return (
        TENANT, DEVICE, capture, hashlib.sha256(data).hexdigest(),
        len(data), PATIENT, STAFF, 2, asset_id, REASON,
    )


def _initialize(root: Path, claims: tuple[tuple, ...]):
    engine = _root_engine(root)
    try:
        ClinicalAsset.__table__.create(bind=engine)
        with engine.begin() as conn:
            for ddl in SCHEMA:
                conn.exec_driver_sql(ddl)
            for claim in claims:
                conn.exec_driver_sql(
                    "INSERT INTO c05b03b_approved VALUES(?,?,?,?,?,?,?,?,?,?,1)", claim
                )
    finally:
        engine.dispose()


def _counts(root: Path):
    engine = _root_engine(root)
    try:
        with engine.connect() as c:
            return tuple(c.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
                         for table in ("clinical_assets", "c05b03b_receipts",
                                       "c05b03b_audit", "c05b03b_outbox"))
    finally:
        engine.dispose()


def _receipt_and_proof(db, claim: tuple, media_root: Path):
    row = db.connection().exec_driver_sql(
        "SELECT tenant,device,capture,receipt_id,digest,byte_size,patient,"
        "staff,version,asset_id,reason FROM c05b03b_receipts "
        "WHERE tenant=? AND device=? AND capture=?", claim[:3],
    ).fetchone()
    if row is None:
        return None
    if (*row[:3], *row[4:]) != claim:
        raise ValueError("SQLCIPHER_RECEIPT_IDENTITY_CONFLICT")
    rid = row[3]
    for table, event in (
        ("c05b03b_audit", "CAPTURE_COMMITTED"),
        ("c05b03b_outbox", "MEDIA_READY"),
    ):
        if db.connection().exec_driver_sql(
            f"SELECT event FROM {table} WHERE receipt_id=?", (rid,),
        ).scalar_one_or_none() != event:
            raise ValueError("RECEIPT_AUDIT_OUTBOX_INCOMPLETE")
    proof = verify_device_capture_media_binding(
        db, tenant=claim[0], patient=claim[5], asset_id=claim[8],
        staff_id=claim[6], digest=claim[3], byte_size=claim[4],
        media_root=media_root,
    )
    assert proof.clinical_receipt_authorized is False
    return rid


def _issue(root: Path, claim: tuple, *, fail_at: str | None = None):
    _guard()
    if fail_at not in (None, "after_media", "after_receipt", "after_audit", "after_outbox"):
        raise ValueError("INVALID_FUE_FAILPOINT")
    engine = _root_engine(root)
    media_root = root / "media"
    try:
        with Session(engine, expire_on_commit=False) as db:
            # Explicit database writer lock, not ignored SQLite FOR UPDATE.
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            approved = db.connection().exec_driver_sql(
                "SELECT tenant,device,capture,digest,byte_size,patient,staff,"
                "version,asset_id,reason,approved FROM c05b03b_approved "
                "WHERE tenant=? AND device=? AND capture=?", claim[:3],
            ).fetchone()
            if approved != (*claim, 1):
                raise ValueError("SQLCIPHER_APPROVAL_VERSION_BINDING_CONFLICT")
            old = _receipt_and_proof(db, claim, media_root)
            if old is not None:
                db.commit()
                return old

            asset = ClinicalAsset(
                id=claim[8], employer_id=claim[0], patient_id=claim[5],
                asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
                created_by=claim[6],
                provenance_json={
                    "ingestion_channel": "LOT06_C05B03B_SYNTHETIC_ONLY",
                    "capture_id": claim[2], "device": claim[1],
                },
            )
            db.add(asset)
            db.flush()
            written = store_clinical_asset_bytes(
                db, employer_id=claim[0], patient_id=claim[5],
                asset_id=claim[8], content=_png(), media_root=media_root,
            )
            assert written.asset.sha256 == claim[3]
            assert written.asset.byte_size == claim[4]
            assert read_clinical_asset_bytes(
                db, employer_id=claim[0], patient_id=claim[5],
                asset_id=claim[8], media_root=media_root,
            ) == _png()
            if fail_at == "after_media":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            rid = "SC-ASSET-TEST-" + secrets.token_hex(16)
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03b_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (*claim[:3], rid, *claim[3:]),
            )
            if fail_at == "after_receipt":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03b_audit VALUES(?,?)", (rid, "CAPTURE_COMMITTED"),
            )
            if fail_at == "after_audit":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03b_outbox VALUES(?,?)", (rid, "MEDIA_READY"),
            )
            if fail_at == "after_outbox":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            db.commit()  # one SQLCipher commit includes actual ClinicalAsset and receipt/audit/outbox
            return rid
    finally:
        engine.dispose()


def test_c05b03b_actual_asset_sqlcipher_atomic_and_lost_ack(tmp_path, monkeypatch):
    _guard()
    root = tmp_path / "sqlcipher-actual-asset"
    root.mkdir()
    monkeypatch.setenv("DC06B_TEST_SQLCIPHER_KEY", secrets.token_hex(32))
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", secrets.token_hex(32))
    first, ack = _claim("capture-asset-atomic", 1001), _claim("capture-ack-lost", 1002)
    _initialize(root, (first, ack))
    assert _counts(root) == (0, 0, 0, 0)

    for boundary in ("after_media", "after_receipt", "after_audit", "after_outbox"):
        with pytest.raises(RuntimeError, match="INJECTED_SQL_ROLLBACK"):
            _issue(root, first, fail_at=boundary)
        assert _counts(root) == (0, 0, 0, 0)
    blobs = list((root / "media").rglob("*.dcm"))
    assert len(blobs) == 1 and blobs[0].read_bytes().startswith(b"DCM1")
    assert _issue(root, first).startswith("SC-ASSET-TEST-")
    assert _counts(root) == (1, 1, 1, 1)
    assert len(list((root / "media").rglob("*.dcm"))) == 1

    for wrong in (
        (*first[:3], "0" * 64, *first[4:]),
        (*first[:7], 3, *first[8:]),
        (*first[:5], PATIENT + 1, *first[6:]),
    ):
        with pytest.raises(ValueError, match="SQLCIPHER_APPROVAL_VERSION_BINDING_CONFLICT"):
            _issue(root, wrong)
    assert _counts(root) == (1, 1, 1, 1)

    # Another OS process commits actual ClinicalAsset and SQL triplet, exits
    # without returning ACK. Parent must recover from disk with full AES check.
    env = dict(os.environ, DC06C05B03B_ROOT=str(root))
    child = subprocess.run(
        [sys.executable, "-m", "isolated_fue_lot06c.test_sqlcipher_clinical_asset_receipt_v15", "--commit-exit"],
        env=env, capture_output=True, text=True, timeout=60, check=False,
    )
    assert child.returncode == 75, f"POSTCOMMIT_CHILD_EXIT_{child.returncode}"
    assert _counts(root) == (2, 2, 2, 2)
    recovered = _issue(root, ack)
    assert recovered.startswith("SC-ASSET-TEST-")
    assert all(_issue(root, ack) == recovered for _ in range(3))
    assert (root / "clinical-asset-lab.db").read_bytes()[:16] != b"SQLite format 3\x00"

    raw = blobs[0].read_bytes()
    blobs[0].write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    with pytest.raises(MediaBindingRejected, match="MEDIA_INTEGRITY_BLOCKED"):
        _issue(root, first)
    assert _counts(root) == (2, 2, 2, 2)  # blocked replay, no extra SQL state
    with pytest.raises(ValueError, match="SQLCIPHER_APPROVAL_VERSION_BINDING_CONFLICT"):
        # An unknown capture is denied before any media read or SQL receipt.
        _issue(root, _claim("not-approved-capture", 1003))

    evidence = Path(os.environ.get("DC06C05B03B_EVIDENCE_DIR", str(tmp_path)))
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "lot06c05b03b-real-asset-sqlcipher-fue.json").write_text(
        json.dumps({
            "kind": "LOT06_C05B03B_ACTUAL_CLINICAL_ASSET_SQLCIPHER_TEST",
            "actual_clinical_asset_orm_in_encrypted_file": True,
            "real_aesgcm_written_verified_before_sql_commit": True,
            "asset_receipt_audit_outbox_same_sql_commit": True,
            "four_injected_failpoints_leave_no_sql_receipt": True,
            "encrypted_orphan_retained_and_rechecked": True,
            "postcommit_os_exit_recovered_with_real_media": True,
            "tampered_ciphertext_blocks_receipt_replay": True,
            "real_device_staff_authentication": False,
            "real_approval_schema_migration": False,
            "sql_and_filesystem_globally_atomic": False,
            "production_clinical_transfer_enabled": False,
            "product_ready": False,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8",
    )
    print("LOT06C05B03B_SQLCIPHER_ACTUAL_ASSET_RECEIPT_ATOMIC_FUE_PASS")


if __name__ == "__main__" and sys.argv[1:] == ["--commit-exit"]:
    _guard()
    _issue(Path(os.environ["DC06C05B03B_ROOT"]), _claim("capture-ack-lost", 1002))
    os._exit(75)
