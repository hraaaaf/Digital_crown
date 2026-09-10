import cv2
import numpy as np

from backend.services.calibration_service import CalibrationService


def _write_synthetic_ruler(path, *, with_ruler: bool) -> None:
    image = np.zeros((600, 800), dtype=np.uint8)
    if with_ruler:
        x = 620
        cv2.line(image, (x, 15), (x, 170), 255, 3)
        for y in (30, 55, 80, 105, 130, 155):
            cv2.line(image, (x - 18, y), (x + 18, y), 255, 3)
    assert cv2.imwrite(str(path), image)


def test_ruler_detection_returns_pixel_candidate_without_physical_scale(tmp_path):
    path = tmp_path / "ruler.png"
    _write_synthetic_ruler(path, with_ruler=True)

    service = CalibrationService()
    candidate = service.detect_ruler_candidate(str(path))

    assert candidate is not None
    assert candidate["method"] == "RULER_TICK_CANDIDATE_V1"
    assert candidate["requires_clinician_validation"] is True
    assert candidate["tick_count"] >= 5
    assert candidate["distance_px"] > 0
    assert len(candidate["p1"]) == 2
    assert len(candidate["p2"]) == 2
    assert "distance_mm" not in candidate
    assert "mm_per_pixel" not in candidate


def test_legacy_auto_ratio_api_fails_closed_even_when_candidate_exists(tmp_path):
    path = tmp_path / "ruler.png"
    _write_synthetic_ruler(path, with_ruler=True)

    service = CalibrationService()

    assert service.detect_ruler_candidate(str(path)) is not None
    assert service.detect_mm_per_pixel(str(path)) is None


def test_no_ruler_returns_no_candidate(tmp_path):
    path = tmp_path / "blank.png"
    _write_synthetic_ruler(path, with_ruler=False)

    service = CalibrationService()

    assert service.detect_ruler_candidate(str(path)) is None
