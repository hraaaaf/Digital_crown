from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate
from backend.services import medication_dict


def test_neo_search_prefers_current_ammps_overlay_when_identity_matches():
    results = medication_dict.search_unified("AMOXICILLINE", limit=50)
    assert results
    current = [r for r in results if r["neo_source_state"] == "CURRENT_REGULATORY_OVERLAY"]
    assert current
    assert all(r["source"]["id"] == medication_dict.AMMPS_CURRENT_SOURCE["id"] for r in current)
    assert all(r["may_claim_current_marketing_status"] is True for r in current)


def test_neo_search_keeps_historical_rows_explicitly_documentary():
    results = medication_dict.search_unified("MEDIATOR", limit=20)
    assert results
    assert all(r["neo_source_state"] == "DOCUMENTARY_REFERENCE" for r in results)
    assert all(r["may_claim_current_marketing_status"] is False for r in results)


def test_rx_context_current_medications_fail_closed_and_deduplicate():
    ctx = PatientClinicalContextUpdate(
        current_medications_status="PRESENT",
        current_medications=["Xarelto 20 mg", "xarelto 20 mg", "  Parac?tamol  "],
    )
    assert ctx.current_medications == ["Xarelto 20 mg", "Parac?tamol"]


def test_rx_context_present_requires_explicit_medication():
    try:
        PatientClinicalContextUpdate(current_medications_status="PRESENT", current_medications=[])
    except ValueError as exc:
        assert "traitement actuel explicite" in str(exc)
    else:
        raise AssertionError("PRESENT without medication must fail closed")


def test_rx_context_unknown_never_carries_silent_medications():
    ctx = PatientClinicalContextUpdate(
        current_medications_status="UNKNOWN",
        current_medications=None,
        pregnancy_status="UNKNOWN",
        breastfeeding_status="UNKNOWN",
    )
    assert ctx.current_medications is None
    assert ctx.pregnancy_status == "UNKNOWN"
    assert ctx.breastfeeding_status == "UNKNOWN"


def test_neo_search_current_rows_precede_documentary_fallbacks():
    results = medication_dict.search_unified("AMOXICILLINE", limit=50)
    states = [row["neo_source_state"] for row in results]
    assert "CURRENT_REGULATORY_OVERLAY" in states
    if "DOCUMENTARY_REFERENCE" in states:
        first_documentary = states.index("DOCUMENTARY_REFERENCE")
        assert all(state == "CURRENT_REGULATORY_OVERLAY" for state in states[:first_documentary])


def test_neo_search_deduplicates_exact_presentation_identity():
    results = medication_dict.search_unified("AMOXICILLINE", limit=50)
    identities = [
        tuple(str(row.get(field) or "").strip().upper() for field in ("nom", "dci", "dosage", "unite", "forme"))
        for row in results
    ]
    assert len(identities) == len(set(identities))
