"""Deterministic FAR ordonnance overlay for the cabinet-validated reference.

The Digital Crown ordonnance remains the clinical source of truth. This renderer only
copies explicit prescription text to logical Page 2 (physical page 2, left half).
Its typography and coordinates are intentionally independent from the application theme.
"""
from __future__ import annotations

import hashlib

import fitz

from backend.services.far_ordonnance_bridge import FarOrdonnanceBridgePayload
from backend.services.insurance_far_2021_1_profile import FAR_2021_1_DERIVED_TEMPLATE_SHA256

FAR_PRESCRIPTION_RENDERER_VERSION = "far-rx-c953d74f-v1"
FAR_PRESCRIPTION_PAGE_INDEX = 1
FAR_PRESCRIPTION_MAX_LINES = 6

# V4 cabinet-reviewed calibration, PDF points on the frozen A4-landscape reference.
_PATIENT_NAME_X = 292.0
_PATIENT_NAME_Y = 76.0
_PATIENT_NAME_FONT_SIZE = 9.6
_MEDICATION_X = 145.0
_POSOLOGY_X = 155.0
_FIRST_MEDICATION_Y = 108.0
_MEDICATION_STEP_Y = 40.0
_POSOLOGY_OFFSET_Y = 16.0
_MEDICATION_FONT_SIZE = 9.0
_POSOLOGY_FONT_SIZE = 8.2
_MAX_MEDICATION_CHARS = 52
_MAX_POSOLOGY_CHARS = 58


def _single_line(value: str, *, field: str, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise ValueError(f"FAR prescription {field} is required")
    if len(text) > max_chars:
        raise ValueError(f"FAR prescription {field} exceeds calibrated printable width")
    return text


def _medication_text(*, name: str, dosage: str, form: str) -> str:
    """Compose only explicit source fields using the cabinet-validated V4 hierarchy."""
    primary = " ".join(part for part in (str(name or "").strip(), str(dosage or "").strip()) if part)
    form_text = str(form or "").strip()
    return f"{primary} - {form_text}" if form_text else primary


def render_far_prescription_pdf(
    *,
    template_bytes: bytes,
    payload: FarOrdonnanceBridgePayload,
    patient_full_name: str,
) -> bytes:
    """Render explicit ordonnance fields on the exact locked FAR reference, fail closed."""
    template_hash = hashlib.sha256(template_bytes).hexdigest()
    if template_hash != FAR_2021_1_DERIVED_TEMPLATE_SHA256:
        raise ValueError("FAR prescription template SHA-256 mismatch")
    if payload.patient_id <= 0 or payload.source_ordonnance_document_id <= 0:
        raise ValueError("FAR prescription requires persisted patient and archived ordonnance")
    if not payload.lines:
        raise ValueError("FAR prescription requires at least one medication")
    if len(payload.lines) > FAR_PRESCRIPTION_MAX_LINES:
        raise ValueError("FAR prescription cannot represent all medication lines")

    patient_name = _single_line(
        patient_full_name,
        field="patient name",
        max_chars=38,
    )

    try:
        document = fitz.open(stream=template_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("Locked FAR template PDF is unreadable") from exc

    try:
        if document.page_count != 2:
            raise ValueError("Locked FAR template must contain exactly two physical pages")
        page = document[FAR_PRESCRIPTION_PAGE_INDEX]
        page.insert_text(
            (_PATIENT_NAME_X, _PATIENT_NAME_Y),
            patient_name,
            fontsize=_PATIENT_NAME_FONT_SIZE,
            fontname="helv",
        )

        for index, line in enumerate(payload.lines):
            medication = _single_line(
                _medication_text(name=line.name, dosage=line.dosage, form=line.form),
                field=f"medication[{index}]",
                max_chars=_MAX_MEDICATION_CHARS,
            )
            posology = _single_line(
                line.posology,
                field=f"posology[{index}]",
                max_chars=_MAX_POSOLOGY_CHARS,
            )
            medication_y = _FIRST_MEDICATION_Y + (index * _MEDICATION_STEP_Y)
            page.insert_text(
                (_MEDICATION_X, medication_y),
                medication,
                fontsize=_MEDICATION_FONT_SIZE,
                fontname="helv",
            )
            page.insert_text(
                (_POSOLOGY_X, medication_y + _POSOLOGY_OFFSET_Y),
                posology,
                fontsize=_POSOLOGY_FONT_SIZE,
                fontname="helv",
            )

        return document.tobytes(garbage=4, deflate=True)
    finally:
        document.close()
