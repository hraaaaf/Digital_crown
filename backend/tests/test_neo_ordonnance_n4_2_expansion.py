from backend.services.neo_medication_evidence import (
    EVIDENCE_VERSION,
    evaluate_bounded_evidence,
    resolve_medication_identity,
)


def _eval(dci, meds):
    return evaluate_bounded_evidence(
        dci=dci,
        current_medications=meds,
        pregnancy_status="NO",
        renal_status="NO_KNOWN_IMPAIRMENT",
        hepatic_status="NO_KNOWN_IMPAIRMENT",
        medication_allergies=[],
        penicillin_allergy_status="NONE_KNOWN",
    )


def _codes(result):
    return {finding.code for finding in result.findings}


def test_n4_2_version_and_new_identity_resolution():
    assert EVIDENCE_VERSION == "2026-09-30.n4.2-v1"
    assert resolve_medication_identity("doxycycline 100 mg") == "DOXYCYCLINE"
    assert resolve_medication_identity("Lithium") == "LITHIUM"
    assert resolve_medication_identity("sertraline 50mg") == "SERTRALINE"


def test_amoxicillin_tetracycline_review_is_sourced():
    result = _eval("amoxicilline", ["doxycycline 100 mg"])
    assert "AMOXICILLIN_TETRACYCLINE_BACTERIOSTATIC_REVIEW" in _codes(result)
    assert result.interaction_complete_for_inputs is False


def test_ibuprofen_high_signal_interactions_are_detected():
    result = _eval("ibuprofene", [
        "lithium", "methotrexate", "tacrolimus", "prednisone",
        "sertraline", "furosemide", "zidovudine", "mifepristone",
    ])
    codes = _codes(result)
    assert "IBUPROFEN_LITHIUM_AVOID" in codes
    assert "IBUPROFEN_METHOTREXATE_AVOID" in codes
    assert "IBUPROFEN_CALCINEURIN_NEPHROTOXICITY" in codes
    assert "IBUPROFEN_CORTICOSTEROID_GI_BLEEDING_RISK" in codes
    assert "IBUPROFEN_ANTIPLATELET_SSRI_GI_BLEEDING_RISK" in codes
    assert "IBUPROFEN_DIURETIC_RENAL_REVIEW" in codes
    assert "IBUPROFEN_ZIDOVUDINE_BLEEDING_REVIEW" in codes
    assert "IBUPROFEN_MIFEPRISTONE_TIMING_REQUIRED" in codes
    assert result.interaction_complete_for_inputs is False
