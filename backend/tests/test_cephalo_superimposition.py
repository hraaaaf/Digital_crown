import math
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import pytest

from backend.services.cephalo_superimposition import (
    ImageROI,
    RegistrationConfig,
    SuperimpositionError,
    _validate_similarity_matrix,
    register_acb_similarity,
    warp_moving_to_reference,
)


def _feature_canvas(size: int = 512) -> np.ndarray:
    image = np.zeros((size, size), dtype=np.uint8)
    for idx, (x, y) in enumerate(
        [(110, 120), (170, 145), (235, 110), (315, 150), (380, 125),
         (130, 225), (205, 255), (285, 220), (365, 265),
         (125, 350), (215, 375), (305, 345), (390, 385)]
    ):
        cv2.circle(image, (x, y), 7 + (idx % 4), 180 + (idx % 3) * 25, 2)
        cv2.line(image, (x - 12, y + 15), (x + 17, y - 9), 120 + idx * 5, 2)
    cv2.putText(image, "ACB", (155, 315), cv2.FONT_HERSHEY_SIMPLEX, 1.3, 255, 3, cv2.LINE_AA)
    cv2.rectangle(image, (90, 85), (420, 420), 90, 2)
    return image


def _similarity_matrix(angle_degrees: float, scale: float, tx: float, ty: float) -> np.ndarray:
    theta = math.radians(angle_degrees)
    a = scale * math.cos(theta)
    b = scale * math.sin(theta)
    return np.array([[a, -b, tx], [b, a, ty]], dtype=np.float64)


def test_identity_registration_is_reproducible_and_never_claims_clinical_validation():
    image = _feature_canvas()
    roi = ImageROI(70, 70, 380, 380)

    first = register_acb_similarity(image, image.copy(), reference_roi=roi, moving_roi=roi)
    second = register_acb_similarity(image, image.copy(), reference_roi=roi, moving_roi=roi)

    np.testing.assert_allclose(np.asarray(first.matrix), np.eye(2, 3), atol=1e-5)
    np.testing.assert_allclose(np.asarray(second.matrix), np.asarray(first.matrix), atol=1e-8)
    metadata = first.to_metadata()
    assert metadata["quality_status"] == "ENGINE_ESTIMATE_ONLY"
    assert metadata["clinically_validated"] is False
    assert metadata["transform_direction"] == "moving_to_reference"
    assert metadata["algorithm"]["ratio_test"] == 0.7


def test_known_similarity_transform_is_recovered_as_moving_to_reference():
    reference = _feature_canvas()
    forward = _similarity_matrix(angle_degrees=3.0, scale=1.02, tx=8.0, ty=-6.0)
    moving = cv2.warpAffine(reference, forward, (512, 512), flags=cv2.INTER_LINEAR)
    roi = ImageROI(55, 55, 405, 405)

    result = register_acb_similarity(
        reference,
        moving,
        reference_roi=roi,
        moving_roi=roi,
    )
    expected_inverse = cv2.invertAffineTransform(forward)

    # This is a synthetic numerical test, not a clinical accuracy threshold.
    np.testing.assert_allclose(np.asarray(result.matrix), expected_inverse, atol=0.12)
    assert result.good_match_count >= 2
    assert result.inlier_count >= 2


def test_warp_is_derived_and_source_is_immutable():
    reference = _feature_canvas()
    moving = reference.copy()
    original = moving.copy()
    roi = ImageROI(70, 70, 380, 380)
    result = register_acb_similarity(reference, moving, reference_roi=roi, moving_roi=roi)

    warped = warp_moving_to_reference(moving, result)

    assert np.array_equal(moving, original)
    assert np.array_equal(warped, reference)


def test_blank_stable_region_fails_closed():
    blank = np.zeros((512, 512), dtype=np.uint8)
    roi = ImageROI(70, 70, 380, 380)

    with pytest.raises(SuperimpositionError, match="detectable SIFT features"):
        register_acb_similarity(blank, blank, reference_roi=roi, moving_roi=roi)


@pytest.mark.parametrize(
    "roi",
    [
        ImageROI(-1, 0, 100, 100),
        ImageROI(0, -1, 100, 100),
        ImageROI(0, 0, 0, 100),
        ImageROI(0, 0, 100, 0),
        ImageROI(450, 0, 100, 100),
        ImageROI(0, 450, 100, 100),
    ],
)
def test_invalid_roi_fails_closed(roi):
    image = _feature_canvas()
    valid = ImageROI(70, 70, 380, 380)

    with pytest.raises(SuperimpositionError):
        register_acb_similarity(
            image,
            image,
            reference_roi=roi,
            moving_roi=valid,
        )


def test_non_uint8_input_is_not_silently_rescaled():
    image = _feature_canvas().astype(np.float32)
    roi = ImageROI(70, 70, 380, 380)
    with pytest.raises(SuperimpositionError, match="uint8"):
        register_acb_similarity(image, image, reference_roi=roi, moving_roi=roi)


def test_similarity_validator_rejects_shear_and_reflection():
    with pytest.raises(SuperimpositionError, match="not a 2D similarity"):
        _validate_similarity_matrix(np.array([[1.0, 0.2, 0.0], [0.0, 1.0, 0.0]]))

    with pytest.raises(SuperimpositionError, match="reflection"):
        _validate_similarity_matrix(np.array([[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]))


def test_config_rejects_invalid_algorithm_parameters():
    with pytest.raises(SuperimpositionError):
        RegistrationConfig(ratio_test=1.0).validate()
    with pytest.raises(SuperimpositionError):
        RegistrationConfig(ransac_reproj_threshold_px=0.0).validate()
    with pytest.raises(SuperimpositionError):
        RegistrationConfig(confidence=1.0).validate()


def test_concurrent_replay_is_deterministic():
    reference = _feature_canvas()
    forward = _similarity_matrix(angle_degrees=2.5, scale=1.01, tx=6.0, ty=-4.0)
    moving = cv2.warpAffine(reference, forward, (512, 512), flags=cv2.INTER_LINEAR)
    roi = ImageROI(55, 55, 405, 405)

    def run_once(_):
        result = register_acb_similarity(
            reference,
            moving,
            reference_roi=roi,
            moving_roi=roi,
        )
        return np.asarray(result.matrix), result.inlier_count, result.good_match_count

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_once, range(8)))

    first_matrix, first_inliers, first_matches = results[0]
    for matrix, inliers, matches in results[1:]:
        np.testing.assert_allclose(matrix, first_matrix, atol=1e-8)
        assert inliers == first_inliers
        assert matches == first_matches
