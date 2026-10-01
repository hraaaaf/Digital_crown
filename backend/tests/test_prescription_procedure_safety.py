from backend.services.prescription_clinical_rules import IEProphylaxisAdultOralAmoxicillinInput
from backend.services.prescription_procedure_safety import (
    AntithromboticProcedureSafetyInput,
    evaluate_antithrombotic_procedure_safety,
    evaluate_ie_prophylaxis_background,
    orchestrate_procedure_safety,
)


def _bleeding(**overrides):
    data = dict(
        procedure_bleeding_risk="LOW_POSTOP_BLEEDING_RISK",
        antithrombotic_status="NONE_REPORTED",
        antithrombotic_classes=(),
        combination_therapy="NO",
        warfarin_inr=None,
        warfarin_inr_current=None,
        lmwh_dose_class="UNKNOWN",
    )
    data.update(overrides)
    return AntithromboticProcedureSafetyInput(**data)


def _ie(**overrides):
    data = dict(
        age_years=40,
        cardiac_risk_category="PREVIOUS_INFECTIVE_ENDOCARDITIS",
        dental_procedure_qualifies=True,
        penicillin_allergy_status="NONE_KNOWN",
        generic_medication_allergy_present=False,
        oral_route_possible=True,
        currently_taking_penicillin_or_amoxicillin=False,
        selected_active_ingredient_code="AMOXICILLIN",
        selected_presentation_verified=True,
    )
    data.update(overrides)
    return IEProphylaxisAdultOralAmoxicillinInput(**data)


def test_bleeding_gate_is_silent_when_no_antithrombotic_is_reported():
    result = evaluate_antithrombotic_procedure_safety(_bleeding())
    assert result.status == "READY"
    assert result.alert_key is None
    assert result.internal_codes == ()


def test_bleeding_gate_fails_closed_on_unknown_antithrombotic_context_for_invasive_care():
    result = evaluate_antithrombotic_procedure_safety(
        _bleeding(antithrombotic_status="UNKNOWN")
    )
    assert result.status == "CONTEXT_REQUIRED"
    assert result.alert_key == "CONTEXT_REQUIRED"
    assert "ANTITHROMBOTIC_STATUS_UNKNOWN" in result.internal_codes


def test_bleeding_gate_fails_closed_on_inconsistent_or_unknown_combination_context():
    inconsistent = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            antithrombotic_status="NONE_REPORTED",
            antithrombotic_classes=("DOAC",),
        )
    )
    unknown_combination = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("DOAC",),
            combination_therapy="UNKNOWN",
        )
    )
    assert inconsistent.status == "CONTEXT_REQUIRED"
    assert "ANTITHROMBOTIC_CONTEXT_INCONSISTENT" in inconsistent.internal_codes
    assert unknown_combination.status == "CONTEXT_REQUIRED"
    assert "ANTITHROMBOTIC_COMBINATION_STATUS_UNKNOWN" in unknown_combination.internal_codes


def test_vka_requires_current_inr_and_escalates_at_four_without_stop_instruction():
    missing = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("VKA",),
        )
    )
    assert missing.status == "CONTEXT_REQUIRED"

    elevated = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("VKA",),
            warfarin_inr=4.0,
            warfarin_inr_current=True,
        )
    )
    assert elevated.status == "PRESCRIBER_REVIEW_REQUIRED"
    assert elevated.alert_key == "PRESCRIBER_REVIEW_RECOMMENDED"
    rendered = repr(elevated).lower()
    for prohibited in ("stop ", "skip ", "hold ", "arrêt", "suspend"):
        assert prohibited not in rendered


def test_vka_invalid_inr_values_fail_closed():
    for value in (float("nan"), float("inf"), 0.0, -1.0):
        result = evaluate_antithrombotic_procedure_safety(
            _bleeding(
                antithrombotic_status="PRESENT",
                antithrombotic_classes=("VKA",),
                warfarin_inr=value,
                warfarin_inr_current=True,
            )
        )
        assert result.status == "CONTEXT_REQUIRED"
        assert "VKA_INR_CURRENT_VALUE_REQUIRED" in result.internal_codes


def test_doac_is_ready_for_low_risk_and_review_only_for_higher_risk():
    low = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("DOAC",),
        )
    )
    higher = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            procedure_bleeding_risk="HIGHER_POSTOP_BLEEDING_RISK",
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("DOAC",),
        )
    )
    assert low.status == "READY"
    assert higher.status == "CLINICAL_REVIEW_REQUIRED"
    assert higher.alert_key == "CLINICAL_REVIEW_RECOMMENDED"


def test_antiplatelet_gate_does_not_recommend_interruption():
    result = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("ANTIPLATELET",),
        )
    )
    assert result.status == "READY"
    assert result.alert_key is None


def test_combination_therapy_requires_prescriber_review():
    result = evaluate_antithrombotic_procedure_safety(
        _bleeding(
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("DOAC", "ANTIPLATELET"),
            combination_therapy="YES",
        )
    )
    assert result.status == "PRESCRIBER_REVIEW_REQUIRED"
    assert result.alert_key == "PRESCRIBER_REVIEW_RECOMMENDED"


def test_ie_wrapper_reuses_existing_rule_and_treats_known_nonqualifying_as_silent():
    ready = evaluate_ie_prophylaxis_background(_ie())
    not_qualifying = evaluate_ie_prophylaxis_background(
        _ie(dental_procedure_qualifies=False)
    )
    assert ready.status == "READY"
    assert not_qualifying.status == "READY"
    assert "DENTAL_PROCEDURE_NOT_QUALIFYING" in not_qualifying.internal_codes


def test_ie_wrapper_fails_closed_on_unknown_and_requires_review_for_clinical_blocker():
    unknown = evaluate_ie_prophylaxis_background(
        _ie(dental_procedure_qualifies=None)
    )
    allergy = evaluate_ie_prophylaxis_background(
        _ie(penicillin_allergy_status="PRESENT")
    )
    wrong_agent = evaluate_ie_prophylaxis_background(
        _ie(selected_active_ingredient_code="AMOXICILLIN_CLAVULANATE")
    )
    assert unknown.status == "CONTEXT_REQUIRED"
    assert unknown.alert_key == "CONTEXT_REQUIRED"
    assert allergy.status == "CLINICAL_REVIEW_REQUIRED"
    assert allergy.alert_key == "CLINICAL_REVIEW_RECOMMENDED"
    assert wrong_agent.status == "CLINICAL_REVIEW_REQUIRED"


def test_ie_wrapper_stays_silent_when_known_nonqualifying_fact_already_decides():
    result = evaluate_ie_prophylaxis_background(
        _ie(
            cardiac_risk_category="UNKNOWN",
            dental_procedure_qualifies=False,
            selected_presentation_verified=False,
        )
    )
    assert result.status == "READY"
    assert result.alert_key is None
    assert "DENTAL_PROCEDURE_NOT_QUALIFYING" in result.internal_codes


def test_orchestrator_exposes_only_generic_alert_key_from_dominant_gate():
    combined = orchestrate_procedure_safety(
        _bleeding(
            antithrombotic_status="PRESENT",
            antithrombotic_classes=("DOAC", "ANTIPLATELET"),
            combination_therapy="YES",
        ),
        _ie(),
    )
    assert combined.status == "PRESCRIBER_REVIEW_REQUIRED"
    assert combined.alert_key == "PRESCRIBER_REVIEW_RECOMMENDED"
    assert combined.ie is not None
    assert combined.ie.status == "READY"
