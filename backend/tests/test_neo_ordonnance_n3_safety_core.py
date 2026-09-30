from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate
from backend.services import medication_dict
from backend.services.neo_prescription_safety import evaluate_neo_prescription_safety


def _current_presentation_id():
    rows = medication_dict.search_regulatory_presentations("AMOXICILLINE", limit=20)
    assert rows
    return rows[0]["presentation_id"]


def _complete_context(**overrides):
    values = dict(
        medication_allergy_status="NONE_KNOWN",
        penicillin_allergy_status="NONE_KNOWN",
        renal_context_status="NO_KNOWN_IMPAIRMENT",
        hepatic_context_status="NO_KNOWN_IMPAIRMENT",
        pregnancy_status="NO",
        breastfeeding_status="NO",
        current_medications_status="NONE_REPORTED",
    )
    values.update(overrides)
    return PatientClinicalContextUpdate(**values)


def test_unresolved_medication_identity_blocks_immediately():
    result = evaluate_neo_prescription_safety(
        presentation_id="missing:identity", patient_context=_complete_context(), age_years=40
    )
    assert result.status == "BLOCKED"
    assert result.blockers == ("MEDICATION_IDENTITY_UNRESOLVED",)
    assert result.medication_identity_verified is False


def test_unknown_structured_context_never_becomes_silent_pass():
    result = evaluate_neo_prescription_safety(
        presentation_id=_current_presentation_id(),
        patient_context=PatientClinicalContextUpdate(),
        age_years=None,
    )
    assert result.status == "BLOCKED"
    for blocker in (
        "AGE_UNKNOWN", "MEDICATION_ALLERGY_STATUS_UNKNOWN",
        "RENAL_CONTEXT_UNKNOWN", "HEPATIC_CONTEXT_UNKNOWN",
        "PREGNANCY_STATUS_UNKNOWN", "BREASTFEEDING_STATUS_UNKNOWN",
        "CURRENT_MEDICATIONS_STATUS_UNKNOWN",
    ):
        assert blocker in result.blockers


def test_n3_does_not_claim_interactions_or_contraindications_are_clear():
    result = evaluate_neo_prescription_safety(
        presentation_id=_current_presentation_id(), patient_context=_complete_context(), age_years=40
    )
    assert result.status == "BLOCKED"
    assert "INTERACTION_KNOWLEDGE_NOT_COMPLETE" in result.blockers
    assert "CONTRAINDICATION_KNOWLEDGE_NOT_COMPLETE" in result.blockers
    assert result.interaction_evaluation_complete is False
    assert result.contraindication_evaluation_complete is False


def test_reported_risk_facts_are_visible_as_review_warnings():
    context = _complete_context(
        medication_allergy_status="PRESENT", medication_allergies=["Substance X"],
        renal_context_status="IMPAIRMENT_REPORTED", renal_context_note="reported",
        pregnancy_status="YES",
    )
    result = evaluate_neo_prescription_safety(
        presentation_id=_current_presentation_id(), patient_context=context, age_years=32
    )
    assert "MEDICATION_ALLERGY_REPORTED_REQUIRES_RECONCILIATION" in result.warnings
    assert "RENAL_IMPAIRMENT_REPORTED_REQUIRES_REVIEW" in result.warnings
    assert "PREGNANCY_REPORTED_REQUIRES_REVIEW" in result.warnings


def test_historical_identity_cannot_claim_current_marketing_status():
    rows = medication_dict.search("MEDIATOR", limit=5)
    assert rows
    result = evaluate_neo_prescription_safety(
        presentation_id=rows[0]["presentation_id"], patient_context=_complete_context(), age_years=40
    )
    assert "CURRENT_MARKETING_STATUS_NOT_VERIFIED" in result.blockers
    assert result.current_marketing_status_verified is False
