"""C05B-03E — real backend staff/station records + encrypted media + SQLCipher receipt.

Synthetic-only FUE, not wired to FastAPI or a cabinet migration. The device
registry and staff approval are explicitly LAB fixtures, not trusted device
enrollment, authenticated human clinical approval, or regulatory evidence.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
from typing import Optional
import uuid

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.routers.auth import has_permission
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import store_clinical_asset_bytes
from backend.services.imaging_clinical_asset_verifier_v15 import (
    MediaBindingRejected, verify_device_capture_media_binding,
)
from isolated_fue_lot06c.test_sqlcipher_clinical_asset_receipt_v15 import _root_engine

metadata = MetaData()
devices = Table(
    "c05b03e_synthetic_devices", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("station", String(36), nullable=False),
    Column("token_sha", String(64), nullable=False),
    Column("generation", Integer, nullable=False),
    Column("active", Integer, nullable=False),
)
approvals = Table(
    "c05b03e_synthetic_approvals", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("patient", Integer, nullable=False),
    Column("staff", Integer, nullable=False),
    Column("station", String(36), nullable=False),
    Column("station_revision", Integer, nullable=False),
    Column("generation", Integer, nullable=False),
    Column("asset_id", Integer, nullable=False),
    Column("digest", String(64), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("version", Integer, nullable=False),
    Column("reason", String(32), nullable=False),
    Column("approved", Integer, nullable=False),
)
receipts = Table(
    "c05b03e_synthetic_receipts", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("receipt_id", String(64), unique=True, nullable=False),
    Column("version", Integer, nullable=False),
    Column("asset_id", Integer, unique=True, nullable=False),
    Column("digest", String(64), nullable=False),
)
audit = Table(
    "c05b03e_synthetic_audit", metadata,
    Column("receipt_id", String(64), primary_key=True),
    Column("event", String(32), nullable=False),
)
outbox = Table(
    "c05b03e_synthetic_outbox", metadata,
    Column("receipt_id", String(64), primary_key=True),
    Column("event", String(32), nullable=False),
)


class BridgeRejected(ValueError):
    """Non-PHI failure code; does not grant clinical authorization."""


@dataclass(frozen=True)
class Claim:
    tenant: int
    device: str
    capture: str
    patient: int
    staff: int
    station: str
    station_revision: int
    generation: int
    asset_id: int
    digest: str
    byte_size: int
    version: int
    reason: str = "LAB_WALK_IN"

    def values(self):
        return dict(
            tenant=self.tenant, device=self.device, capture=self.capture,
            patient=self.patient, staff=self.staff, station=self.station,
            station_revision=self.station_revision, generation=self.generation,
            asset_id=self.asset_id, digest=self.digest, byte_size=self.byte_size,
            version=self.version, reason=self.reason,
        )


def _guard(engine):
    if (
        os.getenv("ENVIRONMENT") != "test"
        or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
        or os.getenv("DC06C05B03E_TEST_ONLY") != "1"
        or engine.dialect.name != "sqlite"
        or str(engine.url) != "sqlite://"
    ):
        raise BridgeRejected("BRIDGE_NOT_ISOLATED")


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _assert_claim(claim: Claim):
    numbers = (
        claim.tenant, claim.patient, claim.staff, claim.asset_id,
        claim.byte_size, claim.version, claim.generation,
    )
    if (
        any(type(x) is not int or x <= 0 for x in numbers)
        or type(claim.station_revision) is not int or claim.station_revision < 0
        or not isinstance(claim.device, str) or not 1 <= len(claim.device) <= 64
        or not isinstance(claim.capture, str) or not 1 <= len(claim.capture) <= 128
        or not isinstance(claim.station, str) or len(claim.station) != 36
        or not isinstance(claim.digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", claim.digest) is None
        or claim.reason != "LAB_WALK_IN"
    ):
        raise BridgeRejected("INVALID_CAPTURE_CLAIM")


def _authority(db: Session, claim: Claim, device_token: str, station_token: str):
    """All authoritative checks occur after BEGIN IMMEDIATE writer lock.

    This test calls the backend's existing real User and WorkstationMode ORM
    and permission policy; the imaging device ledger remains synthetic.
    """
    row = db.execute(select(approvals).where(
        approvals.c.tenant == claim.tenant,
        approvals.c.device == claim.device,
        approvals.c.capture == claim.capture,
    )).mappings().first()
    if row is None or row.get("approved") != 1 or any(
        row.get(k) != value for k, value in claim.values().items()
    ):
        raise BridgeRejected("PERSISTED_APPROVAL_BINDING_OR_VERSION_DENIED")

    dev = db.execute(select(devices).where(
        devices.c.tenant == claim.tenant,
        devices.c.device == claim.device,
    )).mappings().first()
    if (
        not isinstance(device_token, str) or not device_token
        or len(device_token) > 256 or dev is None or dev["active"] != 1
        or dev["station"] != claim.station or dev["generation"] != claim.generation
        or not hmac.compare_digest(dev["token_sha"], _hash(device_token))
    ):
        raise BridgeRejected("DEVICE_TOKEN_OR_REVOKED_DENIED")

    staff = db.query(models.User).filter(models.User.id == claim.staff).first()
    if (
        staff is None or staff.get_employer_id() != claim.tenant
        or not staff.is_active or staff.is_archived or staff.is_suspended
        or staff.approval_status != "approved"
        or not has_permission(staff, "patients")
    ):
        raise BridgeRejected("ACTUAL_STAFF_PERMISSION_OR_REVOKED")

    station = db.query(models.WorkstationMode).filter(
        models.WorkstationMode.id == claim.station,
        models.WorkstationMode.employer_id == claim.tenant,
    ).first()
    if (
        station is None or station.revoked_at is not None
        or station.mode_revision != claim.station_revision
        or not isinstance(station_token, str) or not station_token
        or len(station_token) > 256
        or not hmac.compare_digest(station.token_hash, _hash(station_token))
    ):
        raise BridgeRejected("ACTUAL_STATION_TOKEN_OR_REVOKED")

    patient = db.query(models.Patient).filter(
        models.Patient.id == claim.patient,
        models.Patient.employer_id == claim.tenant,
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        raise BridgeRejected("ACTUAL_PATIENT_SCOPE_REJECTED")


def _issue(engine, claim: Claim, device_token: str, station_token: str,
           media_root: Path, fail_at: Optional[str] = None):
    _guard(engine)
    _assert_claim(claim)
    if fail_at not in (None, "after_receipt", "after_audit", "after_outbox"):
        raise BridgeRejected("INVALID_FAILURE_INJECTION")
    with Session(engine, expire_on_commit=False) as db:
        try:
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
            _authority(db, claim, device_token, station_token)
            asset = db.get(ClinicalAsset, claim.asset_id)
            provenance = asset.provenance_json if asset is not None else None
            if (
                not isinstance(provenance, dict)
                or provenance.get("capture_id") != claim.capture
                or provenance.get("device") != claim.device
                or provenance.get("ingestion_channel") != "C05B03E_SYNTHETIC_ONLY"
            ):
                raise BridgeRejected("CAPTURE_ASSET_PROVENANCE_DENIED")
            try:
                proof = verify_device_capture_media_binding(
                    db, tenant=claim.tenant, patient=claim.patient,
                    asset_id=claim.asset_id, staff_id=claim.staff,
                    digest=claim.digest, byte_size=claim.byte_size,
                    media_root=media_root,
                )
            except MediaBindingRejected as exc:
                raise BridgeRejected("AES_MEDIA_BINDING_DENIED") from exc
            if proof.clinical_receipt_authorized:
                raise BridgeRejected("UNEXPECTED_CLINICAL_AUTHORITY")

            previous = db.execute(select(receipts).where(
                receipts.c.tenant == claim.tenant,
                receipts.c.device == claim.device,
                receipts.c.capture == claim.capture,
            )).mappings().first()
            if previous is not None:
                rid = previous["receipt_id"]
                if (
                    previous["version"] != claim.version
                    or previous["asset_id"] != claim.asset_id
                    or previous["digest"] != claim.digest
                    or db.execute(select(audit.c.event).where(
                        audit.c.receipt_id == rid
                    )).scalar_one_or_none() != "CAPTURE_COMMITTED"
                    or db.execute(select(outbox.c.event).where(
                        outbox.c.receipt_id == rid
                    )).scalar_one_or_none() != "MEDIA_READY"
                ):
                    raise BridgeRejected("IMMUTABLE_RECEIPT_INCOMPLETE_OR_CONFLICT")
                db.commit()
                return rid

            rid = "LAB-ONLY-" + secrets.token_hex(16)
            db.execute(insert(receipts).values(
                tenant=claim.tenant, device=claim.device, capture=claim.capture,
                receipt_id=rid, version=claim.version,
                asset_id=claim.asset_id, digest=claim.digest,
            ))
            if fail_at == "after_receipt":
                raise BridgeRejected("INJECTED_TRANSACTION_ROLLBACK")
            db.execute(insert(audit).values(receipt_id=rid, event="CAPTURE_COMMITTED"))
            if fail_at == "after_audit":
                raise BridgeRejected("INJECTED_TRANSACTION_ROLLBACK")
            db.execute(insert(outbox).values(receipt_id=rid, event="MEDIA_READY"))
            if fail_at == "after_outbox":
                raise BridgeRejected("INJECTED_TRANSACTION_ROLLBACK")
            db.commit()
            return rid
        except BaseException:
            db.rollback()
            raise


def _counts(engine):
    with engine.connect() as conn:
        return tuple(conn.exec_driver_sql(
            f"SELECT COUNT(*) FROM {table.name}"
        ).scalar_one() for table in (receipts, audit, outbox))


@pytest.fixture()
def bridge(tmp_path, monkeypatch):
    if (
        os.getenv("ENVIRONMENT") != "test"
        or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
        or os.getenv("DC06C05B03E_TEST_ONLY") != "1"
    ):
        raise BridgeRejected("SYNTHETIC_FIXTURE_DISABLED")
    monkeypatch.setenv("DC06B_TEST_SQLCIPHER_KEY", secrets.token_hex(32))
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", secrets.token_hex(32))
    root = tmp_path / "real-staff-station-bridge"
    root.mkdir()
    engine = _root_engine(root)
    _guard(engine)
    for table in (
        models.User.__table__, models.Patient.__table__,
        models.WorkstationMode.__table__, ClinicalAsset.__table__,
    ):
        table.create(bind=engine)
    metadata.create_all(engine)
    station_token, device_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    capture = "synthetic-" + uuid.uuid4().hex
    device = "device-" + uuid.uuid4().hex[:16]
    data = b"C05B03E synthetic no-patient imaging media"
    try:
        with Session(engine) as db:
            owner = models.User(
                email="lab-owner-" + uuid.uuid4().hex + "@invalid.test",
                hashed_password="not-a-real-password",
                role="DENTISTE", is_active=True, is_licensed=True,
                nom_complet="Synthetic Owner",
            )
            db.add(owner)
            db.flush()
            staff = models.User(
                email="lab-staff-" + uuid.uuid4().hex + "@invalid.test",
                hashed_password="not-a-real-password",
                role="SECRETAIRE", is_active=True, is_licensed=True,
                employer_id=owner.id, approval_status="approved",
                permissions={"patients": True}, nom_complet="Synthetic Staff",
            )
            patient = models.Patient(
                employer_id=owner.id, nom="Synthetic", prenom="Patient",
                date_naissance=datetime(2000, 1, 1), sexe="F",
            )
            station = models.WorkstationMode(
                id=str(uuid.uuid4()), employer_id=owner.id,
                token_hash=_hash(station_token), mode_revision=0,
                default_experience="cabinet", display_name="Synthetic Station",
            )
            db.add_all([staff, patient, station])
            db.flush()
            asset = create_clinical_asset(
                db, employer_id=owner.id, patient_id=patient.id,
                asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
                created_by=staff.id,
                provenance_json={
                    "ingestion_channel": "C05B03E_SYNTHETIC_ONLY",
                    "capture_id": capture, "device": device,
                },
            )
            store_clinical_asset_bytes(
                db, employer_id=owner.id, patient_id=patient.id,
                asset_id=asset.id, content=data, media_root=root / "media",
            )
            claim = Claim(
                tenant=owner.id, device=device, capture=capture,
                patient=patient.id, staff=staff.id, station=station.id,
                station_revision=0, generation=1, asset_id=asset.id,
                digest=hashlib.sha256(data).hexdigest(),
                byte_size=len(data), version=2,
            )
            db.execute(insert(devices).values(
                tenant=owner.id, device=device, station=station.id,
                token_sha=_hash(device_token), generation=1, active=1,
            ))
            db.execute(insert(approvals).values(**claim.values(), approved=1))
            db.commit()
        assert (root / "clinical-asset-lab.db").read_bytes()[:16] != bytes.fromhex(
            "53514c69746520666f726d6174203300"
        )
        yield (engine, claim, device_token, station_token, root / "media", tmp_path)
    finally:
        engine.dispose()


def _change(engine, table, *conditions, **changes):
    with engine.begin() as conn:
        conn.execute(update(table).where(*conditions).values(**changes))


def test_c05b03e_real_backend_principals_bridge_and_negatives(bridge, monkeypatch):
    engine, claim, device_token, station_token, media_root, tmp = bridge
    args = (engine, claim, device_token, station_token, media_root)
    assert _counts(engine) == (0, 0, 0)
    for bad in (
        replace(claim, tenant=claim.tenant + 999),
        replace(claim, staff=claim.staff + 999),
        replace(claim, patient=claim.patient + 999),
        replace(claim, station=str(uuid.uuid4())),
        replace(claim, version=3),
        replace(claim, digest="0" * 64),
        replace(claim, generation=2),
        replace(claim, byte_size=claim.byte_size + 1),
        replace(claim, asset_id=claim.asset_id + 999),
    ):
        with pytest.raises(BridgeRejected):
            _issue(engine, bad, device_token, station_token, media_root)
    with pytest.raises(BridgeRejected, match="DEVICE_TOKEN"):
        _issue(engine, claim, "wrong", station_token, media_root)
    with pytest.raises(BridgeRejected, match="STATION_TOKEN"):
        _issue(engine, claim, device_token, "wrong", media_root)
    assert _counts(engine) == (0, 0, 0)
    for at in ("after_receipt", "after_audit", "after_outbox"):
        with pytest.raises(BridgeRejected, match="INJECTED_TRANSACTION"):
            _issue(*args, fail_at=at)
        assert _counts(engine) == (0, 0, 0)
    rid = _issue(*args)
    assert rid.startswith("LAB-ONLY-")
    assert all(_issue(*args) == rid for _ in range(3))
    assert _counts(engine) == (1, 1, 1)

    _change(engine, models.User.__table__,
            models.User.__table__.c.id == claim.staff,
            permissions={"patients": False})
    with pytest.raises(BridgeRejected, match="STAFF_PERMISSION"):
        _issue(*args)
    _change(engine, models.User.__table__,
            models.User.__table__.c.id == claim.staff,
            permissions={"patients": True}, is_active=False)
    with pytest.raises(BridgeRejected, match="STAFF_PERMISSION"):
        _issue(*args)
    _change(engine, models.User.__table__,
            models.User.__table__.c.id == claim.staff, is_active=True)
    _change(engine, models.WorkstationMode.__table__,
            models.WorkstationMode.__table__.c.id == claim.station,
            revoked_at=datetime.utcnow())
    with pytest.raises(BridgeRejected, match="STATION_TOKEN_OR_REVOKED"):
        _issue(*args)
    _change(engine, models.WorkstationMode.__table__,
            models.WorkstationMode.__table__.c.id == claim.station,
            revoked_at=None)
    _change(engine, devices, devices.c.device == claim.device, active=0)
    with pytest.raises(BridgeRejected, match="DEVICE_TOKEN_OR_REVOKED"):
        _issue(*args)
    _change(engine, devices, devices.c.device == claim.device, active=1)
    assert _issue(*args) == rid
    blob = next(media_root.rglob("*.dcm"))
    original = blob.read_bytes()
    blob.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    with pytest.raises(BridgeRejected, match="AES_MEDIA_BINDING_DENIED"):
        _issue(*args)
    blob.write_bytes(original)
    assert _issue(*args) == rid
    assert _counts(engine) == (1, 1, 1)

    destination = Path(os.getenv("DC06C05B03E_EVIDENCE_DIR", str(tmp)))
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "lot06c05b03e-real-backend-identity-bridge.json").write_text(
        json.dumps({
            "kind": "C05B03E_ACTUAL_BACKEND_STAFF_WORKSTATION_AND_SQLCIPHER_LAB",
            "actual_user_and_workstation_mode_models_used": True,
            "backend_has_permission_called_after_writer_lock": True,
            "synthetic_device_token_revocation_enforced": True,
            "same_sqlcipher_approval_version_aes_and_receipt_bound": True,
            "wrong_scope_and_credential_denied": True,
            "revoked_staff_station_device_receipt_replay_denied": True,
            "negative_sql_failure_atomic_rollback": True,
            "corrupt_media_receipt_replay_denied": True,
            "production_device_issuer_integrated": False,
            "actual_http_identity_session_verified": False,
            "real_human_approval_ceremony_verified": False,
            "alembic_authority_migration_implemented": False,
            "clinical_receipt_authorized": False,
            "product_ready": False,
            "clinical_go": False,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8",
    )
    print("C05B03E_BACKEND_STAFF_STATION_DEVICE_SQLCIPHER_AES_LAB_PASS")


def test_c05b03e_six_writers_single_receipt(bridge):
    engine, claim, token, station, media_root, _tmp = bridge
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [
            pool.submit(_issue, engine, claim, token, station, media_root)
            for _ in range(6)
        ]
        ids = [x.result(timeout=35) for x in futures]
    assert len(set(ids)) == 1
    assert _counts(engine) == (1, 1, 1)
    print("C05B03E_SIX_SQLCIPHER_WRITERS_ONE_RECEIPT_PASS")


def test_c05b03e_default_is_disabled(bridge, monkeypatch):
    engine, claim, token, station, media_root, _tmp = bridge
    monkeypatch.delenv("DC06C05B03E_TEST_ONLY")
    with pytest.raises(BridgeRejected, match="BRIDGE_NOT_ISOLATED"):
        _issue(engine, claim, token, station, media_root)
    monkeypatch.setenv("DC06C05B03E_TEST_ONLY", "1")
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    with pytest.raises(BridgeRejected, match="BRIDGE_NOT_ISOLATED"):
        _issue(engine, claim, token, station, media_root)
    assert _counts(engine) == (0, 0, 0)
    print("C05B03E_PRODUCTION_GUARD_FAIL_CLOSED_PASS")
