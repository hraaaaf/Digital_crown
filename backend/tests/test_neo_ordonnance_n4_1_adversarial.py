from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate
from backend.services import medication_dict
from backend.services.neo_medication_evidence import (
    evaluate_bounded_evidence,
    resolve_medication_identity,
)
from backend.services.neo_prescription_safety import evaluate_neo_prescription_safety

BASE = dict(
    pregnancy_status="NO",
    renal_status="NO_KNOWN_IMPAIRMENT",
    hepatic_status="NO_KNOWN_IMPAIRMENT",
    medication_allergies=[],
    penicillin_allergy_status="NONE_KNOWN",
)


def ev(dci, meds=(), **kw):
    args = dict(BASE)
    args.update(kw)
    return evaluate_bounded_evidence(dci=dci, current_medications=meds, **args)


def test_accented_methotrexate_resolves_and_blocks():
    r = ev("AMOXICILLINE", ["méthotrexate 10 mg"])
    assert not r.interaction_complete_for_inputs
    assert any(
        x.code == "AMOXICILLIN_METHOTREXATE_INTERACTION" for x in r.findings
    )


def test_substring_is_not_false_methotrexate_match():
    assert resolve_medication_identity("NOTMETHOTREXATEFAKE") is None
    r = ev("AMOXICILLINE", ["NOTMETHOTREXATEFAKE"])
    assert not any(
        x.code == "AMOXICILLIN_METHOTREXATE_INTERACTION" for x in r.findings
    )
    assert not r.interaction_complete_for_inputs


def test_xarelto_identity_resolves_but_evidence_stays_fail_closed():
    assert resolve_medication_identity("Xarelto 20 mg") == "RIVAROXABAN"
    r = ev("AMOXICILLINE", ["Xarelto 20 mg"])
    assert not r.interaction_complete_for_inputs
    assert not r.contraindication_complete_for_inputs


def test_eliquis_identity_resolves_but_evidence_stays_fail_closed():
    assert resolve_medication_identity("Eliquis 5 mg") == "APIXABAN"
    r = ev("IBUPROFENE", ["Eliquis 5 mg"])
    assert not r.interaction_complete_for_inputs
    assert not r.contraindication_complete_for_inputs


def test_unknown_ibuprofen_clinical_context_not_complete():
    r = ev("IBUPROFENE", [], pregnancy_status="UNKNOWN")
    assert not r.interaction_complete_for_inputs
    assert not r.contraindication_complete_for_inputs


def test_unknown_amoxicillin_renal_context_not_complete():
    r = ev("AMOXICILLINE", [], renal_status="UNKNOWN")
    assert not r.interaction_complete_for_inputs
    assert not r.contraindication_complete_for_inputs


def test_known_warfarin_identity_still_emits_bounded_finding():
    assert resolve_medication_identity("Warfarine 5 mg") == "WARFARIN"
    r = ev("IBUPROFENE", ["Warfarine 5 mg"])
    assert not r.interaction_complete_for_inputs
    assert any(
        x.code == "IBUPROFEN_ORAL_ANTICOAGULANT_BLEEDING_RISK" for x in r.findings
    )


def test_safety_core_keeps_bounded_evidence_domains_blocked():
    rows = medication_dict.search_unified("AMOXICILLINE", limit=100)
    pid = next(
        r["presentation_id"] for r in rows if r.get("may_claim_current_marketing_status")
    )
    ctx = PatientClinicalContextUpdate(
        medication_allergy_status="NONE_KNOWN",
        penicillin_allergy_status="NONE_KNOWN",
        renal_context_status="NO_KNOWN_IMPAIRMENT",
        hepatic_context_status="NO_KNOWN_IMPAIRMENT",
        pregnancy_status="NO",
        breastfeeding_status="NO",
        current_medications_status="PRESENT",
        current_medications=["Xarelto 20 mg"],
    )
    r = evaluate_neo_prescription_safety(
        presentation_id=pid, patient_context=ctx, age_years=40
    )
    assert r.status == "BLOCKED"
    assert "INTERACTION_KNOWLEDGE_NOT_COMPLETE" in r.blockers
    assert "CONTRAINDICATION_KNOWLEDGE_NOT_COMPLETE" in r.blockers
    assert not r.interaction_evaluation_complete
    assert not r.contraindication_evaluation_complete
