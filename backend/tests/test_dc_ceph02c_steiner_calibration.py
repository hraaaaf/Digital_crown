"""DC-CEPH-02C regression: no Steiner linear identity loss on calibration.

Uses the real typed backend and only synthetic 38-landmark fixtures. This
is a safety regression, not a proof of clinical numerical concordance.
"""
from copy import deepcopy

import pytest

from backend.repositories.cephalo_repository import _canonicalize_evidence_projection
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import rebuild_evidence_after_landmark_edit
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, CephaloRuntimeEvidenceError
from backend.tests.test_cephalo_runtime_chain import _raw, _points, _initial_graph, LATEST
from backend.tests.test_dc_ceph02b_runtime_matrix import _matrix, _read

METHOD_TO_CANONICAL = {
    "STEINER_U1_NA_CANONICAL_MM_V2": "M_U1_NA_MM_V1",
    "STEINER_L1_NB_CANONICAL_MM_V2": "M_L1_NB_MM_V1",
    "STEINER_POG_NB_CANONICAL_MM_V2": "M_POG_NB_MM_V1",
    "STEINER_L1_DLINE_CANONICAL_MM_V2": "M_L1_DLINE_MM_V1",
}


def _before():
    points = _raw()
    previous = _canonicalize_evidence_projection({
        EVIDENCE_GRAPH_KEY: _initial_graph(points),
    })[EVIDENCE_GRAPH_KEY]
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(points))
    return points, previous, result


def _calibrate(previous, points, result):
    return rebuild_evidence_after_manual_calibration(
        previous_payload=previous,
        patient_id=7,
        image_record_id="radio-r2.jpg",
        result=result,
        runtime_landmarks=points,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="synthetic-operator",
        calibrated_at=LATEST,
    )


def test_calibration_preserves_all_four_source_locked_steiner_linear_methods_and_refs():
    raw, previous, result = _before()
    original = deepcopy(previous)
    before_methods = {
        m["method_id"]: m for m in previous["measurements"]
        if m["method_id"] in METHOD_TO_CANONICAL
    }
    assert set(before_methods) == set(METHOD_TO_CANONICAL)
    assert all(m["availability_status"] == "NOT_COMPUTABLE" for m in before_methods.values())
    after = _calibrate(previous, raw, result)
    assert previous == original, "A calibration transition may not mutate prior history"
    assert after["revision"] == original["revision"] + 1
    assert after["revision_reason"] == "MANUAL_CALIBRATION"
    assert len(after["history"]) == len(original["history"]) + 1
    by_method = {
        m["method_id"]: m for m in after["measurements"]
        if m["method_id"] in METHOD_TO_CANONICAL
    }
    assert set(by_method) == set(METHOD_TO_CANONICAL)
    assert sum(m["method_id"] in METHOD_TO_CANONICAL for m in after["measurements"]) == 4
    current_calibrations = [s for s in after["sources"] if s["kind"] == "calibration"]
    assert len(current_calibrations) == 1
    cal_ref = current_calibrations[0]["evidence_id"]
    construction_ids = {c["construction_id"] for c in after["constructions"]}
    assert len(construction_ids) == len(after["constructions"])
    for method, old in before_methods.items():
        new = by_method[method]
        assert new["measurement_id"] != old["measurement_id"]
        assert len(new["construction_refs"]) == 1
        assert new["construction_refs"][0] in construction_ids
        assert new["construction_refs"][0] not in old["construction_refs"]
        assert new["requires_calibration"] is True
        assert new["unit"] == "mm"
        assert new["availability_status"] in {"AVAILABLE", "NOT_COMPUTABLE", "INVALID"}
        if new["availability_status"] == "AVAILABLE":
            assert new["value"] is not None
            assert new["calibration_ref"] == cal_ref
        else:
            assert new["value"] is None
            assert new["calibration_ref"] is None
        assert cal_ref in new["evidence_refs"]
    projected = _read(after, result)
    status, count = _matrix(projected)
    assert count["NOT_EXPOSED"] == 4, "Only pre-existing source-blocked IDs may remain unexposed"
    for canonical_id in METHOD_TO_CANONICAL.values():
        assert status[canonical_id] != "NOT_EXPOSED"
    assert after["normative_evaluations"] == []
    assert after["diagnoses"] == []
    assert after["final_plans"] == []

    corrected = [dict(item) for item in raw]
    next(p for p in corrected if p["id"] == "B")["x"] += 1.0
    corrected_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(corrected))
    next_rev = rebuild_evidence_after_landmark_edit(
        previous_payload=after,
        patient_id=7,
        image_record_id="radio-r2.jpg",
        result=corrected_result,
        runtime_landmarks=corrected,
        clinician_id="synthetic-operator",
        validated_at=LATEST,
    )
    next_status, _ = _matrix(_read(next_rev, corrected_result))
    assert all(next_status[canonical_id] != "NOT_EXPOSED"
               for canonical_id in METHOD_TO_CANONICAL.values())


def test_calibration_does_not_resurrect_missing_prior_steiner_linear_method():
    raw, previous, result = _before()
    omitted = "STEINER_L1_NB_CANONICAL_MM_V2"
    previous["measurements"] = [
        m for m in previous["measurements"] if m["method_id"] != omitted
    ]
    assert sum(m["method_id"] == omitted for m in previous["measurements"]) == 0
    after = _calibrate(previous, raw, result)
    assert not any(m["method_id"] == omitted for m in after["measurements"])
    other = set(METHOD_TO_CANONICAL) - {omitted}
    assert other.issubset({m["method_id"] for m in after["measurements"]})


def test_unknown_prior_steiner_linear_method_fails_closed_without_promotion():
    raw, previous, result = _before()
    target = next(m for m in previous["measurements"]
                  if m["method_id"] == "STEINER_L1_NB_CANONICAL_MM_V2")
    target["method_id"] = "UNVERIFIED_VENDOR_FAKE_LINEAR_METHOD"
    with pytest.raises(CephaloRuntimeEvidenceError, match="Unknown prior Steiner linear method"):
        _calibrate(previous, raw, result)
