"""Safety contracts for clinician-audited landmark correction evidence."""
from datetime import datetime, timezone

import pytest

from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_landmark_correction_evidence import (
    landmark_submission_changed,
    rebuild_evidence_after_landmark_edit,
)
from backend.services.cephalo_runtime_evidence import (
    CephaloRuntimeEvidenceError,
    build_cephalo_runtime_evidence_payload,
)
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 15, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 10, 15, 5, tzinfo=timezone.utc)
CASE_ID = "cephalo:landmark-audit-test"


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _initial(raw=None):
    raw = raw or _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    return build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )


def _edit(previous, raw, *, clinician_id="99", at=NOW, ratio=None):
    result = CephaloEngine(mm_per_pixel=ratio).calculate_metrics(_points(raw))
    return rebuild_evidence_after_landmark_edit(
        previous_payload=previous,
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        runtime_landmarks=raw,
        clinician_id=clinician_id,
        validated_at=at,
    )


def _landmark(payload, landmark_id, *, origin=None):
    matches = [
        item
        for item in payload["landmarks"]
        if item["landmark_id"] == landmark_id
        and (origin is None or item["origin"] == origin)
    ]
    assert len(matches) == 1
    return matches[0]


def test_unchanged_submission_is_a_true_noop():
    previous = _initial()
    assert landmark_submission_changed(previous, _raw()) is False
    payload = _edit(previous, _raw())
    assert payload == previous
    assert payload["revision"] == 1
    assert "revision_reason" not in payload


def test_first_srpose_edit_preserves_original_and_binds_clinician():
    previous = _initial()
    raw = _raw()
    target = next(item for item in raw if item["id"] == "A")
    original = (target["x"], target["y"])
    target["x"] += 4.0

    assert landmark_submission_changed(previous, raw) is True
    payload = _edit(previous, raw)

    assert payload["revision"] == 2
    assert payload["revision_reason"] == "LANDMARK_EDIT"
    corrected = _landmark(payload, "A", origin="MANUAL_CORRECTED")
    assert corrected["original_auto_x"] == original[0]
    assert corrected["original_auto_y"] == original[1]
    assert corrected["validated_by"] == "99"
    assert datetime.fromisoformat(corrected["validated_at"].replace("Z", "+00:00")) == NOW
    assert corrected["evidence_status"] == "CLINICIAN_VALIDATED"
    assert corrected["evidence_id"] in payload["current_landmark_refs"]

    auto = _landmark(payload, "A", origin="SRPOSE38_AUTO")
    assert (auto["x"], auto["y"]) == original
    assert auto["evidence_id"] not in payload["current_landmark_refs"]


def test_second_correction_keeps_same_original_auto_coordinates():
    raw1 = _raw()
    a1 = next(item for item in raw1 if item["id"] == "A")
    original = (a1["x"], a1["y"])
    a1["x"] += 4.0
    revision2 = _edit(_initial(), raw1)

    raw2 = [dict(item) for item in raw1]
    a2 = next(item for item in raw2 if item["id"] == "A")
    a2["x"] += 3.0
    revision3 = _edit(revision2, raw2, at=LATER)

    assert revision3["revision"] == 3
    corrected = _landmark(revision3, "A", origin="MANUAL_CORRECTED")
    assert (corrected["original_auto_x"], corrected["original_auto_y"]) == original
    assert datetime.fromisoformat(corrected["validated_at"].replace("Z", "+00:00")) == LATER
    assert revision3["history"][-1]["revision"] == 2


def test_omitted_required_point_is_not_reused_from_auto_history():
    previous = _initial()
    without_a = [item for item in _raw() if item["id"] != "A"]
    revision2 = _edit(previous, without_a)

    assert all(
        not ref.endswith(":A")
        for ref in revision2["current_landmark_refs"]
    )
    by_definition = {item["definition_id"]: item for item in revision2["constructions"]}
    assert by_definition["CRANIOM_A_TO_N_VERTICAL_V1"]["availability_status"] == "NOT_COMPUTABLE"
    assert by_definition["CRANIOM_AB_PRIME_V1"]["availability_status"] == "NOT_COMPUTABLE"
    assert "A" in by_definition["CRANIOM_A_TO_N_VERTICAL_V1"]["missing_landmark_ids"]

    without_a_2 = [dict(item) for item in without_a]
    b = next(item for item in without_a_2 if item["id"] == "B")
    b["x"] += 2.0
    revision3 = _edit(revision2, without_a_2, at=LATER)
    by_definition3 = {item["definition_id"]: item for item in revision3["constructions"]}
    assert by_definition3["CRANIOM_A_TO_N_VERTICAL_V1"]["availability_status"] == "NOT_COMPUTABLE"
    assert all(
        not ref.endswith(":A")
        for ref in revision3["current_landmark_refs"]
    )


def test_edit_rejects_duplicate_and_nonfinite_runtime_landmarks():
    previous = _initial()
    duplicate = _raw()
    duplicate.append(dict(duplicate[0]))
    with pytest.raises(CephaloRuntimeEvidenceError, match="Duplicate runtime landmark id"):
        landmark_submission_changed(previous, duplicate)

    nonfinite = _raw()
    nonfinite[0] = {**nonfinite[0], "x": float("nan")}
    with pytest.raises(CephaloRuntimeEvidenceError, match="must be finite"):
        landmark_submission_changed(previous, nonfinite)


def test_actual_edit_requires_clinician_and_timezone_aware_timestamp():
    raw = _raw()
    raw[4] = {**raw[4], "x": raw[4]["x"] + 1.0}
    with pytest.raises(CephaloRuntimeEvidenceError, match="requires clinician_id"):
        _edit(_initial(), raw, clinician_id="")
    with pytest.raises(CephaloRuntimeEvidenceError, match="timezone-aware"):
        _edit(_initial(), raw, at=datetime(2026, 9, 10, 15, 0))


def test_actual_edit_rejects_stale_downstream_clinical_evidence():
    previous = {**_initial(), "findings": [{"finding_id": "stale"}]}
    raw = _raw()
    raw[4] = {**raw[4], "x": raw[4]["x"] + 1.0}
    with pytest.raises(CephaloRuntimeEvidenceError, match="downstream clinical evidence"):
        _edit(previous, raw)


def test_calibration_source_and_refs_survive_landmark_revision():
    raw = _raw()
    base = _initial(raw)
    calibrated_result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(raw))
    calibrated = rebuild_evidence_after_manual_calibration(
        previous_payload=base,
        patient_id=7,
        image_record_id="radio.jpg",
        result=calibrated_result,
        runtime_landmarks=raw,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="99",
        calibrated_at=NOW,
    )
    calibration = next(item for item in calibrated["sources"] if item["kind"] == "calibration")

    edited = [dict(item) for item in raw]
    a = next(item for item in edited if item["id"] == "A")
    a["x"] += 1.0
    payload = _edit(calibrated, edited, at=LATER, ratio=0.2)

    assert any(item["evidence_id"] == calibration["evidence_id"] for item in payload["sources"])
    calibrated_measurements = [
        item for item in payload["measurements"] if item["requires_calibration"]
    ]
    independent_measurements = [
        item for item in payload["measurements"] if not item["requires_calibration"]
    ]
    assert len(calibrated_measurements) == 4
    assert all(
        item["calibration_ref"] == calibration["evidence_id"]
        for item in calibrated_measurements
    )
    assert len(independent_measurements) == 2
    assert {item["method_id"] for item in independent_measurements} == {
        "CRANIOM_U1_FRANKFORT_DEG_V1",
        "CRANIOM_L1_DOWNS_DEG_V1",
    }
    assert all(item["calibration_ref"] is None for item in independent_measurements)


def test_calibration_preserves_explicit_current_set_after_point_omission():
    without_a = [item for item in _raw() if item["id"] != "A"]
    revision2 = _edit(_initial(), without_a)
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(without_a))
    calibrated = rebuild_evidence_after_manual_calibration(
        previous_payload=revision2,
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        runtime_landmarks=without_a,
        p1={"x": 0.0, "y": 0.0},
        p2={"x": 0.0, "y": 50.0},
        distance_mm=10.0,
        clinician_id="99",
        calibrated_at=LATER,
    )

    assert calibrated["current_landmark_refs"] == revision2["current_landmark_refs"]
    assert all(not ref.endswith(":A") for ref in calibrated["current_landmark_refs"])

    edited = [dict(item) for item in without_a]
    b = next(item for item in edited if item["id"] == "B")
    b["x"] += 1.0
    revision4 = _edit(calibrated, edited, at=LATER, ratio=0.2)
    by_definition = {item["definition_id"]: item for item in revision4["constructions"]}
    assert by_definition["CRANIOM_A_TO_N_VERTICAL_V1"]["availability_status"] == "NOT_COMPUTABLE"
    assert all(not ref.endswith(":A") for ref in revision4["current_landmark_refs"])
