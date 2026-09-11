import numpy as np

from backend.services.calibration_service import CalibrationService
from backend.services.cephalo_calibration_candidate import CalibrationCandidate


def _synthetic_threshold() -> np.ndarray:
    image = np.zeros((140, 100), dtype=np.uint8)
    image[:, 50:52] = 255
    for y in (20, 40, 60, 80, 100, 120):
        image[y, 35:66] = 255
    return image


def test_threshold_detector_returns_geometry_only_candidate():
    service = CalibrationService()

    candidate = service._candidate_from_threshold(_synthetic_threshold())

    assert candidate is not None
    assert 49 <= candidate.axis_x_px <= 52
    assert len(candidate.tick_positions_y_px) >= 5
    assert candidate.median_tick_spacing_px > 0
    payload = candidate.to_payload()
    assert payload["status"] == "CANDIDATE_UNVERIFIED"
    assert payload["mm_per_pixel"] is None
    assert payload["distance_mm"] is None
    assert payload["clinician_validated"] is False


def test_threshold_detector_rejects_absence_of_ruler_geometry():
    service = CalibrationService()

    assert service._candidate_from_threshold(np.zeros((140, 100), dtype=np.uint8)) is None


def test_legacy_mm_per_pixel_entrypoint_never_promotes_candidate(monkeypatch):
    service = CalibrationService()
    candidate = CalibrationCandidate.from_ticks(
        axis_x_px=50,
        tick_positions_y_px=[20, 40, 60, 80, 100],
    )
    monkeypatch.setattr(service, "detect_candidate", lambda _path: candidate)

    assert service.detect_mm_per_pixel("ignored.png") is None
