import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

from scripts.validate_cephalo_vnext_lot04_contract import (Lot04ContractError, canonical_json_sha256, validate_acceptance_semantics, validate_manifest_semantics)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "docs" / "audits" / "schemas"


def load(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def valid_manifest():
    return {
        "schema_version": "CEPHALO_LOT04_BENCHMARK_MANIFEST_V1",
        "candidate": {
            "model_name": "srpose38-tta-1024.onnx",
            "model_sha256": "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb",
            "model_size_bytes": 267484931,
            "checkpoint_sha256": "fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc",
            "source_commit": "18d17d1934970016e7610c4849311900b8d1f191",
            "preprocessing_commit": "71efbb62db60fbb2152c7f70e263b500a44f2c80",
            "provider": "CPUExecutionProvider",
            "output_count": 38,
            "index_mapping_version": "LOT03_V1",
        },
        "environment": {"python": "3.10", "numpy": "2.4.3", "onnxruntime": "1.25.0", "opencv": "4.13.0.92"},
        "onnx_interface": {"input_name": "CAPTURE_AT_RUN", "input_dtype": "CAPTURE_AT_RUN", "input_shape": [1,3,1024,1024], "output_name": "CAPTURE_AT_RUN", "output_dtype": "CAPTURE_AT_RUN", "output_shape": [1,38,1024,1024]},
        "preprocessing": {"input_size":[1024,1024],"bbox_padding":1.25,"interpolation":"cv2.INTER_LINEAR","color_conversion":"BGR_TO_RGB","mean":[121.25,121.25,121.25],"std":[76.5,76.5,76.5],"tta_embedded_in_onnx":True,"darkpose_blur_kernel":11},
        "dataset": {"manifest_frozen_before_scoring":True,"cases":[{"case_id":"G0-fixture","sha256":"0"*64,"layer":"G0","calibration_provenance":None}],"development_case_ids":["G0-fixture"],"acceptance_case_ids":[]},
        "metrics": {"per_landmark_mm":True,"directional_xy":True,"robust_percentiles":True,"failure_rate":True,"sdr_secondary":True,"clinical_propagation":["SNA","SNB","ANB","FMA","IMPA","FMIA","SN-GoGn","Co-A","Co-Gn"]},
        "acceptance_policy": {"preregistered":True,"universal_2mm_gate":False,"human_reference_uncertainty_required":True,"landmark_specific":True,"aggregate_regression_masking_forbidden":True,"tolerance_version":"PRE_REGISTERED_V1","landmark_tolerances":[{"landmark_id":"S","max_median_mm":1.0,"max_p95_mm":2.0,"max_failure_rate":0.01}],"clinical_tolerances":[{"measurement_id":"SNA","max_absolute_error":1.0,"unit":"deg"}]},
    }


def test_manifest_schema_accepts_contract_shape():
    jsonschema.validate(valid_manifest(), load("cephalo_vnext_lot04_benchmark_manifest.schema.json"))


@pytest.mark.parametrize("mutation", ["wrong_provider","wrong_count","universal_2mm","unfrozen_manifest"])
def test_manifest_schema_rejects_contract_violations(mutation):
    payload = valid_manifest()
    if mutation == "wrong_provider": payload["candidate"]["provider"] = "CUDAExecutionProvider"
    elif mutation == "wrong_count": payload["candidate"]["output_count"] = 40
    elif mutation == "universal_2mm": payload["acceptance_policy"]["universal_2mm_gate"] = True
    else: payload["dataset"]["manifest_frozen_before_scoring"] = False
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, load("cephalo_vnext_lot04_benchmark_manifest.schema.json"))


def test_acceptance_record_requires_explicit_decision():
    schema = load("cephalo_vnext_lot04_acceptance_record.schema.json")
    payload = {
        "schema_version":"CEPHALO_LOT04_ACCEPTANCE_RECORD_V1","manifest_sha256":"1"*64,
        "candidate_model_sha256":"2"*64,"executed_at":"2026-10-01T00:00:00Z",
        "landmarks":[{"landmark_id":"S","status":"CLINICAL_CANONICAL","n":0,"median_mm":None,"p95_mm":None,"failure_rate":0,"human_reference_uncertainty_mm":None,"tolerance_version":"PRE_REGISTERED_V1","decision":"INSUFFICIENT_EVIDENCE"}],
        "clinical_measurements":[],"overall_decision":"INSUFFICIENT_EVIDENCE","decision_reasons":["No G1/G2 execution in LOT04 contract phase"]
    }
    jsonschema.validate(payload, schema)
    del payload["overall_decision"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)



def test_manifest_semantics_reject_overlap_unknown_and_duplicate():
    payload = valid_manifest()
    payload["dataset"]["acceptance_case_ids"] = ["G0-fixture"]
    with pytest.raises(Lot04ContractError): validate_manifest_semantics(payload)
    payload = valid_manifest()
    payload["dataset"]["acceptance_case_ids"] = ["UNKNOWN"]
    with pytest.raises(Lot04ContractError): validate_manifest_semantics(payload)
    payload = valid_manifest()
    payload["dataset"]["cases"].append(dict(payload["dataset"]["cases"][0]))
    with pytest.raises(Lot04ContractError): validate_manifest_semantics(payload)


def acceptance_for(manifest, overall="INSUFFICIENT_EVIDENCE"):
    return {
        "manifest_sha256": canonical_json_sha256(manifest),
        "candidate_model_sha256": manifest["candidate"]["model_sha256"],
        "landmarks": [{"landmark_id":"S","n":0,"human_reference_uncertainty_mm":None,"decision":"INSUFFICIENT_EVIDENCE"}],
        "clinical_measurements": [],
        "overall_decision": overall,
    }


def test_acceptance_semantics_links_manifest_and_model_hashes():
    manifest = valid_manifest()
    record = acceptance_for(manifest)
    validate_acceptance_semantics(record, manifest)
    record["manifest_sha256"] = "f"*64
    with pytest.raises(Lot04ContractError): validate_acceptance_semantics(record, manifest)
    record = acceptance_for(manifest)
    record["candidate_model_sha256"] = "e"*64
    with pytest.raises(Lot04ContractError): validate_acceptance_semantics(record, manifest)


def test_acceptance_semantics_forbids_false_pass_and_empty_acceptance_split():
    manifest = valid_manifest()
    record = acceptance_for(manifest, "PASS")
    with pytest.raises(Lot04ContractError): validate_acceptance_semantics(record, manifest)


def test_acceptance_semantics_forbids_pass_hiding_clinical_failure():
    manifest = valid_manifest()
    manifest["dataset"]["acceptance_case_ids"] = []
    record = acceptance_for(manifest, "PASS")
    record["landmarks"] = [{"landmark_id":"S","n":10,"human_reference_uncertainty_mm":0.5,"decision":"PASS"}]
    record["clinical_measurements"] = [{"measurement_id":"SNA","decision":"FAIL"}]
    with pytest.raises(Lot04ContractError): validate_acceptance_semantics(record, manifest)


def test_acceptance_semantics_forbids_unexplained_fail():
    manifest = valid_manifest()
    record = acceptance_for(manifest, "FAIL")
    record["landmarks"][0]["decision"] = "PASS"
    record["landmarks"][0]["n"] = 10
    record["landmarks"][0]["human_reference_uncertainty_mm"] = 0.5
    with pytest.raises(Lot04ContractError): validate_acceptance_semantics(record, manifest)


def test_acceptance_semantics_binds_pass_to_preregistered_tolerances():
    manifest = valid_manifest()
    manifest["dataset"]["cases"].append({"case_id":"G1-accept","sha256":"4"*64,"layer":"G1","calibration_provenance":"manual"})
    manifest["dataset"]["acceptance_case_ids"] = ["G1-accept"]
    record = {
        "manifest_sha256": canonical_json_sha256(manifest),
        "candidate_model_sha256": manifest["candidate"]["model_sha256"],
        "landmarks": [{"landmark_id":"S","n":10,"median_mm":1.1,"p95_mm":1.5,"failure_rate":0.0,"human_reference_uncertainty_mm":0.5,"tolerance_version":"PRE_REGISTERED_V1","decision":"PASS"}],
        "clinical_measurements": [{"measurement_id":"SNA","absolute_error":0.5,"decision":"PASS"}],
        "overall_decision":"PASS",
    }
    with pytest.raises(Lot04ContractError):
        validate_acceptance_semantics(record, manifest)
    record["landmarks"][0]["median_mm"] = 0.9
    validate_acceptance_semantics(record, manifest)
