"""LOT06 Phase 2: a real HTTP staff review ceremony bound to SQLCipher.

TEST-ONLY. Not mounted by backend.main, NOT production service/device trust.
The staff HTTP call is a simulated UI action, not proof of a human click.
Clinical media publication stays guarded by the existing signed 03M authority.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time

from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select, update
from sqlalchemy.orm import Session

from backend import models
from backend.routers import auth
from backend.routers.auth import has_permission
from backend.services.imaging_acquisition_preflight_v15 import (
    PreflightRejected, resolve_acquisition_preflight,
)
from isolated_fue_lot06c import c05b03m_security_gate_lab as gate
from isolated_fue_lot06c import unassigned_device_manifest_lab as unassigned_manifest


metadata = MetaData()
reviews = Table(
    "c05b03_phase2_staff_ui_challenge_lab", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("staff", Integer, nullable=False),
    Column("station", String(36), nullable=False),
    Column("patient", Integer, nullable=False),
    Column("appointment", Integer),
    Column("digest", String(64), nullable=False),
    Column("byte_size", Integer, nullable=False),
    Column("challenge_sha", String(64), nullable=False),
    Column("expires_at", Integer, nullable=False),
    Column("consumed", Integer, nullable=False),
)
audit = Table(
    "c05b03_phase2_staff_ui_audit_lab", metadata,
    Column("tenant", Integer, primary_key=True),
    Column("device", String(64), primary_key=True),
    Column("capture", String(128), primary_key=True),
    Column("staff", Integer, nullable=False),
    Column("event", String(48), nullable=False),
)


class ReviewInput(BaseModel):
    challenge: str = Field(min_length=20, max_length=128)
    selected_patient_id: int
    dossier: str = Field(min_length=1, max_length=20)
    date_naissance: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    capture_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    explicit_confirmation: bool


class ReviewDenied(ValueError):
    pass


def _isolation(db: Session) -> None:
    if os.getenv("DC06_PHASE2_REVIEW_LAB") != "1":
        raise ReviewDenied("PHASE2_REVIEW_DISABLED")
    gate._guard(db)  # actual SQLCipher and isolated test-only OS environment


def _authority(db: Session, *, claim, staff_id: int):
    if staff_id != claim.staff:
        raise ReviewDenied("WRONG_STAFF_SESSION")
    staff = db.get(models.User, staff_id)
    station = db.get(models.WorkstationMode, claim.station)
    if (staff is None or not staff.is_active or staff.is_archived or staff.is_suspended
            or staff.approval_status != "approved"
            or int(staff.get_employer_id()) != claim.tenant
            or not has_permission(staff, "patients")
            or station is None or station.employer_id != claim.tenant
            or station.revoked_at is not None
            or station.mode_revision != claim.station_revision):
        raise ReviewDenied("STAFF_OR_STATION_REVOKED")
    try:
        preflight = resolve_acquisition_preflight(
            db, employer_id=claim.tenant, patient_id=claim.patient,
            appointment_id=None,
        )
    except PreflightRejected as exc:
        raise ReviewDenied("PATIENT_LINK_DENIED") from exc
    if (preflight.status != "STAFF_CONFIRMATION_REQUIRED"
            or preflight.patient_id != claim.patient):
        raise ReviewDenied("PATIENT_LINK_DENIED")
    patient = db.get(models.Patient, claim.patient)
    if (patient is None or patient.employer_id != claim.tenant
            or patient.deleted_at is not None
            or not patient.numero_dossier or patient.date_naissance is None):
        raise ReviewDenied("TWO_PATIENT_MARKERS_REQUIRED")
    return patient


def _guarded_capture(db: Session, claim):
    device = db.execute(select(gate.identity).where(
        gate.identity.c.tenant == claim.tenant,
        gate.identity.c.device == claim.device,
    )).mappings().one_or_none()
    approval = db.execute(select(gate.review).where(
        gate.review.c.tenant == claim.tenant,
        gate.review.c.device == claim.device,
        gate.review.c.capture == claim.capture,
    )).mappings().one_or_none()
    if (device is None or device["active"] != 1
            or device["station"] != claim.station
            or device["generation"] != claim.generation
            or approval is None or approval["consumed"] != 0
            or approval["approved_at"] is not None
            or approval["expires_at"] <= int(time.time())
            or any(approval[key] != val for key, val in gate._claim_values(claim).items())):
        raise ReviewDenied("DEVICE_OR_CAPTURE_BINDING_DENIED")
    return approval


def begin(db: Session, *, claim, staff_id: int) -> dict:
    _isolation(db)
    # Table is installed by mount_lab_review before opening any request session.
    db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    try:
        patient = _authority(db, claim=claim, staff_id=staff_id)
        _guarded_capture(db, claim)
        unassigned_manifest.check_pending(db, claim)
        challenge = secrets.token_urlsafe(32)
        now = int(time.time())
        expiry = min(now + 120, now + 119)
        where = (
            (reviews.c.tenant == claim.tenant)
            & (reviews.c.device == claim.device)
            & (reviews.c.capture == claim.capture)
        )
        db.execute(reviews.delete().where(where))
        db.execute(insert(reviews).values(
            tenant=claim.tenant, device=claim.device, capture=claim.capture,
            staff=staff_id, station=claim.station, patient=claim.patient,
            appointment=None, digest=claim.digest,
            byte_size=claim.byte_size,
            challenge_sha=hashlib.sha256(challenge.encode()).hexdigest(),
            expires_at=expiry, consumed=0,
        ))
        db.commit()
        return {
            "status": "STAFF_REVIEW_REQUIRED", "lab_only": True,
            "clinical_receipt_authorized": False, "challenge": challenge,
            "expires_at": expiry,
            "patient_id": patient.id,
            "nom": patient.nom, "prenom": patient.prenom,
            "numero_dossier": patient.numero_dossier,
            "date_naissance": patient.date_naissance.date().isoformat(),
            "capture_digest": claim.digest,
            "capture_size": claim.byte_size,
            "capture": claim.capture,
            "preview_url": "/isolated/lot06-phase2/preview/" + claim.capture,
        }
    except Exception:
        db.rollback()
        raise


def confirm(db: Session, *, claim, staff_id: int, data: ReviewInput) -> dict:
    _isolation(db)
    # Keep UI challenge, preflight and security-gate approval in ONE SQLCipher commit.
    db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    try:
        patient = _authority(db, claim=claim, staff_id=staff_id)
        approved = _guarded_capture(db, claim)
        unassigned_manifest.check_pending(db, claim)
        row = db.execute(select(reviews).where(
            reviews.c.tenant == claim.tenant,
            reviews.c.device == claim.device,
            reviews.c.capture == claim.capture,
        )).mappings().one_or_none()
        if row is None or row["consumed"] != 0 or row["expires_at"] <= int(time.time()):
            raise ReviewDenied("REVIEW_ABSENT_EXPIRED_OR_CONSUMED")
        if (data.explicit_confirmation is not True
                or row["staff"] != staff_id or row["station"] != claim.station
                or row["patient"] != claim.patient
                or row["appointment"] != None
                or row["digest"] != claim.digest or row["byte_size"] != claim.byte_size
                or data.selected_patient_id != patient.id
                or data.dossier != patient.numero_dossier
                or data.date_naissance != patient.date_naissance.date().isoformat()
                or data.capture_digest != claim.digest
                or not hmac.compare_digest(
                    hashlib.sha256(data.challenge.encode()).hexdigest(),
                    row["challenge_sha"],
                )):
            raise ReviewDenied("EXPLICIT_REVIEW_BINDING_MISMATCH")
        updated = db.execute(update(reviews).where(
            reviews.c.tenant == claim.tenant,
            reviews.c.device == claim.device,
            reviews.c.capture == claim.capture,
            reviews.c.consumed == 0,
            reviews.c.challenge_sha == row["challenge_sha"],
        ).values(consumed=1))
        if updated.rowcount != 1:
            raise ReviewDenied("REVIEW_RACE_DENIED")
        gate_updated = db.execute(update(gate.review).where(
            gate.review.c.tenant == claim.tenant,
            gate.review.c.device == claim.device,
            gate.review.c.capture == claim.capture,
            gate.review.c.approved_at.is_(None),
            gate.review.c.consumed == 0,
            gate.review.c.challenge == approved["challenge"],
        ).values(approved_at=int(time.time())))
        if gate_updated.rowcount != 1:
            raise ReviewDenied("STAFF_APPROVAL_RACE_DENIED")
        # Patient-free manifest consumed in the SAME SQLCipher staff review commit.
        unassigned_manifest.consume_for_review(db, claim)
        db.execute(insert(audit).values(
            tenant=claim.tenant, device=claim.device, capture=claim.capture,
            staff=staff_id, event="LAB_HTTP_EXPLICIT_STAFF_CONFIRM",
        ))
        db.execute(insert(gate.review_audit).values(
            tenant=claim.tenant, device=claim.device, capture=claim.capture,
            staff=staff_id, event="LAB_HTTP_EXPLICIT_STAFF_CONFIRM",
        ))
        db.commit()
        return {
            "status": "STAFF_REVIEWED_LAB_ONLY",
            "clinical_receipt_authorized": False,
        }
    except Exception:
        db.rollback()
        raise


def mount_lab_review(app, *, claim, validated_media: bytes):
    """Mounted ONLY on an isolated fixture server; never in backend.main."""
    if (os.getenv("ENVIRONMENT") != "test"
            or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.getenv("DC06_PHASE2_REVIEW_LAB") != "1"):
        raise ReviewDenied("ISOLATED_REVIEW_MOUNT_DISABLED")
    if (len(validated_media) != claim.byte_size or
            hashlib.sha256(validated_media).hexdigest() != claim.digest):
        raise ReviewDenied("CAPTURE_PREVIEW_BYTES_MISMATCH")

    # Explicit LAB-only schema, created before any review DB transaction.
    with Session(app.state.lab_sqlcipher_engine) as setup:
        _isolation(setup)
    metadata.create_all(bind=app.state.lab_sqlcipher_engine, checkfirst=True)

    async def _review_db():
        with Session(app.state.lab_sqlcipher_engine) as session:
            yield session

    def _ensure_request(request: Request, user) -> None:
        if (os.getenv("DC06_PHASE2_REVIEW_LAB") != "1"
                or os.getenv("ENVIRONMENT") != "test"
                or os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
                or request.client is None
                or request.client.host not in ("127.0.0.1", "::1")
                or int(user.id) != int(claim.staff)):
            raise HTTPException(403, "ISOLATED_REVIEW_NOT_AUTHORIZED")

    @app.get("/isolated/lot06-phase2/review/{capture}")
    async def review(capture: str, request: Request,
                     current_user: models.User = Depends(auth.get_current_user),
                     db: Session = Depends(_review_db)):
        _ensure_request(request, current_user)
        if capture != claim.capture:
            raise HTTPException(404, "CAPTURE_NOT_FOUND")
        try:
            return begin(db, claim=claim, staff_id=current_user.id)
        except (ReviewDenied, gate.BridgeRejected):
            raise HTTPException(409, "REVIEW_UNAVAILABLE") from None

    @app.post("/isolated/lot06-phase2/review/{capture}/confirm")
    async def approve(capture: str, data: ReviewInput, request: Request,
                      current_user: models.User = Depends(auth.get_current_user),
                      db: Session = Depends(_review_db)):
        _ensure_request(request, current_user)
        if capture != claim.capture:
            raise HTTPException(404, "CAPTURE_NOT_FOUND")
        try:
            return confirm(db, claim=claim, staff_id=current_user.id, data=data)
        except (ReviewDenied, gate.BridgeRejected):
            raise HTTPException(409, "REVIEW_REJECTED") from None

    @app.get("/isolated/lot06-phase2/preview/{capture}")
    async def preview(capture: str, request: Request,
                      current_user: models.User = Depends(auth.get_current_user),
                      db: Session = Depends(_review_db)):
        _ensure_request(request, current_user)
        if capture != claim.capture:
            raise HTTPException(404, "CAPTURE_NOT_FOUND")
        try:
            _isolation(db)
            _authority(db, claim=claim, staff_id=current_user.id)
            _guarded_capture(db, claim)
            unassigned_manifest.check_pending(db, claim)
            # A valid login alone cannot fetch a capture. The same staff must
            # possess the currently-active, one-use review challenge.
            active = db.execute(select(reviews).where(
                reviews.c.tenant == claim.tenant,
                reviews.c.device == claim.device,
                reviews.c.capture == claim.capture,
            )).mappings().one_or_none()
            challenge_header = request.headers.get("x-dc-review-challenge", "")
            if (active is None or active["consumed"] != 0
                    or active["expires_at"] <= int(time.time())
                    or active["staff"] != current_user.id
                    or active["station"] != claim.station
                    or active["patient"] != claim.patient
                    or active["digest"] != claim.digest
                    or active["byte_size"] != claim.byte_size
                    or not 20 <= len(challenge_header) <= 128
                    or not hmac.compare_digest(
                        hashlib.sha256(challenge_header.encode("utf-8")).hexdigest(),
                        active["challenge_sha"],
                    )):
                raise ReviewDenied("PREVIEW_REVIEW_CHALLENGE_DENIED")
            # Preview never changes the review or creates a ClinicalAsset.
            if hashlib.sha256(validated_media).hexdigest() != claim.digest:
                raise ReviewDenied("PREVIEW_MEDIA_TAMPERED")
        except (ReviewDenied, gate.BridgeRejected):
            raise HTTPException(409, "PREVIEW_UNAVAILABLE") from None
        return Response(
            validated_media, media_type="image/png",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
