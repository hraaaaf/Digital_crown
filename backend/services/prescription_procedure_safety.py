import math
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

from backend.services.prescription_clinical_rules import (
    IEProphylaxisAdultOralAmoxicillinInput,
    evaluate_ie_prophylaxis_adult_oral_amoxicillin,
)


ProcedureBleedingRisk = Literal[
    "UNKNOWN",
    "UNLIKELY_TO_CAUSE_BLEEDING",
    "LOW_POSTOP_BLEEDING_RISK",
    "HIGHER_POSTOP_BLEEDING_RISK",
]
AntithromboticStatus = Literal["UNKNOWN", "NONE_REPORTED", "PRESENT"]
AntithromboticClass = Literal["VKA", "DOAC", "ANTIPLATELET", "LMWH", "OTHER"]
CombinationStatus = Literal["UNKNOWN", "NO", "YES"]
LMWHDoseClass = Literal["UNKNOWN", "PROPHYLACTIC", "TREATMENT"]
ProcedureSafetyStatus = Literal[
    "READY",
    "CONTEXT_REQUIRED",
    "CLINICAL_REVIEW_REQUIRED",
    "PRESCRIBER_REVIEW_REQUIRED",
]


SOURCE_SDCEP_ANTITHROMBOTICS_2022 = "SDCEP_ANTITHROMBOTICS_2022"
SOURCE_AHA_2021 = "AHA_VGS_IE_2021"
SOURCE_ADA_IE_PROPHYLAXIS = "ADA_IE_PROPHYLAXIS"


@dataclass(frozen=True)
class AntithromboticProcedureSafetyInput:
    procedure_bleeding_risk: ProcedureBleedingRisk
    antithrombotic_status: AntithromboticStatus
    antithrombotic_classes: Tuple[AntithromboticClass, ...] = ()
    combination_therapy: CombinationStatus = "UNKNOWN"
    warfarin_inr: Optional[float] = None
    warfarin_inr_current: Optional[bool] = None
    lmwh_dose_class: LMWHDoseClass = "UNKNOWN"


@dataclass(frozen=True)
class ProcedureSafetyGateResult:
    status: ProcedureSafetyStatus
    alert_key: Optional[str]
    internal_codes: Tuple[str, ...]
    source_ids: Tuple[str, ...]


@dataclass(frozen=True)
class ProcedureSafetyOrchestration:
    status: ProcedureSafetyStatus
    alert_key: Optional[str]
    bleeding: ProcedureSafetyGateResult
    ie: Optional[ProcedureSafetyGateResult]


_SEVERITY = {
    "READY": 0,
    "CONTEXT_REQUIRED": 1,
    "CLINICAL_REVIEW_REQUIRED": 2,
    "PRESCRIBER_REVIEW_REQUIRED": 3,
}


def _result(
    status: ProcedureSafetyStatus,
    *codes: str,
    alert_key: Optional[str] = None,
    sources: Tuple[str, ...] = (SOURCE_SDCEP_ANTITHROMBOTICS_2022,),
) -> ProcedureSafetyGateResult:
    return ProcedureSafetyGateResult(
        status=status,
        alert_key=alert_key,
        internal_codes=tuple(codes),
        source_ids=sources,
    )


def evaluate_antithrombotic_procedure_safety(
    data: AntithromboticProcedureSafetyInput,
) -> ProcedureSafetyGateResult:
    """Bounded backoffice-only gate.

    This gate never recommends interruption, dose omission, or timing changes.
    It only returns an internal review state for the practitioner workflow.
    """

    invasive = data.procedure_bleeding_risk in {
        "LOW_POSTOP_BLEEDING_RISK",
        "HIGHER_POSTOP_BLEEDING_RISK",
    }

    if data.procedure_bleeding_risk == "UNKNOWN":
        return _result(
            "CONTEXT_REQUIRED",
            "PROCEDURE_BLEEDING_RISK_UNKNOWN",
            alert_key="CONTEXT_REQUIRED",
        )

    if not invasive:
        return _result("READY")

    if data.antithrombotic_status == "UNKNOWN":
        return _result(
            "CONTEXT_REQUIRED",
            "ANTITHROMBOTIC_STATUS_UNKNOWN",
            alert_key="CONTEXT_REQUIRED",
        )

    classes = tuple(dict.fromkeys(data.antithrombotic_classes))

    if data.antithrombotic_status == "NONE_REPORTED":
        if classes:
            return _result(
                "CONTEXT_REQUIRED",
                "ANTITHROMBOTIC_CONTEXT_INCONSISTENT",
                alert_key="CONTEXT_REQUIRED",
            )
        return _result("READY")

    if not classes:
        return _result(
            "CONTEXT_REQUIRED",
            "ANTITHROMBOTIC_CLASS_UNKNOWN",
            alert_key="CONTEXT_REQUIRED",
        )

    if data.combination_therapy == "UNKNOWN":
        return _result(
            "CONTEXT_REQUIRED",
            "ANTITHROMBOTIC_COMBINATION_STATUS_UNKNOWN",
            alert_key="CONTEXT_REQUIRED",
        )

    if data.combination_therapy == "YES" or len(classes) > 1:
        return _result(
            "PRESCRIBER_REVIEW_REQUIRED",
            "ANTITHROMBOTIC_COMBINATION",
            alert_key="PRESCRIBER_REVIEW_RECOMMENDED",
        )

    drug_class = classes[0]

    if drug_class == "VKA":
        if (
            data.warfarin_inr is None
            or not math.isfinite(data.warfarin_inr)
            or data.warfarin_inr <= 0
            or data.warfarin_inr_current is not True
        ):
            return _result(
                "CONTEXT_REQUIRED",
                "VKA_INR_CURRENT_VALUE_REQUIRED",
                alert_key="CONTEXT_REQUIRED",
            )
        if data.warfarin_inr >= 4:
            return _result(
                "PRESCRIBER_REVIEW_REQUIRED",
                "VKA_INR_AT_OR_ABOVE_4",
                alert_key="PRESCRIBER_REVIEW_RECOMMENDED",
            )
        return _result("READY")

    if drug_class == "LMWH":
        if data.lmwh_dose_class in {"UNKNOWN", "TREATMENT"}:
            return _result(
                "PRESCRIBER_REVIEW_REQUIRED",
                "LMWH_DOSE_REQUIRES_PRESCRIBER_REVIEW",
                alert_key="PRESCRIBER_REVIEW_RECOMMENDED",
            )
        return _result("READY")

    if drug_class == "DOAC":
        if data.procedure_bleeding_risk == "HIGHER_POSTOP_BLEEDING_RISK":
            return _result(
                "CLINICAL_REVIEW_REQUIRED",
                "DOAC_HIGHER_POSTOP_BLEEDING_RISK",
                alert_key="CLINICAL_REVIEW_RECOMMENDED",
            )
        return _result("READY")

    if drug_class == "ANTIPLATELET":
        return _result("READY")

    return _result(
        "CLINICAL_REVIEW_REQUIRED",
        "ANTITHROMBOTIC_CLASS_REQUIRES_REVIEW",
        alert_key="CLINICAL_REVIEW_RECOMMENDED",
    )


_IE_UNKNOWN_CODES = {
    "AGE_UNKNOWN",
    "CARDIAC_RISK_UNKNOWN",
    "DENTAL_PROCEDURE_ELIGIBILITY_UNKNOWN",
    "PENICILLIN_ALLERGY_UNKNOWN",
    "ORAL_ROUTE_UNKNOWN",
    "CURRENT_ANTIBIOTIC_EXPOSURE_UNKNOWN",
    "PRESENTATION_NOT_VERIFIED",
}
_IE_NONQUALIFYING_CODES = {
    "CARDIAC_RISK_NOT_QUALIFYING",
    "DENTAL_PROCEDURE_NOT_QUALIFYING",
}


def evaluate_ie_prophylaxis_background(
    data: IEProphylaxisAdultOralAmoxicillinInput,
) -> ProcedureSafetyGateResult:
    """Reuse the existing IE rule and translate it to background-only workflow states."""

    rule = evaluate_ie_prophylaxis_adult_oral_amoxicillin(data)
    sources = tuple(rule.source_ids) or (SOURCE_AHA_2021, SOURCE_ADA_IE_PROPHYLAXIS)

    if rule.status == "READY":
        return _result("READY", sources=sources)

    blockers = set(rule.blockers)
    if blockers & _IE_NONQUALIFYING_CODES:
        return _result("READY", *rule.blockers, sources=sources)

    if blockers & _IE_UNKNOWN_CODES:
        return _result(
            "CONTEXT_REQUIRED",
            *rule.blockers,
            alert_key="CONTEXT_REQUIRED",
            sources=sources,
        )

    return _result(
        "CLINICAL_REVIEW_REQUIRED",
        *rule.blockers,
        alert_key="CLINICAL_REVIEW_RECOMMENDED",
        sources=sources,
    )


def orchestrate_procedure_safety(
    bleeding_input: AntithromboticProcedureSafetyInput,
    ie_input: Optional[IEProphylaxisAdultOralAmoxicillinInput] = None,
) -> ProcedureSafetyOrchestration:
    bleeding = evaluate_antithrombotic_procedure_safety(bleeding_input)
    ie = evaluate_ie_prophylaxis_background(ie_input) if ie_input is not None else None

    candidates = [bleeding] + ([ie] if ie is not None else [])
    dominant = max(candidates, key=lambda item: _SEVERITY[item.status])

    return ProcedureSafetyOrchestration(
        status=dominant.status,
        alert_key=dominant.alert_key,
        bleeding=bleeding,
        ie=ie,
    )
