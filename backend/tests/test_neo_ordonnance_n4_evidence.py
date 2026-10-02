from backend.services import medication_dict
from backend.services.neo_medication_evidence import evaluate_bounded_evidence
from backend.services.neo_prescription_safety import evaluate_neo_prescription_safety
from backend.schemas.patient_clinical_context import PatientClinicalContextUpdate

def _pid(q):
    rows = medication_dict.search_unified(q, limit=100)
    current = [r for r in rows if r.get("may_claim_current_marketing_status")]
    assert current
    return current[0]["presentation_id"]

def _ctx(**kw):
    base=dict(medication_allergy_status="NONE_KNOWN", penicillin_allergy_status="NONE_KNOWN", renal_context_status="NO_KNOWN_IMPAIRMENT", hepatic_context_status="NO_KNOWN_IMPAIRMENT", pregnancy_status="NO", breastfeeding_status="NO", current_medications_status="NONE_REPORTED", current_medications=None)
    base.update(kw); return PatientClinicalContextUpdate(**base)

def test_unknown_dci_remains_not_covered():
    r=evaluate_bounded_evidence(dci="UNKNOWN X", current_medications=[], pregnancy_status="NO", renal_status="NO_KNOWN_IMPAIRMENT", hepatic_status="NO_KNOWN_IMPAIRMENT", medication_allergies=[], penicillin_allergy_status="NONE_KNOWN")
    assert not r.covered and not r.interaction_complete_for_inputs and not r.contraindication_complete_for_inputs

def test_amoxicillin_methotrexate_is_blocking_and_sourced():
    r=evaluate_bounded_evidence(dci="AMOXICILLINE", current_medications=["Methotrexate 10 mg"], pregnancy_status="NO", renal_status="NO_KNOWN_IMPAIRMENT", hepatic_status="NO_KNOWN_IMPAIRMENT", medication_allergies=[], penicillin_allergy_status="NONE_KNOWN")
    f={x.code:x for x in r.findings}
    assert "AMOXICILLIN_METHOTREXATE_INTERACTION" in f and f["AMOXICILLIN_METHOTREXATE_INTERACTION"].source_ids

def test_amoxicillin_penicillin_allergy_is_contraindicated():
    r=evaluate_bounded_evidence(dci="AMOXICILLIN", current_medications=[], pregnancy_status="NO", renal_status="NO_KNOWN_IMPAIRMENT", hepatic_status="NO_KNOWN_IMPAIRMENT", medication_allergies=[], penicillin_allergy_status="PRESENT")
    assert any(x.code=="AMOXICILLIN_PENICILLIN_ALLERGY_CONTRAINDICATION" and x.severity=="CONTRAINDICATED" for x in r.findings)

def test_ibuprofen_anticoagulant_is_blocking():
    r=evaluate_bounded_evidence(dci="IBUPROFENE", current_medications=["Warfarine 5 mg"], pregnancy_status="NO", renal_status="NO_KNOWN_IMPAIRMENT", hepatic_status="NO_KNOWN_IMPAIRMENT", medication_allergies=[], penicillin_allergy_status="NONE_KNOWN")
    assert any(x.code=="IBUPROFEN_ORAL_ANTICOAGULANT_BLEEDING_RISK" and x.severity=="HIGH_RISK" for x in r.findings)

def test_ibuprofen_pregnancy_does_not_guess_gestational_age():
    r=evaluate_bounded_evidence(dci="IBUPROFEN", current_medications=[], pregnancy_status="YES", renal_status="NO_KNOWN_IMPAIRMENT", hepatic_status="NO_KNOWN_IMPAIRMENT", medication_allergies=[], penicillin_allergy_status="NONE_KNOWN")
    assert any(x.code=="IBUPROFEN_PREGNANCY_GESTATIONAL_AGE_REQUIRED" and x.severity=="BLOCK" for x in r.findings)

def test_n4_core_keeps_interaction_boundary_fail_closed_for_covered_dci():
    r=evaluate_neo_prescription_safety(presentation_id=_pid("AMOXICILLINE"), patient_context=_ctx(), age_years=40)
    assert not r.interaction_evaluation_complete and not r.contraindication_evaluation_complete
    assert "INTERACTION_KNOWLEDGE_NOT_COMPLETE" in r.blockers
    assert "CONTRAINDICATION_KNOWLEDGE_NOT_COMPLETE" in r.blockers
    assert r.evidence_version and r.source_ids

def test_n4_core_blocks_known_amoxicillin_methotrexate_interaction():
    r=evaluate_neo_prescription_safety(presentation_id=_pid("AMOXICILLINE"), patient_context=_ctx(current_medications_status="PRESENT", current_medications=["Methotrexate 10 mg"]), age_years=40)
    assert r.status=="BLOCKED"
    assert "AMOXICILLIN_METHOTREXATE_INTERACTION" in r.blockers
