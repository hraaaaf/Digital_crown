from types import SimpleNamespace

import backend.services.cephalo_service as cephalo_service_module
from backend.services.cephalo_calibration_candidate import CalibrationCandidate
from backend.services.cephalo_service import CephaloService


class _FakeQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return None


class _FakeDB:
    def query(self, *_args, **_kwargs):
        return _FakeQuery()


class _FakeRepo:
    def __init__(self):
        self.created = None

    def create(self, patient_id, db_path, pts, persisted_data, mm_per_pixel=None):
        self.created = {
            "patient_id": patient_id,
            "db_path": db_path,
            "pts": pts,
            "persisted_data": persisted_data,
            "mm_per_pixel": mm_per_pixel,
        }
        return SimpleNamespace(id=77, is_calibrated=False, mm_per_pixel=None)


def test_new_analysis_persists_candidate_without_physical_scale(monkeypatch):
    landmarks = [{"id": "S", "x": 10.0, "y": 20.0}]
    monkeypatch.setattr(
        cephalo_service_module.vision_engine,
        "predict_landmarks",
        lambda _path: {
            "landmarks": landmarks,
            "mode_inference": "TEST",
            "warning": None,
            "processing_time_ms": 1,
        },
    )

    candidate = CalibrationCandidate.from_ticks(
        axis_x_px=50,
        tick_positions_y_px=[20, 40, 60, 80, 100],
    )
    from backend.services.calibration_service import calibration_service

    monkeypatch.setattr(calibration_service, "detect_candidate", lambda _path: candidate)
    monkeypatch.setattr(
        cephalo_service_module.cephalo_engine,
        "calculate_metrics",
        lambda *_args, **_kwargs: SimpleNamespace(model_dump=lambda: {"ai_narrative": {}}),
    )
    monkeypatch.setattr(
        cephalo_service_module,
        "build_cephalo_runtime_evidence_payload",
        lambda **_kwargs: {"typed": "unverified"},
    )

    service = CephaloService(_FakeDB())
    fake_repo = _FakeRepo()
    service.repo = fake_repo

    response = service.process_new_radio(12, "radio.png", "stored/radio.png")

    assert fake_repo.created is not None
    assert fake_repo.created["mm_per_pixel"] is None
    persisted = fake_repo.created["persisted_data"]
    assert persisted["calibration_status"] == "candidate_unverified"
    assert persisted["calibration_candidate"]["mm_per_pixel"] is None
    assert persisted["calibration_candidate"]["distance_mm"] is None
    assert persisted["calibration_candidate"]["clinician_validated"] is False
    assert response["is_calibrated"] is False
    assert response["mm_per_pixel"] is None
    assert response["calibration_candidate"]["status"] == "CANDIDATE_UNVERIFIED"
