"""LOT06-B genuine FastAPI -> Media Core *synthetic isolated* HTTP transfer contract.

Never enabled outside TEST + in-memory SQLite + explicit flag. This is NOT a
production device trust root, clinical enrollment scheme, or SQLCipher proof.
The actual encrypted ClinicalAsset, SQL receipt, audit and outbox share one
SQLAlchemy commit; filesystem and SQL do NOT share an atomic transaction.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, MetaData, String, Table, insert, select, update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.routers.auth import has_permission
from backend.services.clinical_asset_ingestion import (
    ClinicalAssetIngestionError, ingest_clinical_asset_bytes, validate_clinical_import_payload,
)
from backend.services.clinical_asset_storage import (
    ClinicalAssetStorageError, read_clinical_asset_bytes,
)
from backend.services.imaging_acquisition_preflight_v15 import (
    PreflightRejected, resolve_acquisition_preflight,
)

metadata = MetaData()
# Provisional LAB-only structured codes, not the final cabinet wording/policy.
# Free text is intentionally prohibited to avoid logging patient information.
PATIENT_ONLY_REASON_CODES = frozenset({
    "LAB_WALK_IN", "LAB_UNSCHEDULED", "LAB_URGENT",
})


def _reason(appointment: int | None, reason: str | None) -> str | None:
    if appointment is None:
        if reason not in PATIENT_ONLY_REASON_CODES:
            raise TransferLabRejected("PATIENT_ONLY_REASON_REQUIRED", 422)
    elif reason is not None:
        raise TransferLabRejected("PATIENT_ONLY_REASON_WITH_RDV", 422)
    return reason


devices = Table(
    "lot06b_lab_devices", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("token_sha", String(64), nullable=False),
    Column("active", Boolean, nullable=False),
)
captures = Table(
    "lot06b_lab_captures", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("digest", String(64), nullable=False),
    Column("size", Integer, nullable=False),
    Column("patient", Integer),
    Column("appointment", Integer),
    Column("staff", Integer),
    Column("workstation", String(36)),
    # Synthetic server-issued, bound, one-time review challenge.
    Column("review_sha", String(64)),
    Column("review_deadline", Integer),
    Column("review_staff", Integer),
    Column("review_station", String(36)),
    Column("review_patient", Integer),
    Column("review_appointment", Integer),
    Column("review_reason", String(32)),
    # Immutable once explicitly approved; still only an isolated LAB ledger.
    Column("patient_only_reason", String(32)),
)
receipts = Table(
    "lot06b_lab_receipts", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("receipt_id", String(64), unique=True, nullable=False),
    Column("asset_id", Integer, unique=True, nullable=False),
    Column("patient", Integer, nullable=False),
    Column("digest", String(64), nullable=False),
)
audit = Table(
    "lot06b_lab_audit", metadata,
    Column("receipt_id", String(64), primary_key=True),
    Column("event", String(64), nullable=False),
    Column("patient_only_reason", String(32)),
)
outbox = Table(
    "lot06b_lab_outbox", metadata,
    Column("receipt_id", String(64), primary_key=True),
    Column("event", String(64), nullable=False),
)


class TransferLabRejected(ValueError):
    def __init__(self, reason: str, status_code: int = 409):
        self.reason = reason
        self.status_code = status_code
        super().__init__(reason)


def guard(db: Session) -> None:
    # An opt-in flag alone is NOT enough, even when set in a cabinet environment.
    bind = db.get_bind()
    if (os.getenv("ENVIRONMENT") != "test"
            or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME", "").lower() not in {"1", "true"}
            or os.getenv("DC_V15_06_TRANSFER_LAB") != "1"
            or bind.dialect.name != "sqlite"
            or ":memory:" not in str(bind.url)):
        raise TransferLabRejected("ISOLATED_TRANSFER_DISABLED", 503)
    metadata.create_all(bind=bind, checkfirst=True)


def enroll_fixture(db: Session, *, tenant: int, device: str) -> str:
    """LAB-ONLY synthetic admin fixture; never exposed as an HTTP enrollment API."""
    guard(db)
    token = secrets.token_urlsafe(32)
    db.execute(insert(devices).values(
        tenant=tenant, device=device, token_sha=hashlib.sha256(token.encode()).hexdigest(),
        active=True,
    ))
    db.commit()
    return token


def _device(db: Session, *, tenant: int, device: str, token: str) -> None:
    guard(db)
    if not token or len(token) > 256:
        raise TransferLabRejected("DEVICE_AUTH_REQUIRED", 401)
    row = db.execute(select(devices).where(
        devices.c.tenant == tenant, devices.c.device == device
    )).mappings().first()
    if (row is None or not row["active"] or not hmac.compare_digest(
        str(row["token_sha"]), hashlib.sha256(token.encode()).hexdigest()
    )):
        raise TransferLabRejected("DEVICE_AUTH_REQUIRED", 401)


def propose(db: Session, *, tenant: int, device: str, token: str, capture: str,
            digest: str, size: int) -> dict:
    _device(db, tenant=tenant, device=device, token=token)
    old = db.execute(select(captures).where(
        captures.c.tenant == tenant, captures.c.device == device,
        captures.c.capture == capture,
    )).mappings().first()
    if old:
        if old["digest"] != digest or old["size"] != size:
            raise TransferLabRejected("CAPTURE_IDENTITY_CONFLICT")
        return {"status": "AWAITING_STAFF", "server_confirmed": False}
    db.execute(insert(captures).values(
        tenant=tenant, device=device, capture=capture, digest=digest, size=size,
    ))
    db.commit()
    return {"status": "AWAITING_STAFF", "server_confirmed": False}


def issue_review(db: Session, *, staff: models.User, tenant: int, workstation: str,
                 device: str, capture: str, patient: int, appointment: int | None,
                 patient_only_reason: str | None = None) -> dict:
    """Synthetic server-issued one-use binding, NOT operator UI proof."""
    guard(db)
    if int(staff.get_employer_id()) != tenant or not has_permission(staff, "patients"):
        raise TransferLabRejected("STAFF_NOT_AUTHORIZED", 403)
    try:
        decision = resolve_acquisition_preflight(
            db, employer_id=tenant, patient_id=patient, appointment_id=appointment
        )
    except PreflightRejected as exc:
        raise TransferLabRejected(exc.reason, exc.status_code) from exc
    if decision.patient_id != patient or decision.status != "STAFF_CONFIRMATION_REQUIRED":
        raise TransferLabRejected("PATIENT_LINK_REQUIRED", 409)
    patient_only_reason = _reason(appointment, patient_only_reason)
    where = (
        (captures.c.tenant == tenant) & (captures.c.device == device)
        & (captures.c.capture == capture)
    )
    row = db.execute(select(captures).where(where)).mappings().first()
    if not row:
        raise TransferLabRejected("CAPTURE_NOT_FOUND", 404)
    if row["staff"] is not None:
        raise TransferLabRejected("ALREADY_APPROVED", 409)
    receipt = db.execute(select(receipts.c.receipt_id).where(
        (receipts.c.tenant == tenant) & (receipts.c.device == device)
        & (receipts.c.capture == capture)
    )).first()
    if receipt:
        raise TransferLabRejected("ALREADY_COMMITTED", 409)
    challenge = secrets.token_urlsafe(32)
    deadline = int(time.time()) + 300
    # A new review invalidates every older outstanding challenge.
    db.execute(update(captures).where(where).values(
        review_sha=hashlib.sha256(challenge.encode()).hexdigest(),
        review_deadline=deadline, review_staff=staff.id,
        review_station=workstation, review_patient=patient,
        review_appointment=appointment, review_reason=patient_only_reason,
    ))
    db.commit()
    return {
        "status": "STAFF_REVIEW_REQUIRED", "review_challenge": challenge,
        "expires_at": deadline, "patient_id": patient,
        "appointment_id": appointment,
        "patient_only_reason": patient_only_reason,
        "server_confirmed": False,
    }


def approve(db: Session, *, staff: models.User, tenant: int, workstation: str,
            device: str, capture: str, patient: int, appointment: int | None,
            review_challenge: str, patient_only_reason: str | None = None) -> dict:
    guard(db)
    if int(staff.get_employer_id()) != tenant or not has_permission(staff, "patients"):
        raise TransferLabRejected("STAFF_NOT_AUTHORIZED", 403)
    try:
        decision = resolve_acquisition_preflight(
            db, employer_id=tenant, patient_id=patient, appointment_id=appointment
        )
    except PreflightRejected as exc:
        raise TransferLabRejected(exc.reason, exc.status_code) from exc
    if decision.patient_id != patient or decision.status != "STAFF_CONFIRMATION_REQUIRED":
        raise TransferLabRejected("PATIENT_LINK_REQUIRED")
    patient_only_reason = _reason(appointment, patient_only_reason)
    where = (
        (captures.c.tenant == tenant) & (captures.c.device == device)
        & (captures.c.capture == capture)
    )
    row = db.execute(select(captures).where(where)).mappings().first()
    if not row:
        raise TransferLabRejected("CAPTURE_NOT_FOUND", 404)
    receipt = db.execute(select(receipts.c.receipt_id).where(
        (receipts.c.tenant == tenant) & (receipts.c.device == device)
        & (receipts.c.capture == capture)
    )).first()
    if receipt:
        raise TransferLabRejected("ALREADY_COMMITTED")
    if row["staff"] is not None:
        raise TransferLabRejected("ALREADY_APPROVED", 409)
    if not review_challenge or len(review_challenge) > 256 or not row["review_sha"]:
        raise TransferLabRejected("STAFF_REVIEW_CHALLENGE_REQUIRED", 403)
    if (row["review_staff"] != staff.id or row["review_station"] != workstation
            or row["review_patient"] != patient
            or row["review_appointment"] != appointment
            or row["review_reason"] != patient_only_reason):
        raise TransferLabRejected("STAFF_REVIEW_BINDING_MISMATCH", 403)
    if not row["review_deadline"] or int(time.time()) >= row["review_deadline"]:
        raise TransferLabRejected("STAFF_REVIEW_EXPIRED", 403)
    supplied = hashlib.sha256(review_challenge.encode()).hexdigest()
    if not hmac.compare_digest(str(row["review_sha"]), supplied):
        raise TransferLabRejected("STAFF_REVIEW_CHALLENGE_INVALID", 403)
    applied = db.execute(update(captures).where(
        where & (captures.c.review_sha == supplied) & (captures.c.staff.is_(None))
    ).values(
        patient=patient, appointment=appointment, staff=staff.id, workstation=workstation,
        patient_only_reason=patient_only_reason,
        review_sha=None, review_deadline=None, review_staff=None,
        review_station=None, review_patient=None, review_appointment=None,
        review_reason=None,
    ))
    if applied.rowcount != 1:
        db.rollback()
        raise TransferLabRejected("STAFF_REVIEW_ALREADY_CONSUMED", 409)
    db.commit()
    return {"status": "APPROVED", "server_confirmed": False}


def _receipt(db: Session, *, tenant: int, device: str, capture: str) -> dict | None:
    row = db.execute(select(receipts).where(
        receipts.c.tenant == tenant, receipts.c.device == device,
        receipts.c.capture == capture,
    )).mappings().first()
    if row is None:
        return None
    asset = db.query(ClinicalAsset).filter(
        ClinicalAsset.id == row["asset_id"], ClinicalAsset.employer_id == tenant,
        ClinicalAsset.patient_id == row["patient"],
    ).first()
    if asset is None or asset.sha256 != row["digest"]:
        raise TransferLabRejected("RECEIPT_INTEGRITY_BLOCKED", 503)
    try:
        content = read_clinical_asset_bytes(
            db, employer_id=tenant, patient_id=row["patient"], asset_id=asset.id
        )
    except ClinicalAssetStorageError as exc:
        raise TransferLabRejected("RECEIPT_INTEGRITY_BLOCKED", 503) from exc
    if hashlib.sha256(content).hexdigest() != row["digest"]:
        raise TransferLabRejected("RECEIPT_INTEGRITY_BLOCKED", 503)
    return {
        "status": "LAB_SERVER_RECEIPT", "receipt_id": row["receipt_id"],
        "asset_id": row["asset_id"], "patient_id": row["patient"],
        "sha256": row["digest"],
        "server_confirmed": False,  # never make a clinical assertion
    }


def lookup(db: Session, *, tenant: int, device: str, token: str, capture: str) -> dict:
    _device(db, tenant=tenant, device=device, token=token)
    return _receipt(db, tenant=tenant, device=device, capture=capture) or {
        "status": "PENDING", "receipt_id": None, "server_confirmed": False,
    }


def transfer(db: Session, *, tenant: int, device: str, token: str, capture: str,
             payload: bytes, mime: str, fail_at: str | None = None) -> dict:
    if fail_at not in (None, "after_ingest", "after_receipt", "after_audit", "after_outbox"):
        raise TransferLabRejected("INVALID_LAB_FAILPOINT", 422)
    _device(db, tenant=tenant, device=device, token=token)
    where = (
        (captures.c.tenant == tenant) & (captures.c.device == device)
        & (captures.c.capture == capture)
    )
    row = db.execute(select(captures).where(where)).mappings().first()
    if row is None:
        raise TransferLabRejected("CAPTURE_NOT_FOUND", 404)
    if (len(payload) != row["size"] or
            hashlib.sha256(payload).hexdigest() != row["digest"]):
        raise TransferLabRejected("PAYLOAD_BINDING_CONFLICT")
    existing = _receipt(db, tenant=tenant, device=device, capture=capture)
    if existing is not None:
        return existing
    if row["staff"] is None or row["patient"] is None:
        raise TransferLabRejected("EXPLICIT_STAFF_APPROVAL_REQUIRED", 403)
    # Never commit a patient-only image whose reason was not bound at approval.
    _reason(row["appointment"], row["patient_only_reason"])
    current_staff = db.query(models.User).filter(
        models.User.id == row["staff"], models.User.is_active.is_(True)
    ).first()
    if (current_staff is None or int(current_staff.get_employer_id()) != tenant
            or not has_permission(current_staff, "patients")):
        raise TransferLabRejected("STAFF_REVOKED", 403)
    try:
        resolution = resolve_acquisition_preflight(
            db, employer_id=tenant, patient_id=row["patient"],
            appointment_id=row["appointment"],
        )
    except PreflightRejected as exc:
        raise TransferLabRejected(exc.reason, exc.status_code) from exc
    if resolution.patient_id != row["patient"]:
        raise TransferLabRejected("PATIENT_LINK_STALE")
    # Protect against staff workstation revocation after the confirmation.
    station = db.query(models.WorkstationMode).filter(
        models.WorkstationMode.id == row["workstation"],
        models.WorkstationMode.employer_id == tenant,
        models.WorkstationMode.revoked_at.is_(None),
    ).first()
    if station is None:
        raise TransferLabRejected("STATION_REVOKED", 403)
    # SQLite's default driver may open a SAVEPOINT without a real outer BEGIN
    # after SELECT-only SQLAlchemy work. A no-op DML starts the actual SQLite
    # writer transaction before ingestion's nested SAVEPOINT. The SQL commit
    # must cover ClinicalAsset, receipt, audit and outbox as one unit.
    # This test-only ledger is disabled on every persistent/production DB.
    db.execute(update(captures).where(where).values(size=row["size"]))
    try:
        validated = validate_clinical_import_payload(
            payload, claimed_mime_type=mime,
        )
        if not validated.mime_type.startswith("image/"):
            raise TransferLabRejected("LAB_PHOTO_ONLY", 422)
        result = ingest_clinical_asset_bytes(
            db, employer_id=tenant, patient_id=row["patient"],
            asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
            content=payload, claimed_mime_type=mime,
            created_by=row["staff"],
            provenance_json={
                "ingestion_channel": "LOT06B_LAB_ONLY",
                "device_proof": "ISOLATED_FIXTURE_TOKEN",
                "capture_id": capture,
            },
        )
        if fail_at == "after_ingest":
            raise TransferLabRejected("INJECTED_LAB_ROLLBACK", 503)
        rid = "LAB-SERVER-" + secrets.token_hex(16)
        db.execute(insert(receipts).values(
            tenant=tenant, device=device, capture=capture,
            receipt_id=rid, asset_id=result.asset.id,
            patient=row["patient"], digest=row["digest"],
        ))
        if fail_at == "after_receipt":
            raise TransferLabRejected("INJECTED_LAB_ROLLBACK", 503)
        db.execute(insert(audit).values(
            receipt_id=rid, event="LAB_ACQUISITION_COMMITTED",
            patient_only_reason=row["patient_only_reason"],
        ))
        if fail_at == "after_audit":
            raise TransferLabRejected("INJECTED_LAB_ROLLBACK", 503)
        db.execute(insert(outbox).values(
            receipt_id=rid, event="LAB_MEDIA_READY"
        ))
        if fail_at == "after_outbox":
            raise TransferLabRejected("INJECTED_LAB_ROLLBACK", 503)
        db.commit()
        db.refresh(result.asset)
    except (ClinicalAssetIngestionError, ClinicalAssetStorageError, IntegrityError,
            OSError, ValueError):
        db.rollback()
        raise
    # Even if HTTP response is lost, an authenticated /receipt re-lookup
    # recovers this same SQL receipt; source spool must not be dropped early.
    return _receipt(db, tenant=tenant, device=device, capture=capture)
