"""Integration tests proving CephaloService persists, but does not expose, typed evidence."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.cephalo_service import CephaloService
from backend.services.sota_vision_service import SOTA_LANDMARKS_MAPPING

NOW = datetime(2026, 9, 10, 13, 30, tzinfo=timezone.utc)


def _engine_points():
    return {
        "S": (10.0, 10.0), "N": (20.0, 10.0), "Po": (0.0, 20.0), "Or": (20.0, 20.0),
        "A": (24.0, 28.0), "B": (22.0, 38.0), "Go": (5.0, 50.0), "Me": (25.0, 55.0),
        "U1a": (20.0, 25.0), "U1i": (24.0, 35.0), "L1a": (20.0, 48.0), "L1i": (23.0, 38.0),
    }


def _result():
    return CephaloEngine(mm_per_pixel=None).calculate_metrics(_engine_points())


def _srpose_points():
    coords = {
        name: (float(100 + index * 2), float(120 + index * 3))
        for index, name in SOTA_LANDMARKS_MAPPING.items()
    }
    coords.update({
        key: value
        for key, value in _engine_points().items()
        if key in coords
    })
    # Typed angular geometry uses canonical SRPose landmark names while the
    # legacy engine fixture uses U1a/U1i and L1a/L1i. Keep both systems bound
    # to the same physical points so integration parity is meaningful.
    coords["U1_apex"] = _engine_points()["U1a"]
    coords["U1_incisal"] = _engine_points()["U1i"]
    coords["L1_apex"] = _engine_points()["L1a"]
    coords["L1_incisal"] = _engine_points()["L1i"]
    return [
        {"id": name, "x": x, "y": y}
        for name, (x, y) in coords.items()
    ]


class _Repo:
    def __init__(self, existing=None):
        self.existing = existing
        self.persisted = None

    def get_by_id(self, _analysis_id):
        return self.existing

    def create(self, _patient_id, _path, _landmarks, results, mm_per_pixel=None):
        self.persisted = results
        return SimpleNamespace(id=42, is_calibrated=False, mm_per_pixel=mm_per_pixel)

    def update(self, _analysis_id, _landmarks, results, mm_per_pixel=None):
        self.persisted = results
        return SimpleNamespace(
            id=42,
            is_calibrated=False,
            mm_per_pixel=mm_per_pixel,
            landmarks_data=_landmarks,
        )


def test_new_analysis_persists_evidence_without_changing_public_result(monkeypatch):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = CephaloService(db)
    repo = _Repo()
    service.repo = repo

    monkeypatch.setattr(
        "backend.services.cephalo_service.vision_engine.predict_landmarks",
        lambda _path: {
            "landmarks": _srpose_points(),
            "mode_inference": "SOTA_ONNX_38",
            "warning": None,
            "processing_time_ms": 1.0,
        },
    )
    monkeypatch.setattr(
        "backend.services.calibration_service.calibration_service.detect_mm_per_pixel",
        lambda _path: None,
    )
    monkeypatch.setattr(
        "backend.services.cephalo_service.cephalo_engine.calculate_metrics",
        lambda *_args, **_kwargs: _result(),
    )

    response = service.process_new_radio(7, "/tmp/radio.jpg", "api/static/radio.jpg")

    assert EVIDENCE_GRAPH_KEY in repo.persisted
    graph = repo.persisted[EVIDENCE_GRAPH_KEY]
    assert graph["revision"] == 1
    assert graph["history"] == []

    craniom_angular = [
        item for item in graph["measurements"]
        if item["analysis_id"] == "CRANIOM" and not item["requires_calibration"]
    ]
    assert {item["method_id"] for item in craniom_angular} == {
        "CRANIOM_U1_FRANKFORT_DEG_V1",
        "CRANIOM_L1_DOWNS_DEG_V1",
        "CRANIOM_INTERINCISAL_DEG_V1",
    }

    steiner = [item for item in graph["measurements"] if item["analysis_id"] == "STEINER"]
    assert {item["method_id"] for item in steiner} == {
        "STEINER_SNA_DEG_V1",
        "STEINER_SNB_DEG_V1",
        "STEINER_ANB_DEG_V1",
        "STEINER_U1_NA_DEG_V1",
        "STEINER_L1_NB_DEG_V1",
    }
    assert EVIDENCE_GRAPH_KEY not in response["results"]


def test_refine_replaces_current_manual_revision_but_preserves_original_auto(monkeypatch):
    initial_db = MagicMock()
    initial_db.query.return_value.filter.return_value.first.return_value = None
    initial_service = CephaloService(initial_db)
    initial_repo = _Repo()
    initial_service.repo = initial_repo

    monkeypatch.setattr(
        "backend.services.cephalo_service.vision_engine.predict_landmarks",
        lambda _path: {
            "landmarks": _srpose_points(),
            "mode_inference": "SOTA_ONNX_38",
            "warning": None,
            "processing_time_ms": 1.0,
        },
    )
    monkeypatch.setattr(
        "backend.services.calibration_service.calibration_service.detect_mm_per_pixel",
        lambda _path: None,
    )
    monkeypatch.setattr(
        "backend.services.cephalo_service.cephalo_engine.calculate_metrics",
        lambda *_args, **_kwargs: _result(),
    )
    initial_service.process_new_radio(7, "/tmp/radio.jpg", "api/static/radio.jpg")

    existing = SimpleNamespace(
        patient_id=7,
        patient=None,
        image_original_path="api/static/radio.jpg",
        angles_data=initial_repo.persisted,
        mm_per_pixel=None,
        is_calibrated=False,
        calibration_data=None,
        created_at=NOW,
    )
    service = CephaloService(MagicMock())
    repo = _Repo(existing=existing)
    service.repo = repo
    monkeypatch.setattr(
        "backend.services.cephalo_service.bilan_ortho_engine.generate_bilan",
        lambda *_args, **_kwargs: {},
    )

    manual = [
        {"id": key, "x": x + 1.0, "y": y}
        for key, (x, y) in _engine_points().items()
    ]
    response = service.refine_analysis(42, manual, clinician_id="99")

    payload = repo.persisted[EVIDENCE_GRAPH_KEY]
    assert payload["revision"] == 2
    assert len(payload["history"]) == 1
    assert payload["history"][0]["revision"] == 1
    assert len([x for x in payload["landmarks"] if x["origin"] == "SRPOSE38_AUTO"]) == 38

    srpose_ids = set(SOTA_LANDMARKS_MAPPING.values())
    expected_corrected_ids = {item["id"] for item in manual if item["id"] in srpose_ids}
    expected_manual_ids = {item["id"] for item in manual if item["id"] not in srpose_ids}

    corrected = [x for x in payload["landmarks"] if x["origin"] == "MANUAL_CORRECTED"]
    manual_only = [x for x in payload["landmarks"] if x["origin"] == "MANUAL"]
    assert {x["landmark_id"] for x in corrected} == expected_corrected_ids
    assert {x["landmark_id"] for x in manual_only} == expected_manual_ids
    assert all(x["validated_by"] == "99" for x in corrected + manual_only)
    assert EVIDENCE_GRAPH_KEY not in response["results"]
