"""API-boundary proofs for optional-clinician AUTO_VERIFIED calibration."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import ValidationError

from backend import models
from backend.routers import cephalo_auto_calibration, ia
from backend.routers.cephalo_auto_calibration import (
    AutoCalibrationRequest,
    auto_calibrate_analysis_with_provenance,
    confirm_auto_calibration_with_provenance,
)
from backend.services.cephalo_auto_calibration_gate import ValidatedFiducialProfile
from backend.services.cephalo_fiducial_profiles import FiducialProfileRegistry
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, build_cephalo_runtime_evidence_payload
from backend.services.cephalo_engine import CephaloEngine
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 20, 0, tzinfo=timezone.utc)
CASE_ID = "cephalo:auto-route-test"


class _Query:
    def __init__(self, analysis):
        self.analysis = analysis

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.analysis


class _DB:
    def __init__(self, analysis):
        self.analysis = analysis
        self.commits = 0
        self.rollbacks = 0
        self.refreshes = 0

    def query(self, model):
        assert model is models.CephaloAnalysis
        return _Query(self.analysis)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def refresh(self, obj):
        assert obj is self.analysis
        self.refreshes += 1


def _raw():
    return [
        {"id": name, "x": float(100 + index * 2), "y": float(120 + index * 3)}
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    ]


def _points(raw):
    return {item["id"]: (item["x"], item["y"]) for item in raw}


def _analysis(*, with_graph=True, with_candidate=True, with_profile_binding=True):
    raw = _raw()
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points(raw))
    graph = build_cephalo_runtime_evidence_payload(
        patient_id=7,
        image_record_id="radio.jpg",
        result=result,
        landmarks=raw,
        inference_mode="SOTA_ONNX_38",
        case_id=CASE_ID,
        recorded_at=NOW,
    )
    angles = result.model_dump()
    angles["vision_metadata"] = {"mode_inference": "SOTA_ONNX_38"}
    if with_graph:
        angles[EVIDENCE_GRAPH_KEY] = graph
    if with_candidate:
        candidate = {
            "status": "CANDIDATE_UNVERIFIED",
            "detector_method": "CLASSICAL_RULER_GEOMETRY_V1",
            "axis_x_px": 40.0,
            "tick_positions_y_px": [10.0, 35.0, 60.0, 85.0, 110.0],
            "median_tick_spacing_px": 25.0,
            "mm_per_pixel": None,
            "distance_mm": None,
            "clinician_validated": False,
        }
        if with_profile_binding:
            candidate["profile_binding"] = {
                "profile_id": "TEST_RULER",
                "profile_version": "1",
                "validation_reference": "test-fixture://validated-ruler-profile-v1",
            }
        angles["calibration_candidate"] = candidate
    return SimpleNamespace(
        id=41,
        patient_id=7,
        image_original_path="radio.jpg",
        angles_data=angles,
        landmarks_data=raw,
        calibration_data=None,
        is_calibrated=False,
        mm_per_pixel=None,
    )


def _profile_registry():
    return FiducialProfileRegistry(
        [
            ValidatedFiducialProfile(
                profile_id="TEST_RULER",
                version="1",
                known_tick_spacing_mm=5.0,
                min_ticks=5,
                max_spacing_deviation_ratio=0.05,
                validation_reference="test-fixture://validated-ruler-profile-v1",
            )
        ]
    )


def _call(monkeypatch, analysis, *, registry=None):
    db = _DB(analysis)
    monkeypatch.setattr(cephalo_auto_calibration, "assert_patient_access", lambda *_args: None)
    if registry is not None:
        monkeypatch.setattr(cephalo_auto_calibration, "validated_fiducial_profiles", registry)
    response = auto_calibrate_analysis_with_provenance(
        41,
        AutoCalibrationRequest(),
        db=db,
        current_user=SimpleNamespace(id=99),
    )
    return response, db


def test_auto_calibration_routes_are_unique():
    expected = {
        "/analyses/{analysis_id}/auto-calibrate": auto_calibrate_analysis_with_provenance,
        "/analyses/{analysis_id}/auto-calibration/confirm": confirm_auto_calibration_with_provenance,
    }
    for path, endpoint in expected.items():
        matches = [
            route
            for route in ia.router.routes
            if isinstance(route, APIRoute)
            and route.path == path
            and "POST" in (route.methods or set())
        ]
        assert len(matches) == 1
        assert matches[0].endpoint is endpoint


def test_request_cannot_select_a_physical_profile():
    with pytest.raises(ValidationError):
        AutoCalibrationRequest(profile_id="TEST_RULER", profile_version="1")


def test_empty_production_registry_fails_closed_without_mutation(monkeypatch):
    analysis = _analysis()
    before_angles = analysis.angles_data
    db = _DB(analysis)
    monkeypatch.setattr(cephalo_auto_calibration, "assert_patient_access", lambda *_args: None)
    monkeypatch.setattr(
        cephalo_auto_calibration,
        "validated_fiducial_profiles",
        FiducialProfileRegistry(),
    )

    with pytest.raises(HTTPException) as caught:
        auto_calibrate_analysis_with_provenance(
            41,
            AutoCalibrationRequest(),
            db=db,
            current_user=SimpleNamespace(id=99),
        )

    assert caught.value.status_code == 409
    assert "non validé" in caught.value.detail
    assert db.commits == 0
    assert db.rollbacks == 0
    assert analysis.is_calibrated is False
    assert analysis.mm_per_pixel is None
    assert analysis.angles_data is before_angles


def test_typed_graph_is_required_before_auto_calibration(monkeypatch):
    analysis = _analysis(with_graph=False)
    db = _DB(analysis)
    monkeypatch.setattr(cephalo_auto_calibration, "assert_patient_access", lambda *_args: None)
    monkeypatch.setattr(cephalo_auto_calibration, "validated_fiducial_profiles", _profile_registry())

    with pytest.raises(HTTPException) as caught:
        auto_calibrate_analysis_with_provenance(
            41,
            AutoCalibrationRequest(),
            db=db,
            current_user=SimpleNamespace(id=99),
        )

    assert caught.value.status_code == 409
    assert "graphe de preuve typé" in caught.value.detail
    assert db.commits == 0
    assert analysis.is_calibrated is False


def test_candidate_is_required_before_auto_calibration(monkeypatch):
    analysis = _analysis(with_candidate=False)
    db = _DB(analysis)
    monkeypatch.setattr(cephalo_auto_calibration, "assert_patient_access", lambda *_args: None)
    monkeypatch.setattr(cephalo_auto_calibration, "validated_fiducial_profiles", _profile_registry())

    with pytest.raises(HTTPException) as caught:
        auto_calibrate_analysis_with_provenance(
            41,
            AutoCalibrationRequest(),
            db=db,
            current_user=SimpleNamespace(id=99),
        )

    assert caught.value.status_code == 409
    assert "candidat" in caught.value.detail.lower()
    assert db.commits == 0
    assert analysis.is_calibrated is False


def test_candidate_without_server_bound_profile_fails_closed_even_when_registry_has_profile(monkeypatch):
    analysis = _analysis(with_profile_binding=False)
    before_angles = analysis.angles_data
    db = _DB(analysis)
    monkeypatch.setattr(cephalo_auto_calibration, "assert_patient_access", lambda *_args: None)
    monkeypatch.setattr(cephalo_auto_calibration, "validated_fiducial_profiles", _profile_registry())

    with pytest.raises(HTTPException) as caught:
        auto_calibrate_analysis_with_provenance(
            41,
            AutoCalibrationRequest(),
            db=db,
            current_user=SimpleNamespace(id=99),
        )

    assert caught.value.status_code == 409
    assert "identité fiduciale physique" in caught.value.detail
    assert db.commits == 0
    assert analysis.is_calibrated is False
    assert analysis.mm_per_pixel is None
    assert analysis.angles_data is before_angles


def test_profile_binding_reference_must_match_registry(monkeypatch):
    analysis = _analysis()
    analysis.angles_data["calibration_candidate"]["profile_binding"]["validation_reference"] = "forged://ref"
    before_angles = analysis.angles_data
    db = _DB(analysis)
    monkeypatch.setattr(cephalo_auto_calibration, "assert_patient_access", lambda *_args: None)
    monkeypatch.setattr(cephalo_auto_calibration, "validated_fiducial_profiles", _profile_registry())

    with pytest.raises(HTTPException) as caught:
        auto_calibrate_analysis_with_provenance(
            41,
            AutoCalibrationRequest(),
            db=db,
            current_user=SimpleNamespace(id=99),
        )

    assert caught.value.status_code == 409
    assert "Référence physique" in caught.value.detail
    assert db.commits == 0
    assert analysis.is_calibrated is False
    assert analysis.mm_per_pixel is None
    assert analysis.angles_data is before_angles


def test_auto_verified_success_does_not_require_clinician_confirmation(monkeypatch):
    analysis = _analysis()
    previous_graph = analysis.angles_data[EVIDENCE_GRAPH_KEY]
    response, db = _call(monkeypatch, analysis, registry=_profile_registry())

    assert response["calibration_state"] == "AUTO_VERIFIED"
    assert response["is_calibrated"] is True
    assert response["mm_per_pixel"] == pytest.approx(0.2)
    assert response["clinician_confirmation_required"] is False
    assert response["clinician_confirmation_recommended"] is True
    assert db.commits == 1
    assert db.refreshes == 1
    assert db.rollbacks == 0

    assert analysis.is_calibrated is True
    assert analysis.mm_per_pixel == pytest.approx(0.2)
    assert analysis.calibration_data["method"] == "AUTO_FIDUCIAL_PROFILE"
    assert analysis.calibration_data["state"] == "AUTO_VERIFIED"
    assert analysis.calibration_data["triggered_by"] == "99"
    assert analysis.calibration_data["provenance"]["clinician_confirmed"] is False

    graph = analysis.angles_data[EVIDENCE_GRAPH_KEY]
    assert graph["revision"] == previous_graph["revision"] + 1
    assert graph["revision_reason"] == "AUTO_CALIBRATION"
    assert graph["landmarks"] == previous_graph["landmarks"]
    assert graph["constructions"] == previous_graph["constructions"]
    assert all(item["availability_status"] == "AVAILABLE" for item in graph["measurements"])


def test_optional_confirmation_changes_only_audit_state_not_ratio_or_values(monkeypatch):
    analysis = _analysis()
    _, db = _call(monkeypatch, analysis, registry=_profile_registry())
    auto_graph = analysis.angles_data[EVIDENCE_GRAPH_KEY]
    before_ratio = analysis.mm_per_pixel
    before_values = [item["value"] for item in auto_graph["measurements"]]
    before_landmarks = auto_graph["landmarks"]
    before_constructions = auto_graph["constructions"]

    response = confirm_auto_calibration_with_provenance(
        41,
        db=db,
        current_user=SimpleNamespace(id=99),
    )

    assert response["calibration_state"] == "CLINICIAN_CONFIRMED"
    assert response["clinician_confirmation_required"] is False
    assert response["clinician_confirmation_recommended"] is False
    assert response["mm_per_pixel"] == pytest.approx(before_ratio)
    assert db.commits == 2
    assert db.refreshes == 2
    assert db.rollbacks == 0

    assert analysis.mm_per_pixel == pytest.approx(before_ratio)
    assert analysis.calibration_data["state"] == "CLINICIAN_CONFIRMED"
    assert analysis.calibration_data["provenance"]["clinician_confirmed"] is False
    assert analysis.calibration_data["confirmation"]["confirmed_by"] == "99"
    graph = analysis.angles_data[EVIDENCE_GRAPH_KEY]
    assert graph["revision"] == auto_graph["revision"] + 1
    assert graph["revision_reason"] == "CLINICIAN_CALIBRATION_CONFIRMATION"
    assert graph["landmarks"] == before_landmarks
    assert graph["constructions"] == before_constructions
    assert [item["value"] for item in graph["measurements"]] == before_values
    source = next(item for item in graph["sources"] if item["kind"] == "calibration")
    assert source["quality_status"] == "CLINICIAN_CONFIRMED_AUTO_FIDUCIAL_PROFILE"
    assert source["metadata"]["clinician_confirmed"] is True
    assert source["metadata"]["confirmed_by"] == "99"
