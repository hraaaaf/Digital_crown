from backend.services.prescription_clinical_rules import (
    IEProphylaxisAdultOralAmoxicillinInput,
    evaluate_ie_prophylaxis_adult_oral_amoxicillin,
)


def _eligible(**overrides):
    data = dict(
        age_years=40,
        cardiac_risk_category="PREVIOUS_INFECTIVE_ENDOCARDITIS",
        dental_procedure_qualifies=True,
        penicillin_allergy_status="NONE_KNOWN",
        oral_route_possible=True,
        currently_taking_penicillin_or_amoxicillin=False,
        selected_active_ingredient_code="AMOXICILLIN",
        selected_presentation_verified=True,
    )
    data.update(overrides)
    return IEProphylaxisAdultOralAmoxicillinInput(**data)


def test_exact_eligible_adult_rule_returns_traceable_single_dose():
    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(_eligible())

    assert result.status == "READY"
    assert result.blockers == ()
    assert result.active_ingredient_code == "AMOXICILLIN"
    assert result.total_dose_mg == 2000
    assert result.timing_min_minutes_before == 30
    assert result.timing_max_minutes_before == 60
    assert result.single_dose is True
    assert result.rule_id == "IE_PROPHYLAXIS_ADULT_ORAL_AMOXICILLIN"
    assert len(result.source_ids) == 2


def test_unknown_inputs_fail_closed_instead_of_guessing():
    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        _eligible(
            age_years=None,
            cardiac_risk_category="UNKNOWN",
            dental_procedure_qualifies=None,
            penicillin_allergy_status="UNKNOWN",
            oral_route_possible=None,
            currently_taking_penicillin_or_amoxicillin=None,
            selected_active_ingredient_code=None,
            selected_presentation_verified=False,
        )
    )

    assert result.status == "BLOCKED"
    assert result.total_dose_mg is None
    assert "AGE_UNKNOWN" in result.blockers
    assert "CARDIAC_RISK_UNKNOWN" in result.blockers
    assert "DENTAL_PROCEDURE_ELIGIBILITY_UNKNOWN" in result.blockers
    assert "PENICILLIN_ALLERGY_UNKNOWN" in result.blockers
    assert "ORAL_ROUTE_UNKNOWN" in result.blockers
    assert "CURRENT_ANTIBIOTIC_EXPOSURE_UNKNOWN" in result.blockers
    assert "PRESENTATION_NOT_VERIFIED" in result.blockers
    assert "ACTIVE_INGREDIENT_NOT_AMOXICILLIN" in result.blockers


def test_rule_blocks_non_qualifying_cardiac_context():
    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        _eligible(cardiac_risk_category="NONE_REPORTED")
    )
    assert result.status == "BLOCKED"
    assert result.blockers == ("CARDIAC_RISK_NOT_QUALIFYING",)


def test_rule_blocks_non_qualifying_dental_procedure():
    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        _eligible(dental_procedure_qualifies=False)
    )
    assert result.status == "BLOCKED"
    assert result.blockers == ("DENTAL_PROCEDURE_NOT_QUALIFYING",)


def test_rule_blocks_reported_penicillin_allergy():
    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        _eligible(penicillin_allergy_status="PRESENT")
    )
    assert result.status == "BLOCKED"
    assert result.blockers == ("PENICILLIN_ALLERGY_PRESENT",)


def test_rule_blocks_current_penicillin_or_amoxicillin_exposure():
    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        _eligible(currently_taking_penicillin_or_amoxicillin=True)
    )
    assert result.status == "BLOCKED"
    assert result.blockers == ("CURRENT_PENICILLIN_OR_AMOXICILLIN",)


def test_rule_blocks_pediatric_patient_instead_of_reusing_adult_dose():
    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(_eligible(age_years=17))
    assert result.status == "BLOCKED"
    assert result.total_dose_mg is None
    assert result.blockers == ("ADULT_RULE_ONLY",)


def test_rule_blocks_unverified_or_wrong_medication_identity():
    unverified = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        _eligible(selected_presentation_verified=False)
    )
    wrong_agent = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        _eligible(selected_active_ingredient_code="AMOXICILLIN_CLAVULANATE")
    )

    assert unverified.status == "BLOCKED"
    assert unverified.blockers == ("PRESENTATION_NOT_VERIFIED",)
    assert wrong_agent.status == "BLOCKED"
    assert wrong_agent.blockers == ("ACTIVE_INGREDIENT_NOT_AMOXICILLIN",)
