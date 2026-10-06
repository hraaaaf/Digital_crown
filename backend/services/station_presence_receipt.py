from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings

STAFF_PRESENCE_ACTION = "APPOINTMENT_PRESENCE_CONFIRMED_STAFF"
QUEUE_CORE_PRESENCE_ACTION = "QUEUE_CORE_PRESENCE_CONFIRMED"
RECEIPT_VERSION = "v1.5-04.2"
UNICODE_FONT_NAME = "StationReceiptUnicode"
PRESENCE_PROOF_DETAILS_PREFIX = "presence_start="



def _unicode_font_candidates() -> tuple[Path, ...]:
    backend_dir = Path(__file__).resolve().parents[1]
    windir = os.getenv("WINDIR") or os.getenv("SystemRoot")
    candidates = [
        backend_dir / "static" / "assets" / "fonts" / "Amiri-Regular.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansArabic-Regular.ttf"),
    ]
    if windir:
        candidates.extend((Path(windir) / "Fonts" / "tahoma.ttf", Path(windir) / "Fonts" / "arial.ttf"))
    candidates.extend(
        (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
        )
    )
    return tuple(candidates)


def _unicode_font() -> str:
    try:
        pdfmetrics.getFont(UNICODE_FONT_NAME)
        return UNICODE_FONT_NAME
    except KeyError:
        pass
    for path in _unicode_font_candidates():
        if not path.is_file():
            continue
        try:
            pdfmetrics.registerFont(TTFont(UNICODE_FONT_NAME, str(path)))
            return UNICODE_FONT_NAME
        except Exception:
            continue
    return "Helvetica"


def _pdf_text(value: str) -> str:
    text = str(value or "")
    if any("\u0600" <= ch <= "\u06ff" for ch in text):
        return get_display(arabic_reshaper.reshape(text))
    return text


def presence_proof_details(appointment_start: datetime) -> str:
    return f"{PRESENCE_PROOF_DETAILS_PREFIX}{appointment_start.isoformat(timespec='seconds')}"


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

    expected_details = presence_proof_details(appointment.datetime_start)
    event = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.employer_id == employer_id,
            models.AuditLog.resource_type == "Appointment",
            models.AuditLog.resource_id == str(appointment.id),
            models.AuditLog.action.in_((STAFF_PRESENCE_ACTION, QUEUE_CORE_PRESENCE_ACTION)),
            models.AuditLog.details == expected_details,
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
    value_font = _unicode_font()

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
        pdf.setFont(value_font, 10)
        pdf.drawString(70 * mm, y, _pdf_text(str(value)))
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
