"""V1.5-06B read-only acquisition identity preflight.

NEVER creates ClinicalAsset records or issues an upload token.
No patient identity is inferred from filenames or nearest appointment.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend import models


class PreflightRejected(ValueError):
    """Fail-closed contract violation with a non-PHI reason code."""

    def __init__(self, reason: str, status_code: int = 409):
        self.reason = reason
        self.status_code = status_code
        super().__init__(reason)


@dataclass(frozen=True)
class PreflightDecision:
    status: str
    reason: str
    patient_id: int | None = None
    appointment_id: int | None = None


def resolve_acquisition_preflight(
    db: Session,
    *,
    employer_id: int,
    patient_id: int | None = None,
    appointment_id: int | None = None,
) -> PreflightDecision:
    """Resolve only the *candidate* in one cabinet; never authorize upload.

    A trusted and bound capture session does not yet exist in LOT06-B.
    Consequently even a unique RDV requires a human to approve a patient.
    The caller must enforce workstation+staff authorization beforehand.
    """
    employer_id = int(employer_id)
    if patient_id is None and appointment_id is None:
        return PreflightDecision("AWAITING_HUMAN_LINK", "NO_EXPLICIT_REFERENCE")
    appointment = None
    if appointment_id is not None:
        appointment = (
            db.query(models.Appointment)
            .filter(
                models.Appointment.id == appointment_id,
                models.Appointment.employer_id == employer_id,
                models.Appointment.deleted_at.is_(None),
            )
            .first()
        )
        if appointment is None:
            raise PreflightRejected("APPOINTMENT_NOT_FOUND", 404)
        if appointment.patient_id is None:
            # A quick RDV with only a patient name is not an identity.
            if patient_id is not None:
                raise PreflightRejected("PATIENT_APPOINTMENT_CONFLICT")
            return PreflightDecision(
                "AWAITING_HUMAN_LINK", "APPOINTMENT_UNLINKED",
                appointment_id=appointment_id,
            )
        if patient_id is not None and int(patient_id) != int(appointment.patient_id):
            # Never silently override a contradictory patient hint.
            raise PreflightRejected("PATIENT_APPOINTMENT_CONFLICT")
        patient_id = int(appointment.patient_id)

    patient = (
        db.query(models.Patient)
        .filter(
            models.Patient.id == patient_id,
            models.Patient.employer_id == employer_id,
            models.Patient.deleted_at.is_(None),
        )
        .first()
    )
    if patient is None:
        raise PreflightRejected("PATIENT_NOT_FOUND", 404)
    return PreflightDecision(
        status="STAFF_CONFIRMATION_REQUIRED",
        reason="NO_SERVER_VERIFIED_CAPTURE_CONTEXT",
        patient_id=patient.id,
        appointment_id=appointment.id if appointment is not None else None,
    )
