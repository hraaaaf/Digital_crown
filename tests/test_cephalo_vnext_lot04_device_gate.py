import copy
from scripts.validate_cephalo_vnext_lot04_contract import canonical_json_sha256, validate_acceptance_semantics, Lot04ContractError

def manifest():
    return {
      "candidate":{"model_sha256":"a"*64},
      "dataset":{"cases":[{"case_id":"c1"}],"development_case_ids":[],"acceptance_case_ids":["c1"]},
      "acceptance_policy":{
        "tolerance_version":"REFERENCE_EQUIVALENCE_V1",
        "landmark_tolerances":[{"landmark_id":"S","max_median_mm":1.0,"max_p95_mm":2.0,"max_failure_rate":0.0}],
        "clinical_tolerances":[{"measurement_id":"SNA","max_absolute_error":2.0,"unit":"deg"}],
      },
    }

def record(m):
    return {
      "manifest_sha256":canonical_json_sha256(m),
      "candidate_model_sha256":"a"*64,
      "landmarks":[{"landmark_id":"S","n":1,"median_mm":0.5,"p95_mm":1.0,"failure_rate":0.0,"human_reference_uncertainty_mm":2.0,"tolerance_version":"REFERENCE_EQUIVALENCE_V1","decision":"PASS"}],
      "clinical_measurements":[{"measurement_id":"SNA","n":1,"signed_bias":0.0,"absolute_error":1.0,"decision":"PASS"}],
      "device_strata":[],
      "overall_decision":"PASS",
    }

def test_descriptive_device_stratum_does_not_block_overall_pass():
    m=manifest();r=record(m)
    r["device_strata"]=[{"device":"D","landmark_id":"S","n":58,"p95_mm":3.0,"human_device_p95_mm":1.0,"gate_status":"INSUFFICIENT_N_FOR_P95_GATE","decision":"DESCRIPTIVE_ONLY"}]
    validate_acceptance_semantics(r,m)

def test_hard_device_failure_blocks_overall_pass():
    m=manifest();r=record(m)
    r["device_strata"]=[{"device":"D","landmark_id":"S","n":59,"p95_mm":3.0,"human_device_p95_mm":1.0,"gate_status":"HARD_GATE","decision":"FAIL"}]
    try:
        validate_acceptance_semantics(r,m)
    except Lot04ContractError as e:
        assert "hard-gated device failure" in str(e)
    else:
        raise AssertionError("hard device failure must block overall PASS")

def test_hard_device_failure_can_support_overall_fail():
    m=manifest();r=record(m)
    r["device_strata"]=[{"device":"D","landmark_id":"S","n":59,"p95_mm":3.0,"human_device_p95_mm":1.0,"gate_status":"HARD_GATE","decision":"FAIL"}]
    r["overall_decision"]="FAIL"
    validate_acceptance_semantics(r,m)
