from dataclasses import dataclass
from typing import Literal, Optional, Tuple


RuleStatus = Literal["BLOCKED", "READY"]
PenicillinAllergyStatus = Literal["UNKNOWN", "NONE_KNOWN", "PRESENT"]
CardiacRiskCategory = Literal[
    "UNKNOWN",
    "NONE_REPORTED",
    "OTHER_CARDIAC_CONDITION",
    "PROSTHETIC_CARDIAC_VALVE",
    "PROSTHETIC_MATERIAL_FOR_CARDIAC_VALVE_REPAIR",
    "PREVIOUS_INFECTIVE_ENDOCARDITIS",
    "UNREPAIRED_CYANOTIC_CONGENITAL_HEART_DISEASE",
    "REPAIRED_CHD_WITH_RESIDUAL_SHUNT_OR_VALVULAR_REGURGITATION_AT_PROSTHETIC_PATCH_OR_DEVICE",
    "CARDIAC_TRANSPLANT_WITH_VALVE_REGURGITATION_DUE_STRUCTURALLY_ABNORMAL_VALVE",
]


QUALIFYING_CARDIAC_CATEGORIES = {
    "PROSTHETIC_CARDIAC_VALVE",
    "PROSTHETIC_MATERIAL_FOR_CARDIAC_VALVE_REPAIR",
    "PREVIOUS_INFECTIVE_ENDOCARDITIS",
    "UNREPAIRED_CYANOTIC_CONGENITAL_HEART_DISEASE",
    "REPAIRED_CHD_WITH_RESIDUAL_SHUNT_OR_VALVULAR_REGURGITATION_AT_PROSTHETIC_PATCH_OR_DEVICE",
    "CARDIAC_TRANSPLANT_WITH_VALVE_REGURGITATION_DUE_STRUCTURALLY_ABNORMAL_VALVE",
}

SOURCE_AHA_2021 = "AHA_VGS_IE_2021"
SOURCE_ADA_IE_PROPHYLAXIS = "ADA_IE_PROPHYLAXIS"


@dataclass(frozen=True)
class IEProphylaxisAdultOralAmoxicillinInput:
    """Explicit inputs for the first Prescription Intelligence C2 clinical rule.

    The rule is intentionally narrow and fail-closed. It never infers cardiac risk,
    dental-procedure eligibility, allergy state, route feasibility, current antibiotic
    exposure, patient age, or medication identity from free text.
    """

    age_years: Optional[int]
    cardiac_risk_category: CardiacRiskCategory
    dental_procedure_qualifies: Optional[bool]
    penicillin_allergy_status: PenicillinAllergyStatus
    generic_medication_allergy_present: bool
    oral_route_possible: Optional[bool]
    currently_taking_penicillin_or_amoxicillin: Optional[bool]
    selected_active_ingredient_code: Optional[str]
    selected_presentation_verified: bool


@dataclass(frozen=True)
class ClinicalRuleResult:
    status: RuleStatus
    rule_id: str
    rule_version: str
    blockers: Tuple[str, ...]
    active_ingredient_code: Optional[str] = None
    total_dose_mg: Optional[int] = None
    timing_min_minutes_before: Optional[int] = None
    timing_max_minutes_before: Optional[int] = None
    single_dose: Optional[bool] = None
    source_ids: Tuple[str, ...] = ()


RULE_ID = "IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN"
RULE_VERSION = "2026-09-15.v3"


def evaluate_ie_prophylaxis_adult_oral_amoxicillin(
    data: IEProphylaxisAdultOralAmoxicillinInput,
) -> ClinicalRuleResult:
    blockers = []

    if data.age_years is None:
        blockers.append("AGE_UNKNOWN")
    elif data.age_years < 18:
        blockers.append("ADULT_RULE_ONLY")

    if data.cardiac_risk_category == "UNKNOWN":
        blockers.append("CARDIAC_RISK_UNKNOWN")
    elif data.cardiac_risk_category not in QUALIFYING_CARDIAC_CATEGORIES:
        blockers.append("CARDIAC_RISK_NOT_QUALIFYING")

    if data.dental_procedure_qualifies is None:
        blockers.append("DENTAL_PROCEDURE_ELIGIBILITY_UNKNOWN")
    elif data.dental_procedure_qualifies is not True:
        blockers.append("DENTAL_PROCEDURE_NOT_QUALIFYING")

    if data.generic_medication_allergy_present:
        blockers.append("GENERIC_MEDICATION_ALLERGY_REQUIRES_RECONCILIATION")

    if data.penicillin_allergy_status == "UNKNOWN":
        blockers.append("PENICILLIN_ALLERGY_UNKNOWN")
    elif data.penicillin_allergy_status != "NONE_KNOWN":
        blockers.append("PENICILLIN_ALLERGY_PRESENT")

    if data.oral_route_possible is None:
        blockers.append("ORAL_ROUTE_UNKNOWN")
    elif data.oral_route_possible is not True:
        blockers.append("ORAL_ROUTE_NOT_POSSIBLE")

    if data.currently_taking_penicillin_or_amoxicillin is None:
        blockers.append("CURRENT_ANTIBIOTIC_EXPOSURE_UNKNOWN")
    elif data.currently_taking_penicillin_or_amoxicillin is True:
        blockers.append("CURRENT_PENICILLIN_OR_AMOXICILLIN")

    if not data.selected_presentation_verified:
        blockers.append("PRESENTATION_NOT_VERIFIED")

    if data.selected_active_ingredient_code != "AMOXICILLIN":
        blockers.append("ACTIVE_INGREDIENT_NOT_AMOXICILLIN")

    if blockers:
        return ClinicalRuleResult(
            status="BLOCKED",
            rule_id=RULE_ID,
            rule_version=RULE_VERSION,
            blockers=tuple(blockers),
            source_ids=(SOURCE_AHA_2021, SOURCE_ADA_IE_PROPHYLAXIS),
        )

    return ClinicalRuleResult(
        status="READY",
        rule_id=RULE_ID,
        rule_version=RULE_VERSION,
        blockers=(),
        active_ingredient_code="AMOXICILLIN",
        total_dose_mg=2000,
        timing_min_minutes_before=30,
        timing_max_minutes_before=60,
        single_dose=True,
        source_ids=(SOURCE_AHA_2021, SOURCE_ADA_IE_PROPHYLAXIS),
    )
