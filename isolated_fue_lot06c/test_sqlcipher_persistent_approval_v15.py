"""LOT06-C05B-03C — persisted approval authority rehearsal, test-only.

Synthetic principals/workstations/devices/approvals live in a file-backed SQLCipher
database. It is NOT production authentication, an Alembic migration, a clinical
receipt issuer, hardware power-loss evidence, or a cross-FS/SQL transaction.
"""
import hashlib
import json
import os
from dataclasses import dataclass, replace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import secrets
import subprocess
import sys

import pytest
from sqlalchemy import event
from sqlcipher3.dbapi2 import IntegrityError, OperationalError  # creator=SQLCipher DBAPI
from sqlalchemy.orm import Session

from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_storage import (
    read_clinical_asset_bytes, store_clinical_asset_bytes,
)
from backend.services.imaging_clinical_asset_verifier_v15 import (
    MediaBindingRejected, verify_device_capture_media_binding,
)
from isolated_fue_lot06c.test_sqlcipher_clinical_asset_receipt_v15 import (
    _guard as prior_guard, _png, _root_engine,
)

SCHEMA = (
    "CREATE TABLE users (id INTEGER PRIMARY KEY)",
    "CREATE TABLE patients (id INTEGER PRIMARY KEY)",
    """CREATE TABLE c05b03c_staff (
        tenant INTEGER NOT NULL, staff INTEGER NOT NULL, active INTEGER NOT NULL
        CHECK(active IN (0,1)), authorized INTEGER NOT NULL CHECK(authorized IN (0,1)),
        PRIMARY KEY(tenant,staff))""",
    """CREATE TABLE c05b03c_workstations (
        tenant INTEGER NOT NULL, station TEXT NOT NULL, active INTEGER NOT NULL
        CHECK(active IN (0,1)), PRIMARY KEY(tenant,station))""",
    """CREATE TABLE c05b03c_devices (
        tenant INTEGER NOT NULL, device TEXT NOT NULL, station TEXT NOT NULL,
        active INTEGER NOT NULL CHECK(active IN (0,1)), generation INTEGER NOT NULL,
        PRIMARY KEY(tenant,device),
        FOREIGN KEY(tenant,station) REFERENCES c05b03c_workstations(tenant,station))""",
    """CREATE TABLE c05b03c_approvals (
        tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
        patient INTEGER NOT NULL, staff INTEGER NOT NULL, station TEXT NOT NULL,
        appointment INTEGER, reason TEXT NOT NULL, digest TEXT NOT NULL,
        byte_size INTEGER NOT NULL, asset_id INTEGER NOT NULL,
        version INTEGER NOT NULL CHECK(version > 0),
        approved INTEGER NOT NULL CHECK(approved IN (0,1)),
        PRIMARY KEY(tenant,device,capture),
        FOREIGN KEY(tenant,device) REFERENCES c05b03c_devices(tenant,device),
        FOREIGN KEY(tenant,staff) REFERENCES c05b03c_staff(tenant,staff))""",
    """CREATE TABLE c05b03c_receipts (
        tenant INTEGER NOT NULL, device TEXT NOT NULL, capture TEXT NOT NULL,
        receipt_id TEXT NOT NULL UNIQUE, patient INTEGER NOT NULL,
        staff INTEGER NOT NULL, station TEXT NOT NULL, appointment INTEGER,
        reason TEXT NOT NULL, digest TEXT NOT NULL, byte_size INTEGER NOT NULL,
        asset_id INTEGER NOT NULL UNIQUE, version INTEGER NOT NULL,
        PRIMARY KEY(tenant,device,capture),
        FOREIGN KEY(tenant,device,capture)
          REFERENCES c05b03c_approvals(tenant,device,capture))""",
    "CREATE TABLE c05b03c_audit (receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)",
    "CREATE TABLE c05b03c_outbox (receipt_id TEXT PRIMARY KEY, event TEXT NOT NULL)",
    """CREATE TRIGGER c05b03c_receipt_no_update BEFORE UPDATE ON c05b03c_receipts
       BEGIN SELECT RAISE(ABORT,'RECEIPT_IMMUTABLE'); END""",
    """CREATE TRIGGER c05b03c_receipt_no_delete BEFORE DELETE ON c05b03c_receipts
       BEGIN SELECT RAISE(ABORT,'RECEIPT_IMMUTABLE'); END""",
    """CREATE TRIGGER c05b03c_approval_frozen AFTER UPDATE ON c05b03c_approvals
       WHEN EXISTS (SELECT 1 FROM c05b03c_receipts r
          WHERE r.tenant=OLD.tenant AND r.device=OLD.device AND r.capture=OLD.capture)
         AND (NEW.patient != OLD.patient OR NEW.staff != OLD.staff
           OR NEW.station != OLD.station OR NEW.digest != OLD.digest
           OR NEW.byte_size != OLD.byte_size OR NEW.asset_id != OLD.asset_id
           OR NEW.version != OLD.version OR NEW.reason != OLD.reason
           OR NEW.appointment IS NOT OLD.appointment)
       BEGIN SELECT RAISE(ABORT,'APPROVAL_BINDING_FROZEN'); END""",
    """CREATE TRIGGER c05b03c_approval_no_delete BEFORE DELETE ON c05b03c_approvals
       WHEN EXISTS (SELECT 1 FROM c05b03c_receipts r
          WHERE r.tenant=OLD.tenant AND r.device=OLD.device AND r.capture=OLD.capture)
       BEGIN SELECT RAISE(ABORT,'APPROVAL_REFERENCED'); END""",
)


@dataclass(frozen=True)
class Capture:
    tenant: int
    device: str
    capture: str
    patient: int
    staff: int
    station: str
    appointment: int | None
    reason: str
    digest: str
    byte_size: int
    asset_id: int
    version: int

    def binding(self):
        return (self.tenant, self.device, self.capture, self.patient, self.staff,
                self.station, self.appointment, self.reason, self.digest,
                self.byte_size, self.asset_id, self.version)


def _guard():
    prior_guard()
    if os.environ.get("DC06C05B03C_TEST_ONLY") != "1":
        raise RuntimeError("C05B03C_ISOLATED_ONLY")


def _capture(name, asset):
    data = _png()
    return Capture(31, "lab-device", name, 73, 81, "lab-station", None,
                   "LAB_UNSCHEDULED", hashlib.sha256(data).hexdigest(),
                   len(data), asset, 2)


def _engine(root):
    _guard()
    engine = _root_engine(root)
    @event.listens_for(engine, "connect")
    def _foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    return engine


def _setup(root, claims):
    engine = _engine(root)
    try:
        with engine.begin() as c:
            for ddl in SCHEMA:
                c.exec_driver_sql(ddl)
            assert c.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            for uid in (31, 81):
                c.exec_driver_sql("INSERT INTO users(id) VALUES(?)", (uid,))
            c.exec_driver_sql("INSERT INTO patients(id) VALUES(73)")
            c.exec_driver_sql("INSERT INTO c05b03c_staff VALUES(31,81,1,1)")
            c.exec_driver_sql("INSERT INTO c05b03c_workstations VALUES(31,'lab-station',1)")
            c.exec_driver_sql("INSERT INTO c05b03c_devices VALUES(31,'lab-device','lab-station',1,1)")
            for claim in claims:
                c.exec_driver_sql(
                    "INSERT INTO c05b03c_approvals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1)",
                    claim.binding(),
                )
        ClinicalAsset.__table__.create(bind=engine)
    finally:
        engine.dispose()


def _counts(root):
    engine = _engine(root)
    try:
        with engine.connect() as c:
            return tuple(c.exec_driver_sql(f"SELECT count(*) FROM {table}").scalar_one()
                         for table in ("clinical_assets", "c05b03c_receipts",
                                       "c05b03c_audit", "c05b03c_outbox"))
    finally:
        engine.dispose()


def _existing(db, claim, root):
    row = db.connection().exec_driver_sql(
        """SELECT tenant,device,capture,receipt_id,patient,staff,station,appointment,
                  reason,digest,byte_size,asset_id,version FROM c05b03c_receipts
           WHERE tenant=? AND device=? AND capture=?""",
        (claim.tenant, claim.device, claim.capture),
    ).fetchone()
    if row is None:
        return None
    if tuple(row[:3]) + tuple(row[4:]) != claim.binding():
        raise ValueError("HISTORICAL_RECEIPT_BINDING_CONFLICT")
    for table, expected in (("c05b03c_audit", "COMMITTED"),
                            ("c05b03c_outbox", "MEDIA_READY")):
        actual = db.connection().exec_driver_sql(
            f"SELECT event FROM {table} WHERE receipt_id=?", (row[3],)
        ).scalar_one_or_none()
        if actual != expected:
            raise ValueError("RECEIPT_AUDIT_OUTBOX_INCOMPLETE")
    proof = verify_device_capture_media_binding(
        db, tenant=claim.tenant, patient=claim.patient, asset_id=claim.asset_id,
        staff_id=claim.staff, digest=claim.digest, byte_size=claim.byte_size,
        media_root=root / "media",
    )
    assert proof.clinical_receipt_authorized is False
    return row[3]


def _authorize(db, claim):
    conn = db.connection()
    approved = conn.exec_driver_sql(
        """SELECT patient,staff,station,appointment,reason,digest,byte_size,
                  asset_id,version,approved FROM c05b03c_approvals
           WHERE tenant=? AND device=? AND capture=?""",
        (claim.tenant, claim.device, claim.capture),
    ).fetchone()
    if approved != (*claim.binding()[3:], 1):
        raise ValueError("APPROVAL_VERSION_OR_BINDING_REJECTED")
    staff = conn.exec_driver_sql(
        "SELECT active,authorized FROM c05b03c_staff WHERE tenant=? AND staff=?",
        (claim.tenant, claim.staff),
    ).fetchone()
    device = conn.exec_driver_sql(
        "SELECT station,active,generation FROM c05b03c_devices WHERE tenant=? AND device=?",
        (claim.tenant, claim.device),
    ).fetchone()
    station = conn.exec_driver_sql(
        "SELECT active FROM c05b03c_workstations WHERE tenant=? AND station=?",
        (claim.tenant, claim.station),
    ).fetchone()
    if staff != (1, 1) or device != (claim.station, 1, 1) or station != (1,):
        raise ValueError("PERSISTED_STAFF_DEVICE_STATION_REVOKED")


def _issue(root, claim, fail_at=None):
    _guard()
    if fail_at not in (None, "after_media", "after_receipt", "after_audit", "after_outbox"):
        raise ValueError("INVALID_FUE_FAILPOINT")
    engine = _engine(root)
    try:
        with Session(engine, expire_on_commit=False) as db:
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            # Reject revoked actors on every requester call, including ACK replay.
            # Immutable historical records remain available through internal audit only.
            _authorize(db, claim)
            old = _existing(db, claim, root)
            if old is not None:
                db.commit()
                return old  # identity-bound ACK replay by a currently authorized requester
            _authorize(db, claim)  # DB authority under writer lock, not client-provided token
            asset = ClinicalAsset(
                id=claim.asset_id, employer_id=claim.tenant, patient_id=claim.patient,
                asset_type="PHOTO", source_kind="DEVICE_CAPTURE", created_by=claim.staff,
                provenance_json={"ingestion_channel": "LOT06_C05B03C_SYNTHETIC_ONLY",
                                 "capture_id": claim.capture, "device": claim.device},
            )
            db.add(asset)
            db.flush()
            stored = store_clinical_asset_bytes(
                db, employer_id=claim.tenant, patient_id=claim.patient,
                asset_id=claim.asset_id, content=_png(), media_root=root / "media",
            )
            assert stored.asset.sha256 == claim.digest
            assert stored.asset.byte_size == claim.byte_size
            assert read_clinical_asset_bytes(
                db, employer_id=claim.tenant, patient_id=claim.patient,
                asset_id=claim.asset_id, media_root=root / "media",
            ) == _png()
            if fail_at == "after_media":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            _authorize(db, claim)
            rid = "TEST-APPROVED-" + secrets.token_hex(16)
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03c_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (*claim.binding()[:3], rid, *claim.binding()[3:]),
            )
            if fail_at == "after_receipt":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03c_audit VALUES(?,?)", (rid, "COMMITTED")
            )
            if fail_at == "after_audit":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            db.connection().exec_driver_sql(
                "INSERT INTO c05b03c_outbox VALUES(?,?)", (rid, "MEDIA_READY")
            )
            if fail_at == "after_outbox":
                raise RuntimeError("INJECTED_SQL_ROLLBACK")
            db.commit()
            return rid
    finally:
        engine.dispose()


def _fixture(tmp_path, monkeypatch, names):
    _guard()
    monkeypatch.setenv("DC06B_TEST_SQLCIPHER_KEY", secrets.token_hex(32))
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", secrets.token_hex(32))
    root = tmp_path / "persistent-approval"
    root.mkdir()
    claims = tuple(_capture(name, 19000 + i) for i, name in enumerate(names))
    _setup(root, claims)
    assert (root / "clinical-asset-lab.db").read_bytes()[:16] != b"SQLite format 3\x00"
    return root, claims


def _change(root, query, args=()):
    engine = _engine(root)
    try:
        with engine.begin() as c:
            c.exec_driver_sql(query, args)
    finally:
        engine.dispose()


def test_c05b03c_approval_refuses_conflict_and_revocation(tmp_path, monkeypatch):
    root, (first,) = _fixture(tmp_path, monkeypatch, ("not-yet-issued",))
    wrong = (
        replace(first, tenant=32), replace(first, device="other"),
        replace(first, station="different"), replace(first, staff=82),
        replace(first, patient=74), replace(first, version=3),
        replace(first, digest="0" * 64), replace(first, appointment=999),
    )
    for claim in wrong:
        with pytest.raises(ValueError, match="APPROVAL_VERSION_OR_BINDING_REJECTED"):
            _issue(root, claim)
    assert _counts(root) == (0, 0, 0, 0)

    for table, column, where, args in (
        ("c05b03c_staff", "active", "tenant=31 AND staff=81", ()),
        ("c05b03c_staff", "authorized", "tenant=31 AND staff=81", ()),
        ("c05b03c_devices", "active", "tenant=31 AND device='lab-device'", ()),
        ("c05b03c_workstations", "active", "tenant=31 AND station='lab-station'", ()),
    ):
        _change(root, f"UPDATE {table} SET {column}=0 WHERE {where}", args)
        with pytest.raises(ValueError, match="PERSISTED_STAFF_DEVICE_STATION_REVOKED"):
            _issue(root, first)
        _change(root, f"UPDATE {table} SET {column}=1 WHERE {where}", args)
    _change(root, "UPDATE c05b03c_approvals SET version=3")
    with pytest.raises(ValueError, match="APPROVAL_VERSION_OR_BINDING_REJECTED"):
        _issue(root, first)
    assert _counts(root) == (0, 0, 0, 0)
    print("LOT06C05B03C_PERSISTED_AUTHORITY_DENIAL_PASS")


def test_c05b03c_atomic_receipt_historical_replay_and_exit(tmp_path, monkeypatch):
    root, (first, ack, blocked) = _fixture(
        tmp_path, monkeypatch, ("rollback-and-success", "lost-ack", "revoked-before-issue")
    )
    for boundary in ("after_media", "after_receipt", "after_audit", "after_outbox"):
        with pytest.raises(RuntimeError, match="INJECTED_SQL_ROLLBACK"):
            _issue(root, first, fail_at=boundary)
        assert _counts(root) == (0, 0, 0, 0)
    assert len(list((root / "media").rglob("*.dcm"))) == 1
    rid = _issue(root, first)
    assert _counts(root) == (1, 1, 1, 1)

    child = subprocess.run(
        [sys.executable, "-m", "isolated_fue_lot06c.test_sqlcipher_persistent_approval_v15",
         "--commit-exit"],
        env=dict(os.environ, DC06C05B03C_ROOT=str(root)),
        text=True, capture_output=True, timeout=60, check=False,
    )
    assert child.returncode == 75, f"POSTCOMMIT_PROCESS_EXIT_{child.returncode}"
    recovered = _issue(root, ack)
    assert recovered.startswith("TEST-APPROVED-") and recovered != rid
    assert all(_issue(root, ack) == recovered for _ in range(3))
    assert _counts(root) == (2, 2, 2, 2)

    _change(root, "UPDATE c05b03c_devices SET active=0")
    with pytest.raises(ValueError, match="PERSISTED_STAFF_DEVICE_STATION_REVOKED"):
        _issue(root, blocked)
    # Revoked requesters must not receive existing receipts either.
    for old_claim in (first, ack):
        with pytest.raises(ValueError, match="PERSISTED_STAFF_DEVICE_STATION_REVOKED"):
            _issue(root, old_claim)
    engine = _engine(root)
    try:
        # This internal-only audit helper retains and verifies evidence after revocation.
        with Session(engine) as audit:
            assert _existing(audit, first, root) == rid
            assert _existing(audit, ack, root) == recovered
            with pytest.raises(ValueError, match="HISTORICAL_RECEIPT_BINDING_CONFLICT"):
                _existing(audit, replace(first, version=7), root)
        with pytest.raises(IntegrityError, match="RECEIPT_IMMUTABLE"):
            with engine.begin() as c:
                c.exec_driver_sql("UPDATE c05b03c_receipts SET version=7")
        with pytest.raises(IntegrityError, match="APPROVAL_BINDING_FROZEN"):
            with engine.begin() as c:
                c.exec_driver_sql(
                    "UPDATE c05b03c_approvals SET version=7 WHERE capture=?",
                    (first.capture,),
                )
        with pytest.raises(IntegrityError, match="APPROVAL_REFERENCED"):
            with engine.begin() as c:
                c.exec_driver_sql(
                    "DELETE FROM c05b03c_approvals WHERE capture=?", (first.capture,)
                )
    finally:
        engine.dispose()
    # Verify corruption denial with a presently authorized requester, not a
    # revoked requester already blocked at the authorization boundary.
    _change(root, "UPDATE c05b03c_devices SET active=1")
    assert _issue(root, first) == rid
    blob = next((root / "media").rglob("*.dcm"))
    data = blob.read_bytes()
    blob.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
    with pytest.raises(MediaBindingRejected, match="MEDIA_INTEGRITY_BLOCKED"):
        _issue(root, first)
    assert _counts(root) == (2, 2, 2, 2)

    evidence_dir = Path(os.environ.get("DC06C05B03C_EVIDENCE_DIR", str(tmp_path)))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "kind": "LOT06_C05B03C_PERSISTENT_SQLCIPHER_APPROVAL_LAB_ONLY",
        "persistent_server_owned_approval_fixture": True,
        "persisted_tenant_staff_device_station_revision_checked": True,
        "cross_tenant_identity_version_and_role_refused": True,
        "revocation_before_issue_refused": True,
        "historical_receipt_internal_audit_after_revocation": True,
        "revoked_requester_receipt_replay_denied": True,
        "receipt_immutable_test_trigger_enforced": True,
        "four_sql_failpoints_atomic_rollback": True,
        "real_aesgcm_media_bound_before_sql_commit": True,
        "postcommit_process_exit_ack_replay": True,
        "tampered_media_blocks_historical_replay": True,
        "foreign_keys_enabled_for_synthetic_authority": True,
        "actual_authenticated_device_or_staff": False,
        "production_approval_schema_migrated": False,
        "powercut_durability_certified": False,
        "windows_ntfs_certified": False,
        "sql_and_media_globally_atomic": False,
        "production_clinical_receipt_enabled": False,
        "product_ready": False,
    }
    (evidence_dir / "lot06c05b03c-persistent-approval-fue.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("LOT06C05B03C_PERSISTENT_RECEIPT_REPLAY_PASS")


def test_c05b03c_six_concurrent_writers_one_receipt(tmp_path, monkeypatch):
    root, (first,) = _fixture(tmp_path, monkeypatch, ("concurrent-issue",))
    with ThreadPoolExecutor(max_workers=6) as pool:
        ids = list(pool.map(lambda _: _issue(root, first), range(6)))
    assert len(set(ids)) == 1
    assert _counts(root) == (1, 1, 1, 1)
    print("LOT06C05B03C_CONCURRENT_ONE_RECEIPT_PASS")


def test_c05b03c_write_lock_prevents_mid_transaction_revocation(tmp_path, monkeypatch):
    root, (first,) = _fixture(tmp_path, monkeypatch, ("race-lock",))
    a, b = _engine(root), _engine(root)
    try:
        with a.connect() as issuing:
            issuing.exec_driver_sql("BEGIN IMMEDIATE")
            with b.connect() as revoker:
                revoker.exec_driver_sql("PRAGMA busy_timeout=1")
                with pytest.raises(OperationalError, match="locked"):
                    revoker.exec_driver_sql("UPDATE c05b03c_devices SET active=0")
                revoker.rollback()
            issuing.rollback()
        _change(root, "UPDATE c05b03c_devices SET active=0")
        with pytest.raises(ValueError, match="PERSISTED_STAFF_DEVICE_STATION_REVOKED"):
            _issue(root, first)
        assert _counts(root) == (0, 0, 0, 0)
    finally:
        a.dispose()
        b.dispose()
    print("LOT06C05B03C_WRITER_SERIALIZATION_PASS")


if __name__ == "__main__" and sys.argv[1:] == ["--commit-exit"]:
    _guard()
    _issue(Path(os.environ["DC06C05B03C_ROOT"]), _capture("lost-ack", 19001))
    os._exit(75)
