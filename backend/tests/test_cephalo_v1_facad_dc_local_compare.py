"""Local-only FACAD/DC comparison FUE-0. ALL data below are synthetic."""
import copy
import json

import pytest

from audit.cephalo_v1_facad_dc_local_compare import compare_local_case, main

HASH_IMAGE = "a" * 64
HASH_FACAD = "b" * 64
HASH_DC = "c" * 64


def _fixture():
    return {
        "schema_version": "CEPH_V1_FACAD_DC_LOCAL_SAME_TRACE_V1",
        "facad": {
            "same_trace_case_id": "SYNTHETIC-NO-PATIENT-01",
            "source_image_sha256": HASH_IMAGE,
            "export_sha256": HASH_FACAD,
            "version": "synthetic-facad-3.14",
            "unit": "mm",
            "values_mm": {"Wits": 1.0, "Co-A": 1.0, "Co-Gn": 2.0, "ANS-Me": 1.2},
        },
        "digital_crown": {
            "same_trace_case_id": "SYNTHETIC-NO-PATIENT-01",
            "source_image_sha256": HASH_IMAGE,
            "export_sha256": HASH_DC,
            "version": "synthetic-dc-r14",
            "coordinate_frame_verified": True,
            "calibration": {"verified": True, "source": "SYNTHETIC_RULER", "mm_per_pixel": 0.2},
            "manual_olp_verified": True,
            "co_reference_equivalence_verified": True,
            "landmarks_px": {
                "olp": [0, 0], "u1_incisal": [10, 2], "l1_incisal": [10, -2],
                "b": [2, 3], "a": [7, 8], "co_anatomic": [4, 4],
                "gn": [10, 12], "ans": [2, 1], "me": [2, 7],
            },
        },
        "tolerance_mm": 0.01,
    }


def _metrics(case):
    return compare_local_case(case)["measurements"]


def test_synthetic_expected_values_match_but_never_claim_clinical_vendor_parity():
    case = _fixture()
    case["digital_crown"]["landmarks_px"]["co_anatomic"] = [4, 4]
    # Co-A sqrt((7-4)^2+(8-4)^2)=5px -> 1 mm;
    # Co-Gn sqrt((10-4)^2+(12-4)^2)=10px -> 2 mm.
    output = compare_local_case(case)
    assert {output["measurements"][k]["status"] for k in ("Wits", "Co-A", "Co-Gn", "ANS-Me")} == {"NUMERIC_MATCH"}
    assert output["measurements"]["Z"]["status"] == "NOT_COMPARABLE"
    assert output["measurements"]["Z"]["reason"] == "HOLD_Z_ORIENTATION"
    assert output["clinical_validation_available"] is False
    assert output["same_trace_numeric_parity_observed"] is False


def test_actual_dc_delta_and_sign_are_preserved():
    case = _fixture()
    case["facad"]["values_mm"]["Wits"] = -1
    metrics = _metrics(case)
    assert metrics["Wits"]["status"] == "DIFFERENT"
    assert metrics["Wits"]["delta_mm"] == pytest.approx(2.0)
    assert metrics["Co-A"]["status"] == "NUMERIC_MATCH"


def test_zero_tolerance_is_explicit_and_valid():
    case = _fixture()
    case["tolerance_mm"] = 0
    assert _metrics(case)["Wits"]["status"] == "NUMERIC_MATCH"


@pytest.mark.parametrize("mutate,reason", [
    (lambda c: c.update(schema_version="bad"), "SCHEMA_INVALID"),
    (lambda c: c["facad"].update(same_trace_case_id="OTHER"), "SAME_TRACE_ID_MISMATCH"),
    (lambda c: c["facad"].update(source_image_sha256="d" * 64), "SOURCE_IMAGE_HASH_MISMATCH"),
    (lambda c: c["digital_crown"].update(source_image_sha256="not-a-sha"), "SOURCE_IMAGE_HASH_MISMATCH"),
    (lambda c: c["facad"].update(export_sha256=None), "EXPORT_ATTESTATION_MISSING"),
    (lambda c: c["facad"].update(unit="cm"), "FACAD_UNIT_NOT_MM"),
    (lambda c: c["digital_crown"].update(coordinate_frame_verified=False), "DC_COORDINATE_FRAME_UNVERIFIED"),
    (lambda c: c["digital_crown"]["calibration"].update(verified=False), "DC_NATIVE_CALIBRATION_UNVERIFIED"),
    (lambda c: c["digital_crown"]["calibration"].update(mm_per_pixel=None), "DC_NATIVE_CALIBRATION_UNVERIFIED"),
    (lambda c: c["digital_crown"]["calibration"].update(mm_per_pixel=0), "DC_NATIVE_CALIBRATION_UNVERIFIED"),
    (lambda c: c.update(tolerance_mm=None), "TOLERANCE_MISSING_OR_INVALID"),
    (lambda c: c.update(tolerance_mm=-1), "TOLERANCE_MISSING_OR_INVALID"),
])
def test_fail_closed_global_attestation(mutate, reason):
    case = _fixture()
    mutate(case)
    metrics = _metrics(case)
    for name in ("Wits", "Co-A", "Co-Gn", "ANS-Me"):
        assert metrics[name]["status"] == "NOT_COMPARABLE"
        assert metrics[name]["reason"] == reason


def test_co_ambiguity_gates_only_the_co_dependent_measurements():
    case = _fixture()
    case["digital_crown"]["co_reference_equivalence_verified"] = False
    metrics = _metrics(case)
    assert metrics["Wits"]["status"] == "NUMERIC_MATCH"
    assert metrics["ANS-Me"]["status"] == "NUMERIC_MATCH"
    assert metrics["Co-A"]["reason"] == "CONDYLION_REFERENCE_NOT_ATTESTED"
    assert metrics["Co-Gn"]["reason"] == "CONDYLION_REFERENCE_NOT_ATTESTED"


def test_missing_manual_olp_attestation_gates_wits_only():
    case = _fixture()
    case["digital_crown"]["manual_olp_verified"] = False
    metrics = _metrics(case)
    assert metrics["Wits"]["reason"] == "MANUAL_OLP_NOT_ATTESTED"
    assert metrics["ANS-Me"]["status"] == "NUMERIC_MATCH"


def test_missing_wits_landmark_gates_only_wits_and_never_fills_olp():
    case = _fixture()
    case["digital_crown"]["landmarks_px"].pop("olp")
    metrics = _metrics(case)
    assert metrics["Wits"]["reason"] == "MEASUREMENT_EVIDENCE_INCOMPLETE"
    assert metrics["Co-Gn"]["status"] == "NUMERIC_MATCH"


def test_invalid_facad_measurement_never_casts_or_invents_number():
    case = _fixture()
    case["facad"]["values_mm"]["ANS-Me"] = "1.2"
    metrics = _metrics(case)
    assert metrics["ANS-Me"]["status"] == "NOT_COMPARABLE"
    assert metrics["Wits"]["status"] == "NUMERIC_MATCH"


def test_invalid_dc_point_remains_not_comparable():
    case = _fixture()
    case["digital_crown"]["landmarks_px"]["a"] = [float("nan"), 7]
    metrics = _metrics(case)
    assert metrics["Wits"]["status"] == "NOT_COMPARABLE"
    assert metrics["Co-A"]["status"] == "NOT_COMPARABLE"
    assert metrics["Co-Gn"]["status"] == "NUMERIC_MATCH"


def test_local_cli_never_echoes_patient_or_source_identifiers(tmp_path, capsys):
    case = _fixture()
    case["facad"]["same_trace_case_id"] = "LOCAL_RESTRICTED_SYNTHETIC_ID"
    case["digital_crown"]["same_trace_case_id"] = "LOCAL_RESTRICTED_SYNTHETIC_ID"
    path = tmp_path / "local-only-no-upload.json"
    path.write_text(json.dumps(case), encoding="utf-8")
    assert main(["--input-json", str(path)]) == 0
    output = capsys.readouterr().out
    assert "LOCAL_RESTRICTED_SYNTHETIC_ID" not in output
    assert str(path) not in output
    assert HASH_IMAGE not in output
    assert json.loads(output)["measurements"]["Wits"]["status"] == "NUMERIC_MATCH"


def test_local_cli_invalid_json_refuses_without_leaking_path(tmp_path, capsys):
    path = tmp_path / "sensitive-case-name.json"
    path.write_text("not json!", encoding="utf-8")
    assert main(["--input-json", str(path)]) == 2
    output = capsys.readouterr().out
    assert str(path) not in output
    assert json.loads(output)["status"] == "INPUT_REJECTED"


def test_extreme_but_finite_declared_values_never_emit_infinite_delta():
    case = _fixture()
    case["digital_crown"]["landmarks_px"]["a"] = [-1, 0]
    case["digital_crown"]["landmarks_px"]["b"] = [0, 0]
    case["digital_crown"]["calibration"]["mm_per_pixel"] = 1e308
    case["facad"]["values_mm"]["Wits"] = 1e308
    result = compare_local_case(case)
    assert result["measurements"]["Wits"]["reason"] == "NUMERIC_DELTA_NONFINITE"
    # JSON must remain serializable without non-standard NaN / Infinity values.
    json.dumps(result, allow_nan=False)


def test_huge_json_integer_in_point_is_refused_without_overflow_exception():
    case = _fixture()
    case["digital_crown"]["landmarks_px"]["a"] = [10 ** 400, 0]
    result = compare_local_case(case)
    assert result["measurements"]["Wits"]["status"] == "NOT_COMPARABLE"
    assert result["measurements"]["Co-A"]["status"] == "NOT_COMPARABLE"
    assert result["measurements"]["Co-Gn"]["status"] == "NUMERIC_MATCH"
