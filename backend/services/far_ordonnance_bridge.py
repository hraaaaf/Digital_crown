"""Deterministic bridge from Digital Crown ordonnance data to FAR output.

The clinical ordonnance remains the single source of truth. This module only decides
whether a validated ordonnance must also produce a FAR-form prescription output and
copies explicit prescription fields without inference.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.schemas.documents import OrdonnanceData

FAR_ASSURANCE_CODES = frozenset({"FAR", "MUTUELLE_FAR"})


@dataclass(frozen=True)
class FarPrescriptionLine:
    name: str
    dosage: str
    form: str
    posology: str


@dataclass(frozen=True)
class FarOrdonnanceBridgePayload:
    patient_id: int
    source_ordonnance_document_id: int
    lines: tuple[FarPrescriptionLine, ...]


def patient_requires_far_ordonnance(*, assurance: str | None) -> bool:
    """Return True only for explicit FAR insurance codes stored on Patient.assurance."""
    return str(assurance or "").strip().upper() in FAR_ASSURANCE_CODES


def build_far_ordonnance_payload(
    *,
    patient_id: int,
    source_ordonnance_document_id: int,
    ordonnance: OrdonnanceData,
) -> FarOrdonnanceBridgePayload:
    """Copy explicit validated ordonnance fields; never infer medication data."""
    if patient_id <= 0:
        raise ValueError("FAR ordonnance bridge requires a persisted patient")
    if source_ordonnance_document_id <= 0:
        raise ValueError("FAR ordonnance bridge requires an archived source ordonnance")
    if not ordonnance.medications:
        raise ValueError("FAR ordonnance bridge requires at least one explicit medication")

    lines = tuple(
        FarPrescriptionLine(
            name=str(item.nom or "").strip(),
            dosage=str(item.dosage or "").strip(),
            form=str(item.forme or "").strip(),
            posology=str(item.posologie or "").strip(),
        )
        for item in ordonnance.medications
    )
    if any(not line.name for line in lines):
        raise ValueError("FAR ordonnance bridge cannot render an unnamed medication")

    return FarOrdonnanceBridgePayload(
        patient_id=patient_id,
        source_ordonnance_document_id=source_ordonnance_document_id,
        lines=lines,
    )
