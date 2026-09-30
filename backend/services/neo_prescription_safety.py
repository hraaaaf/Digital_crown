"""Neo-Ordonnance N3 structural safety core.

This module is deliberately conservative: it aggregates verified medication identity
and structured patient facts, but does not invent interaction/contraindication knowledge.
A missing evidence domain is a blocker, never a silent PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

from backend.services import medication_dict


@dataclass(frozen=True)
class NeoSafetyResult:
    status: str
    presentation_id: str
    blockers: Tuple[str, ...]
    warnings: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    medication_identity_verified: bool
    current_marketing_status_verified: bool
    interaction_evaluation_complete: bool
    contraindication_evaluation_complete: bool


def _value(context: Any, name: str, default: Any = None) -> Any:
    if isinstance(context, Mapping):
        return context.get(name, default)
    return getattr(context, name, default)


def evaluate_neo_prescription_safety(
    *,
    presentation_id: str,
    patient_context: Any,
    age_years: Optional[int],
) -> NeoSafetyResult:
    blockers: list[str] = []
    warnings: list[str] = []
    presentation = medication_dict.get_unified_presentation(presentation_id)

    if presentation is None:
        return NeoSafetyResult(
            status="BLOCKED",
            presentation_id=presentation_id,
            blockers=("MEDICATION_IDENTITY_UNRESOLVED",),
            warnings=(),
            source_ids=(),
            medication_identity_verified=False,
            current_marketing_status_verified=False,
            interaction_evaluation_complete=False,
            contraindication_evaluation_complete=False,
        )

    source = presentation.get("source") or {}
    source_id = str(source.get("id") or "UNKNOWN_SOURCE")
    current_verified = bool(source.get("current_marketing_status_verified"))
    if not current_verified:
        blockers.append("CURRENT_MARKETING_STATUS_NOT_VERIFIED")

    if age_years is None:
        blockers.append("AGE_UNKNOWN")
    if _value(patient_context, "medication_allergy_status", "UNKNOWN") == "UNKNOWN":
        blockers.append("MEDICATION_ALLERGY_STATUS_UNKNOWN")
    if _value(patient_context, "penicillin_allergy_status", "UNKNOWN") == "UNKNOWN":
        blockers.append("PENICILLIN_ALLERGY_STATUS_UNKNOWN")
    if _value(patient_context, "renal_context_status", "UNKNOWN") == "UNKNOWN":
        blockers.append("RENAL_CONTEXT_UNKNOWN")
    if _value(patient_context, "hepatic_context_status", "UNKNOWN") == "UNKNOWN":
        blockers.append("HEPATIC_CONTEXT_UNKNOWN")
    if _value(patient_context, "pregnancy_status", "UNKNOWN") == "UNKNOWN":
        blockers.append("PREGNANCY_STATUS_UNKNOWN")
    if _value(patient_context, "breastfeeding_status", "UNKNOWN") == "UNKNOWN":
        blockers.append("BREASTFEEDING_STATUS_UNKNOWN")
    if _value(patient_context, "current_medications_status", "UNKNOWN") == "UNKNOWN":
        blockers.append("CURRENT_MEDICATIONS_STATUS_UNKNOWN")

    # N3 establishes the Neo safety boundary. It does not replace the legacy runtime yet.
    # Therapeutic knowledge is not yet
    # complete enough to assert absence of interactions or contraindications.
    blockers.extend((
        "INTERACTION_KNOWLEDGE_NOT_COMPLETE",
        "CONTRAINDICATION_KNOWLEDGE_NOT_COMPLETE",
    ))

    if _value(patient_context, "medication_allergy_status") == "PRESENT":
        warnings.append("MEDICATION_ALLERGY_REPORTED_REQUIRES_RECONCILIATION")
    if _value(patient_context, "renal_context_status") == "IMPAIRMENT_REPORTED":
        warnings.append("RENAL_IMPAIRMENT_REPORTED_REQUIRES_REVIEW")
    if _value(patient_context, "hepatic_context_status") == "IMPAIRMENT_REPORTED":
        warnings.append("HEPATIC_IMPAIRMENT_REPORTED_REQUIRES_REVIEW")
    if _value(patient_context, "pregnancy_status") == "YES":
        warnings.append("PREGNANCY_REPORTED_REQUIRES_REVIEW")
    if _value(patient_context, "breastfeeding_status") == "YES":
        warnings.append("BREASTFEEDING_REPORTED_REQUIRES_REVIEW")

    return NeoSafetyResult(
        status="BLOCKED" if blockers else "READY",
        presentation_id=presentation_id,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        source_ids=(source_id,),
        medication_identity_verified=True,
        current_marketing_status_verified=current_verified,
        interaction_evaluation_complete=False,
        contraindication_evaluation_complete=False,
    )
