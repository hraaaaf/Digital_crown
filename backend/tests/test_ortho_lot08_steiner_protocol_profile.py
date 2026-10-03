import json
from pathlib import Path

from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS

ROOT=Path(__file__).resolve().parents[2]
PROFILE=ROOT/"docs/audits/schemas/ortho_lot08_steiner_protocol_profile_v1.json"

def _profile():
    return json.loads(PROFILE.read_text(encoding="utf-8"))

def test_steiner_profile_is_precode_source_locked_and_lot06_authoritative():
    p=_profile()
    assert p["status"]=="SOURCE_LOCKED"
    assert p["pre_code_gate"]["gate"]=="ORTHO_ANALYSIS_PROTOCOLS_SOURCE_LOCKED"
    assert p["pre_code_gate"]["status"]=="SATISFIED"
    assert p["final_gate"]["status"]=="SATISFIED"
    assert p["protocol_profile_id"]=="STEINER_STATIC_PROTOCOL_PROFILE_V1"
    assert p["scientific_authority"]=="LOT06_CANONICAL_MEASUREMENT_REGISTRY"
    assert p["execution_policy"]["parallel_formula_outside_LOT06"]=="FORBIDDEN"

def test_every_steiner_measurement_identity_is_canonical():
    p=_profile()
    ids=[]
    for layer in p["layers"].values():
        ids += layer.get("required_measurement_ids",[])
        ids += layer.get("optional_serial_or_auxiliary",[])
        ids += layer.get("serial_assessment",[])
    missing=sorted(set(ids)-set(CANONICAL_MEASUREMENTS))
    assert missing==[]

def test_unresolved_detector_semantics_are_not_promoted_into_core():
    p=_profile()
    base=p["layers"]["STEINER_1953_BASE"]
    assert "M_U6_NA_MM_V1" not in base["required_measurement_ids"]
    assert "M_L6_NB_MM_V1" not in base["required_measurement_ids"]
    assert p["explicit_manual_or_constructed_identities"]["D_Steiner_1959"].startswith("manual_explicit_only")

def test_historical_norms_cannot_classify_patients():
    p=_profile()
    norm=p["norm_sets"][0]
    assert norm["authority"]=="REFERENCE_DISPLAY_ONLY"
    assert norm["classification_authority"] is False
    assert norm["out_of_domain_behavior"]=="DISPLAY_MEASUREMENT_AND_REFERENCE_WITHOUT_CLASSIFICATION"

def test_treatment_decisions_remain_clinician_owned():
    p=_profile()
    assert p["scope_resolutions"]["AUTONOMOUS_TREATMENT"]=="FORBIDDEN"
    assert p["scope_resolutions"]["EXTRACTION_NON_EXTRACTION"]=="CLINICIAN_ONLY"


def test_serial_semantics_are_explicitly_outside_static_profile_gate():
    p=_profile()
    serial=p["separate_profiles"]["STEINER_SERIAL_ASSESSMENT_V1"]
    assert serial["status"]=="DEFERRED_SEPARATE_PROFILE"
    assert set(serial["measurement_ids"])=={"M_SERIAL_INCISOR_DISPLACEMENT_V1","M_SERIAL_MOLAR_DISPLACEMENT_V1"}

def test_holdaway_relationship_is_interpretive_not_treatment_authority():
    p=_profile()
    rel=p["layers"]["STEINER_1959_EXTENSION"]["derived_relationships"][0]
    assert rel["inputs"]==["M_L1_NB_MM_V1","M_POG_NB_MM_V1"]
    assert rel["authority"]=="PROTOCOL_DERIVED_INTERPRETATION_ONLY"
    assert rel["autonomous_treatment"] is False
