import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCHEMAS=ROOT/"docs"/"audits"/"schemas"

AARIZ_TO_DC={
"A":"A","ANS":"ANS","B":"B","Me":"Me","N":"N","Or":"Or","Pog":"Pog","PNS":"PNS",
"Pn":"Prn","S":"S","Ar":"Ar","Co":"Co","Gn":"Gn","Go":"Go","Po":"Po",
"LIT":"L1_incisal","UIA":"U1_apex","UIT":"U1_incisal","LIA":"L1_apex",
"Li":"Li_soft","Ls":"Ls_soft","N\u0060":"N_soft","Pog\u0060":"Pog_soft","Sn":"Sn_soft",
}

def load(name):
    return json.loads((SCHEMAS/name).read_text(encoding="utf-8"))

def test_reference_equivalence_policy_is_frozen_from_lot02_human_envelopes():
    p=load("cephalo_vnext_lot04_tolerance_policy_reference_equivalence_v1.json")
    l=load("cephalo_vnext_lot02_landmark_agreement.json")
    m=load("cephalo_vnext_lot02_sentinel_measurement_agreement.json")
    assert p["policy_id"]=="REFERENCE_EQUIVALENCE_V1"
    assert p["status"]=="APPROVED_BEFORE_CANDIDATE_SCORING"
    assert p["clinical_validity_claim"] is False
    assert p["universal_2mm_gate"] is False
    assert p["human_gate"]=="A_APPROVED"
    assert p["failure_policy"]["max_failure_rate"]==0
    assert p["primary_landmark_gate"]=="candidate_median_mm <= frozen_human_median_mm AND candidate_p95_mm <= frozen_human_p95_mm"
    assert len(p["landmark_tolerances"])==24
    by_dc={x["landmark_id"]:x for x in p["landmark_tolerances"]}
    assert set(by_dc)==set(AARIZ_TO_DC.values())
    for aariz,dc in AARIZ_TO_DC.items():
        assert by_dc[dc]["max_p95_mm"]==l["landmarks"][aariz]["p95_mm"]
        assert by_dc[dc]["max_median_mm"]==l["landmarks"][aariz]["median_mm"]
        assert by_dc[dc]["max_failure_rate"]==0
    g1a=m["measurements_g1a_consensus_only"]
    clinical={x["measurement_id"]:x for x in p["clinical_tolerances"]}
    assert set(clinical)==set(g1a)
    for mid,data in clinical.items():
        assert data["max_absolute_error"]==g1a[mid]["p95_abs"]
        assert data["unit"]==g1a[mid]["unit"]

def test_reference_equivalence_policy_binds_expected_lot02_artifacts():
    p=load("cephalo_vnext_lot04_tolerance_policy_reference_equivalence_v1.json")
    assert p["source_bindings"]=={
      "landmark_agreement_sha256":"e99fa49373ed20902c7266cbe805fcc2eee2d5bc70f747f64f424cfa45d35ff0",
      "sentinel_measurement_agreement_sha256":"868de930eba33bf2b6d6b175b386f1c42e7fdb3205566ddbe331141fa5f1804d",
      "goldset_manifest_sha256":"73c742db47686b0cf8b75b599b6373d3fc707d9b25a440c8d81d3d99ced241df",
    }


def test_device_stratified_gate_is_frozen_before_alternative_scoring():
    p=load("cephalo_vnext_lot04_tolerance_policy_reference_equivalence_v1.json")
    d=p["device_stratified_policy"]
    assert d["status"]=="APPROVED_BEFORE_ALTERNATIVE_CANDIDATE_SCORING"
    assert d["min_n_for_hard_p95_gate"]==59
    assert d["hard_gate_metric"]=="p95_mm"
    assert d["comparator"]=="candidate_device_p95_mm <= frozen_LOT02_human_device_p95_mm"
    assert d["insufficient_n_status"]=="INSUFFICIENT_N_FOR_P95_GATE"
    assert d["insufficient_n_effect"]=="DESCRIPTIVE_ONLY"
    assert d["post_hoc_pooling_allowed"] is False
    assert d["aggregate_masking_allowed"] is False
