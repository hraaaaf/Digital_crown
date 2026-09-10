"""Service-boundary contracts for typed cephalometric landmark refinements."""
from types import SimpleNamespace

import pytest

from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.cephalo_service import CephaloService
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _graph(raw=None):
    raw = raw or _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    return build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id="cephalo:service-refinement",
    )


class _Repo:
    def __init__(self, analysis):
        self.analysis = analysis
        self.update_calls = []

    def get_by_id(self, analysis_id):
        assert analysis_id == self.analysis.id
        return self.analysis

    def update(self, analysis_id, landmarks_data, angles_data, mm_per_pixel=None):
        self.update_calls.append((analysis_id, landmarks_data, angles_data, mm_per_pixel))
        self.analysis.landmarks_data = landmarks_data
        self.analysis.angles_data = angles_data
        self.analysis.mm_per_pixel = mm_per_pixel
        return self.analysis


def _service(*, typed=True, raw=None, mm_per_pixel=None):
    raw = raw or _raw()
    angles = {"legacy": "keep"}
    if typed:
        angles[EVIDENCE_GRAPH_KEY] = _graph(raw)
    analysis = SimpleNamespace(
        id=42,
        patient_id=7,
        image_original_path="radio.jpg",
        angles_data=angles,
        landmarks_data=raw,
        mm_per_pixel=mm_per_pixel,
        is_calibrated=mm_per_pixel is not None,
        patient=None,
    )
    service = CephaloService.__new__(CephaloService)
    service.db = None
    service.repo = _Repo(analysis)
    return service


def test_typed_changed_landmark_requires_authenticated_clinician_before_persistence():
    service = _service()
    edited = _raw()
    edited[4] = {**edited[4], "x": edited[4]["x"] + 2.0}

    with pytest.raises(ValueError, match="identité du praticien"):
        service.refine_analysis(
            analysis_id=42,
            landmarks=edited,
            ai_diagnostic={"author": "practitioner"},
        )

    assert service.repo.update_calls == []


def test_typed_unchanged_landmarks_do_not_create_fake_edit_revision():
    service = _service()
    previous = service.repo.analysis.angles_data[EVIDENCE_GRAPH_KEY]

    result = service.refine_analysis(
        analysis_id=42,
        landmarks=_raw(),
        ai_diagnostic={"author": "practitioner"},
    )

    persisted = service.repo.update_calls[0][2][EVIDENCE_GRAPH_KEY]
    assert persisted == previous
    assert persisted["revision"] == 1
    assert "revision_reason" not in persisted
    assert result["analysis_id"] == 42


def test_typed_refinement_cannot_bypass_calibration_provenance():
    service = _service(mm_per_pixel=None)

    with pytest.raises(ValueError, match="endpoint de calibration"):
        service.refine_analysis(
            analysis_id=42,
            landmarks=_raw(),
            ai_diagnostic={"author": "practitioner"},
            mm_per_pixel=0.2,
        )

    assert service.repo.update_calls == []


def test_legacy_analysis_is_not_backfilled_with_invented_evidence_provenance():
    service = _service(typed=False)

    service.refine_analysis(
        analysis_id=42,
        landmarks=_raw(),
        ai_diagnostic={"author": "practitioner"},
        clinician_id="99",
    )

    persisted = service.repo.update_calls[0][2]
    assert EVIDENCE_GRAPH_KEY not in persisted
