"""03B.4a: adversarial ruler detection without millimetre inference.

The Wikimedia JPEGs are public samples, NOT a clinical sensitivity/specificity
dataset. Film A contains a visible graduated ruler; B provides a negative case
for film-border artefacts. No automatic physical scale may be inferred.
"""
import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from backend.services.calibration_service import CalibrationService


def _ruler(width=140, height=340, x=70, start=30, step=28, count=9):
    image = np.zeros((height, width), dtype=np.uint8)
    last = start + (count - 1) * step
    image[max(0, start - 12):min(height, last + 13), x:x + 2] = 255
    for y in (start + i * step for i in range(count)):
        image[y, x + 2:min(width, x + 22)] = 255
    return image


def test_existing_six_tick_fixture_keeps_image_only_candidate():
    mask = np.zeros((140, 100), dtype=np.uint8)
    mask[:, 50:52] = 255
    for y in (20, 40, 60, 80, 100, 120):
        mask[y, 35:66] = 255
    candidate = CalibrationService()._candidate_from_threshold(mask)
    assert candidate is not None
    assert abs(candidate.axis_x_px - 50) < 4
    assert candidate.median_tick_spacing_px == 20
    payload = candidate.to_payload()
    assert payload["detector_method"] == "CLASSICAL_RULER_GEOMETRY_V2"
    assert payload["status"] == "CANDIDATE_UNVERIFIED"
    assert payload["mm_per_pixel"] is None
    assert payload["distance_mm"] is None
    assert payload["clinician_validated"] is False
    assert "profile_binding" not in payload


def test_one_sided_ruler_below_top_thirty_percent(tmp_path):
    image = _ruler(height=500, x=70, start=230, step=24, count=10)
    file = tmp_path / "late.png"
    assert cv2.imwrite(str(file), image)
    candidate = CalibrationService().detect_candidate(str(file))
    assert candidate is not None
    assert len(candidate.tick_positions_y_px) >= 8
    assert 59 <= candidate.axis_x_px <= 78
    assert min(candidate.tick_positions_y_px) > 190


@pytest.mark.parametrize("reverse", [False, True])
def test_both_contrast_polarities_without_assuming_scale(tmp_path, reverse):
    image = _ruler()
    if reverse:
        image = 255 - image
    file = tmp_path / "fiducial.png"
    assert cv2.imwrite(str(file), image)
    detector = CalibrationService()
    candidate = detector.detect_candidate(str(file))
    assert candidate is not None
    assert 18 < candidate.median_tick_spacing_px < 40
    assert detector.detect_mm_per_pixel(str(file)) is None


def test_irregular_ticks_and_film_borders_do_not_make_a_ruler():
    detector = CalibrationService()
    image = np.zeros((400, 160), dtype=np.uint8)
    image[:, 70:72] = 255
    for y in (20, 43, 67, 104, 133, 147, 205, 248, 280):
        image[y, 72:98] = 255
    assert detector._candidate_from_threshold(image) is None
    border = np.zeros((400, 160), dtype=np.uint8)
    border[:, 145:149] = 255
    assert detector._candidate_from_threshold(border) is None


def test_invalid_images_fail_closed(tmp_path):
    detector = CalibrationService()
    assert detector._candidate_from_threshold(np.zeros((140, 100), np.uint8)) is None
    assert detector._candidate_from_threshold(np.zeros((4, 5), np.uint8)) is None
    for image in (np.zeros((600, 600), np.uint8), np.full((600, 600), 255, np.uint8)):
        file = tmp_path / ("white.png" if image[0, 0] else "black.png")
        assert cv2.imwrite(str(file), image)
        assert detector.detect_candidate(str(file)) is None
    assert detector.detect_candidate(str(tmp_path / "does-not-exist.jpg")) is None


def test_multiple_equally_plausible_rulers_are_ambiguous():
    a = _ruler(width=420, x=75)
    b = _ruler(width=420, x=345)
    assert CalibrationService()._candidate_from_threshold(cv2.bitwise_or(a, b)) is None


def test_pinned_wikimedia_positive_and_negative_cases():
    directory = os.environ.get("DC_CEPH03B4A_RADIO_DIR")
    if not directory:
        pytest.skip("Public JPEG bytes staged only in 03B.4a CI")
    a, b = (Path(directory) / f"cephalo-{name}.jpg" for name in "AB")
    assert a.is_file() and b.is_file()
    detector = CalibrationService()
    candidate_a = detector.detect_candidate(str(a))
    candidate_b = detector.detect_candidate(str(b))
    assert candidate_a is not None
    assert 2000 <= candidate_a.axis_x_px <= 2100
    assert len(candidate_a.tick_positions_y_px) >= 8
    assert candidate_b is None
    # A visually detected ruler is NOT a validated physical scale.
    assert detector.detect_mm_per_pixel(str(a)) is None
    assert detector.detect_mm_per_pixel(str(b)) is None
