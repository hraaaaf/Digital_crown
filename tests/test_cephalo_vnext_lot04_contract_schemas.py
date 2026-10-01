import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

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
        "acceptance_policy": {"preregistered":True,"universal_2mm_gate":False,"human_reference_uncertainty_required":True,"landmark_specific":True,"aggregate_regression_masking_forbidden":True},
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
