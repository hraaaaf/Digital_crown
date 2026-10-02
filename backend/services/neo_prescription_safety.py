"""Neo-Ordonnance N3 structural safety core.

This module is deliberately conservative: it aggregates verified medication identity
and structured patient facts, but does not invent interaction/contraindication knowledge.
A missing evidence domain is a blocker, never a silent PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

from backend.services import medication_dict
from backend.services.neo_medication_evidence import evaluate_bounded_evidence


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
    evidence_version: Optional[str] = None
    evidence_findings: Tuple[str, ...] = ()


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
    elif not isinstance(age_years, int) or isinstance(age_years, bool) or age_years < 0 or age_years > 130:
        blockers.append("AGE_INVALID")
    status_contracts = (
        ("medication_allergy_status", {"UNKNOWN", "NONE_KNOWN", "PRESENT"}, "MEDICATION_ALLERGY_STATUS"),
        ("penicillin_allergy_status", {"UNKNOWN", "NONE_KNOWN", "PRESENT"}, "PENICILLIN_ALLERGY_STATUS"),
        ("renal_context_status", {"UNKNOWN", "NO_KNOWN_IMPAIRMENT", "IMPAIRMENT_REPORTED"}, "RENAL_CONTEXT"),
        ("hepatic_context_status", {"UNKNOWN", "NO_KNOWN_IMPAIRMENT", "IMPAIRMENT_REPORTED"}, "HEPATIC_CONTEXT"),
        ("pregnancy_status", {"UNKNOWN", "NO", "YES"}, "PREGNANCY_STATUS"),
        ("breastfeeding_status", {"UNKNOWN", "NO", "YES"}, "BREASTFEEDING_STATUS"),
        ("current_medications_status", {"UNKNOWN", "NONE_REPORTED", "PRESENT"}, "CURRENT_MEDICATIONS_STATUS"),
    )
    for field, allowed, blocker_prefix in status_contracts:
        value = _value(patient_context, field, "UNKNOWN")
        if value == "UNKNOWN": blockers.append(f"{blocker_prefix}_UNKNOWN")
        elif not isinstance(value, str) or value not in allowed: blockers.append(f"{blocker_prefix}_INVALID")

    def _valid_string_list(value: Any) -> bool:
        return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)

    current_status = _value(patient_context, "current_medications_status", "UNKNOWN")
    current_meds = _value(patient_context, "current_medications")
    if current_status == "PRESENT" and not _valid_string_list(current_meds):
        blockers.append("CURRENT_MEDICATIONS_PRESENT_WITHOUT_VALID_LIST")
    if current_status != "PRESENT" and current_meds not in (None, []):
        blockers.append("CURRENT_MEDICATIONS_LIST_STATUS_MISMATCH")
    allergy_status = _value(patient_context, "medication_allergy_status", "UNKNOWN")
    allergies = _value(patient_context, "medication_allergies")
    if allergy_status == "PRESENT" and not _valid_string_list(allergies):
        blockers.append("MEDICATION_ALLERGY_PRESENT_WITHOUT_VALID_LIST")
    if allergy_status != "PRESENT" and allergies not in (None, []):
        blockers.append("MEDICATION_ALLERGY_LIST_STATUS_MISMATCH")

    evidence = evaluate_bounded_evidence(
        dci=str(presentation.get("dci") or ""),
        current_medications=current_meds or [],
        pregnancy_status=str(_value(patient_context, "pregnancy_status", "UNKNOWN")),
        renal_status=str(_value(patient_context, "renal_context_status", "UNKNOWN")),
        hepatic_status=str(_value(patient_context, "hepatic_context_status", "UNKNOWN")),
        medication_allergies=allergies or [],
        penicillin_allergy_status=str(_value(patient_context, "penicillin_allergy_status", "UNKNOWN")),
    )
    if not evidence.interaction_complete_for_inputs:
        blockers.append("INTERACTION_KNOWLEDGE_NOT_COMPLETE")
    if not evidence.contraindication_complete_for_inputs:
        blockers.append("CONTRAINDICATION_KNOWLEDGE_NOT_COMPLETE")
    for finding in evidence.findings:
        if finding.severity in {"CONTRAINDICATED", "HIGH_RISK", "AVOID", "BLOCK"}:
            blockers.append(finding.code)
        else:
            warnings.append(finding.code)
    source_ids_extra = evidence.source_ids

    if _value(patient_context, "medication_allergy_status") == "PRESENT":
        warnings.append("MEDICATION_ALLERGY_REPORTED_REQUIRES_RECONCILIATION")
    if _value(patient_context, "penicillin_allergy_status") == "PRESENT":
        warnings.append("PENICILLIN_ALLERGY_REPORTED_REQUIRES_RECONCILIATION")
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
        source_ids=tuple(dict.fromkeys((source_id, *source_ids_extra))),
        medication_identity_verified=True,
        current_marketing_status_verified=current_verified,
        interaction_evaluation_complete=evidence.interaction_complete_for_inputs,
        contraindication_evaluation_complete=evidence.contraindication_complete_for_inputs,
        evidence_version=evidence.evidence_version,
        evidence_findings=tuple(f.code for f in evidence.findings),
    )
