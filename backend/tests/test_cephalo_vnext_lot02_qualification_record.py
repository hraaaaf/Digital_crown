import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RECORD=ROOT/"docs"/"audits"/"schemas"/"cephalo_vnext_lot02_aariz_qualification.json"

def load():
    return json.loads(RECORD.read_text(encoding="utf-8"))

def test_qualification_record_counts_are_complete_and_consistent():
    r=load()
    q=r["qc_counts"]
    assert sum(q.values())==29000
    assert q=={
        "CONSENSUS_CANDIDATE":27248,
        "REVIEW_REQUIRED":1309,
        "ADJUDICATION_REQUIRED":441,
        "STRUCTURAL_INVALID":2,
    }
    assert sum(sum(v.values()) for v in r["split_counts"].values())==29000
    assert r["source"]["cases"]==1000
    assert r["source"]["splits"]=={"train":700,"valid":150,"test":150}

def test_unresolved_pairs_cannot_be_exact_ground_truth():
    r=load()
    p=r["qc_policy"]
    assert p["auto_midpoint_only_for"]=="CONSENSUS_CANDIDATE"
    assert p["unresolved_pairs_are_not_exact_ground_truth"] is True
    assert p["thresholds_are_clinical_acceptance"] is False
    assert "never silently averaged" in r["g1_design"]["G1B"]

def test_srpose_published_checkpoint_is_byte_identical_to_frozen_checkpoint():
    r=load()
    p=r["detector_provenance"]
    assert p["byte_for_byte_match"] is True
    assert p["source_weight_sha256"]==p["digital_crown_frozen_checkpoint_sha256"]
    assert p["source_weight_sha256"]=="fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc"
    assert p["aariz_reference_in_source_repo"] is False

def test_qualification_does_not_select_detector_or_grant_clinical_acceptance():
    r=load()
    effect=r["gate_effect"]
    assert effect["detector_selection"]=="NOT_GRANTED_BY_THIS_RECORD"
    assert effect["clinical_acceptance"]=="NOT_GRANTED_BY_THIS_RECORD"


def test_g2_cross_device_distribution_is_frozen_and_complete():
    r=load()
    g2=r["g2_cross_device"]
    assert g2["devices"]==7
    assert len(g2["machine_distribution"])==7
    assert sum(g2["machine_distribution"].values())==1000
    assert sum(g2["pixel_size_distribution_mm_per_px"].values())==1000
    assert g2["role"].startswith("External cross-device stratification")
