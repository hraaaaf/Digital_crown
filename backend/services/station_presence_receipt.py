from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings

STAFF_PRESENCE_ACTION = "APPOINTMENT_PRESENCE_CONFIRMED_STAFF"
QUEUE_CORE_PRESENCE_ACTION = "QUEUE_CORE_PRESENCE_CONFIRMED"
RECEIPT_VERSION = "v1.5-04.2"


@dataclass(frozen=True)
class PresenceProof:
    source: str
    audit_id: int
    timestamp: datetime


def reliable_presence_proof(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    appointment: models.Appointment,
) -> PresenceProof | None:
    if (
        appointment.employer_id != employer_id
        or appointment.patient_id != patient_id
        or appointment.deleted_at is not None
        or appointment.status != models.AppointmentStatus.EN_SALLE_ATTENTE
    ):
        return None

    event = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.employer_id == employer_id,
            models.AuditLog.resource_type == "Appointment",
            models.AuditLog.resource_id == str(appointment.id),
            models.AuditLog.action.in_((STAFF_PRESENCE_ACTION, QUEUE_CORE_PRESENCE_ACTION)),
        )
        .order_by(models.AuditLog.timestamp.desc(), models.AuditLog.id.desc())
        .first()
    )
    if event is None:
        return None

    source = "staff" if event.action == STAFF_PRESENCE_ACTION else "queue_core"
    return PresenceProof(source=source, audit_id=int(event.id), timestamp=event.timestamp)


def _claim(
    *,
    employer_id: int,
    patient_id: int,
    appointment_id: int,
    appointment_start: datetime,
    proof: PresenceProof,
) -> str:
    return "\n".join(
        (
            RECEIPT_VERSION,
            str(int(employer_id)),
            str(int(patient_id)),
            str(int(appointment_id)),
            appointment_start.isoformat(timespec="seconds"),
            proof.source,
            str(int(proof.audit_id)),
            proof.timestamp.isoformat(timespec="seconds"),
        )
    )


def presence_receipt_verification_code(
    *,
    employer_id: int,
    patient_id: int,
    appointment_id: int,
    appointment_start: datetime,
    proof: PresenceProof,
    secret_key: str | None = None,
) -> str:
    key = (secret_key or settings.SECRET_KEY).encode("utf-8")
    digest = hmac.new(
        key,
        _claim(
            employer_id=employer_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            appointment_start=appointment_start,
            proof=proof,
        ).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:24].upper()


def verify_presence_receipt_code(
    code: str,
    *,
    employer_id: int,
    patient_id: int,
    appointment_id: int,
    appointment_start: datetime,
    proof: PresenceProof,
    secret_key: str | None = None,
) -> bool:
    expected = presence_receipt_verification_code(
        employer_id=employer_id,
        patient_id=patient_id,
        appointment_id=appointment_id,
        appointment_start=appointment_start,
        proof=proof,
        secret_key=secret_key,
    )
    return hmac.compare_digest(code, expected)


def render_presence_receipt_pdf(
    *,
    cabinet_name: str,
    practitioner_name: str,
    patient_name: str,
    appointment_start: datetime,
    verification_code: str,
) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, invariant=1, pageCompression=0)
    pdf.setTitle("Justificatif de presence")
    pdf.setAuthor("Digital Crown")
    pdf.setSubject("Justificatif de presence patient")
    width, height = A4

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, height - 32 * mm, "JUSTIFICATIF DE PRESENCE")

    pdf.setFont("Helvetica", 11)
    y = height - 52 * mm
    rows = (
        ("Cabinet", cabinet_name or "Cabinet dentaire"),
        ("Praticien", practitioner_name or ""),
        ("Patient", patient_name),
        ("Date", appointment_start.strftime("%d/%m/%Y")),
        ("Heure du rendez-vous", appointment_start.strftime("%H:%M")),
        ("Reference de verification", verification_code),
    )
    for label, value in rows:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(28 * mm, y, f"{label} :")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(70 * mm, y, str(value))
        y -= 8 * mm

    y -= 4 * mm
    pdf.setFont("Helvetica", 10)
    pdf.drawString(28 * mm, y, "Ce document atteste une presence confirmee au cabinet.")
    y -= 7 * mm
    pdf.drawString(28 * mm, y, "Emission automatisee par Digital Crown a partir d'une preuve de presence autorisee.")

    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(width - 20 * mm, 16 * mm, f"Digital Crown {RECEIPT_VERSION}")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
