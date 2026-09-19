"""Deterministic 2D anterior-cranial-base feature registration for F5.

Scientific boundary:
- This module estimates a geometric registration only.
- It does not diagnose, score treatment, or interpret change.
- It does not declare a result clinically valid.
- Clinical activation remains gated by V1_05_F5_VALIDATION_STRATEGY.md.

Method:
clinician-confirmed stable ACB ROI -> SIFT -> KNN ratio filter ->
robust 4-DOF similarity transform mapping moving image to reference image.

Scientific source for SIFT/KNN ratio < 0.7 and finite 4-DOF similarity transform:
Zhao et al., J Digit Imaging (2025), DOI 10.1007/s10278-025-01447-0.

OpenCV estimator defaults are made explicit for reproducibility and are algorithmic
parameters, not clinical acceptance thresholds:
https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import cv2
import numpy as np


METHOD_ID = "ACB_STRUCTURAL_FEATURE_SIMILARITY"
METHOD_VERSION = "1"
QUALITY_STATUS = "ENGINE_ESTIMATE_ONLY"


class SuperimpositionError(ValueError):
    """Explicit fail-closed error for non-computable registrations."""


@dataclass(frozen=True)
class ImageROI:
    """Pixel-space region selected/confirmed on one immutable source image."""

    x: int
    y: int
    width: int
    height: int

    def validate(self, image_shape: tuple[int, ...]) -> None:
        if len(image_shape) < 2:
            raise SuperimpositionError("Image shape must contain height and width.")
        image_height, image_width = int(image_shape[0]), int(image_shape[1])
        if self.width <= 0 or self.height <= 0:
            raise SuperimpositionError("ROI width and height must be positive.")
        if self.x < 0 or self.y < 0:
            raise SuperimpositionError("ROI origin must be inside the image.")
        if self.x + self.width > image_width or self.y + self.height > image_height:
            raise SuperimpositionError("ROI extends outside the source image.")

    def as_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class RegistrationConfig:
    """Versioned algorithm configuration; none of these are clinical gates."""

    ratio_test: float = 0.7
    ransac_reproj_threshold_px: float = 3.0
    max_iters: int = 2000
    confidence: float = 0.99
    refine_iters: int = 10
    rng_seed: int = 0

    def validate(self) -> None:
        if not (0.0 < self.ratio_test < 1.0):
            raise SuperimpositionError("KNN ratio_test must be between 0 and 1.")
        if not math.isfinite(self.ransac_reproj_threshold_px) or self.ransac_reproj_threshold_px <= 0:
            raise SuperimpositionError("RANSAC reprojection threshold must be positive and finite.")
        if self.max_iters <= 0:
            raise SuperimpositionError("RANSAC max_iters must be positive.")
        if not (0.0 < self.confidence < 1.0):
            raise SuperimpositionError("RANSAC confidence must be between 0 and 1.")
        if self.refine_iters < 0:
            raise SuperimpositionError("RANSAC refine_iters cannot be negative.")


@dataclass(frozen=True)
class RegistrationResult:
    """Recalculable transform metadata. Never a clinical interpretation."""

    matrix: tuple[tuple[float, float, float], tuple[float, float, float]]
    rotation_degrees: float
    uniform_scale: float
    translation_x_px: float
    translation_y_px: float
    good_match_count: int
    inlier_count: int
    reference_roi: ImageROI
    moving_roi: ImageROI
    reference_size_px: tuple[int, int]
    moving_size_px: tuple[int, int]
    config: RegistrationConfig

    def to_metadata(self) -> dict[str, Any]:
        return {
            "method_id": METHOD_ID,
            "method_version": METHOD_VERSION,
            "quality_status": QUALITY_STATUS,
            "clinically_validated": False,
            "transform_direction": "moving_to_reference",
            "matrix": [list(row) for row in self.matrix],
            "rotation_degrees": self.rotation_degrees,
            "uniform_scale": self.uniform_scale,
            "translation_px": {
                "x": self.translation_x_px,
                "y": self.translation_y_px,
            },
            "good_match_count": self.good_match_count,
            "inlier_count": self.inlier_count,
            "reference_roi": self.reference_roi.as_dict(),
            "moving_roi": self.moving_roi.as_dict(),
            "reference_size_px": {
                "width": self.reference_size_px[0],
                "height": self.reference_size_px[1],
            },
            "moving_size_px": {
                "width": self.moving_size_px[0],
                "height": self.moving_size_px[1],
            },
            "algorithm": {
                "feature": "SIFT",
                "matcher": "BFMatcher_L2_KNN",
                "ratio_test": self.config.ratio_test,
                "estimator": "estimateAffinePartial2D_RANSAC",
                "ransac_reproj_threshold_px": self.config.ransac_reproj_threshold_px,
                "max_iters": self.config.max_iters,
                "confidence": self.config.confidence,
                "refine_iters": self.config.refine_iters,
                "rng_seed": self.config.rng_seed,
                "opencv_version": cv2.__version__,
            },
        }


def _as_gray_uint8(image: np.ndarray, *, label: str) -> np.ndarray:
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise SuperimpositionError(f"{label} image is missing or empty.")
    if image.dtype != np.uint8:
        raise SuperimpositionError(f"{label} image must be uint8; implicit intensity conversion is forbidden.")
    if image.ndim == 2:
        return np.ascontiguousarray(image)
    if image.ndim == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    raise SuperimpositionError(f"{label} image must be grayscale or BGR.")


def _roi_mask(shape: tuple[int, int], roi: ImageROI) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    mask[roi.y : roi.y + roi.height, roi.x : roi.x + roi.width] = 255
    return mask


def _validate_similarity_matrix(matrix: np.ndarray) -> tuple[float, float, float, float]:
    if matrix is None or matrix.shape != (2, 3) or not np.isfinite(matrix).all():
        raise SuperimpositionError("Registration did not produce a finite 2x3 transform.")

    linear = matrix[:, :2].astype(np.float64)
    gram = linear.T @ linear
    scale_sq = float(np.trace(gram) / 2.0)
    if not math.isfinite(scale_sq) or scale_sq <= 0.0:
        raise SuperimpositionError("Registration produced a degenerate transform.")

    tolerance = max(1e-8, scale_sq * 1e-5)
    if not np.allclose(gram, np.eye(2) * scale_sq, atol=tolerance, rtol=1e-5):
        raise SuperimpositionError("Registration transform is not a 2D similarity transform.")
    if float(np.linalg.det(linear)) <= 0.0:
        raise SuperimpositionError("Registration transform contains a reflection.")

    scale = math.sqrt(scale_sq)
    rotation_deg = math.degrees(math.atan2(float(matrix[1, 0]), float(matrix[0, 0])))
    tx = float(matrix[0, 2])
    ty = float(matrix[1, 2])
    return scale, rotation_deg, tx, ty


def register_acb_similarity(
    reference_image: np.ndarray,
    moving_image: np.ndarray,
    *,
    reference_roi: ImageROI,
    moving_roi: ImageROI,
    config: RegistrationConfig | None = None,
) -> RegistrationResult:
    """Estimate a moving->reference ACB similarity transform.

    The function intentionally exposes match/inlier counts but does not convert
    them into a clinical pass/fail threshold. Clinical thresholds are blocked
    pending the prospective validation protocol.
    """

    config = config or RegistrationConfig()
    config.validate()

    reference = _as_gray_uint8(reference_image, label="Reference")
    moving = _as_gray_uint8(moving_image, label="Moving")
    reference_roi.validate(reference.shape)
    moving_roi.validate(moving.shape)

    if not hasattr(cv2, "SIFT_create"):
        raise SuperimpositionError("OpenCV SIFT support is unavailable.")

    sift = cv2.SIFT_create()
    keypoints_ref, descriptors_ref = sift.detectAndCompute(
        reference, _roi_mask(reference.shape, reference_roi)
    )
    keypoints_mov, descriptors_mov = sift.detectAndCompute(
        moving, _roi_mask(moving.shape, moving_roi)
    )

    if descriptors_ref is None or descriptors_mov is None:
        raise SuperimpositionError("Stable ROI does not contain detectable SIFT features.")
    if len(keypoints_ref) < 2 or len(keypoints_mov) < 2:
        raise SuperimpositionError("At least two feature correspondences are required.")

    # SIFT descriptors are floating-point vectors. OpenCV specifies L1/L2 for
    # SIFT/SURF and Hamming for binary descriptors. Zhao 2025 reports SIFT
    # with a Hamming KNN matcher; we intentionally follow the descriptor
    # contract here rather than reproduce that internal inconsistency.
    matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    candidate_pairs = matcher.knnMatch(descriptors_mov, descriptors_ref, k=2)
    good_matches = []
    for pair in candidate_pairs:
        if len(pair) != 2:
            continue
        nearest, second = pair
        if nearest.distance < config.ratio_test * second.distance:
            good_matches.append(nearest)

    # Two non-coincident point pairs are the mathematical minimum for a
    # 4-DOF similarity transform. This is not a clinical quality threshold.
    if len(good_matches) < 2:
        raise SuperimpositionError("Insufficient feature correspondences for similarity estimation.")

    moving_points = np.float32(
        [keypoints_mov[match.queryIdx].pt for match in good_matches]
    ).reshape(-1, 1, 2)
    reference_points = np.float32(
        [keypoints_ref[match.trainIdx].pt for match in good_matches]
    ).reshape(-1, 1, 2)

    cv2.setRNGSeed(config.rng_seed)
    matrix, inlier_mask = cv2.estimateAffinePartial2D(
        moving_points,
        reference_points,
        method=cv2.RANSAC,
        ransacReprojThreshold=config.ransac_reproj_threshold_px,
        maxIters=config.max_iters,
        confidence=config.confidence,
        refineIters=config.refine_iters,
    )
    scale, rotation_deg, tx, ty = _validate_similarity_matrix(matrix)

    inlier_count = int(np.asarray(inlier_mask).sum()) if inlier_mask is not None else 0
    matrix_tuple = (
        (float(matrix[0, 0]), float(matrix[0, 1]), float(matrix[0, 2])),
        (float(matrix[1, 0]), float(matrix[1, 1]), float(matrix[1, 2])),
    )

    return RegistrationResult(
        matrix=matrix_tuple,
        rotation_degrees=rotation_deg,
        uniform_scale=scale,
        translation_x_px=tx,
        translation_y_px=ty,
        good_match_count=len(good_matches),
        inlier_count=inlier_count,
        reference_roi=reference_roi,
        moving_roi=moving_roi,
        reference_size_px=(reference.shape[1], reference.shape[0]),
        moving_size_px=(moving.shape[1], moving.shape[0]),
        config=config,
    )


def warp_moving_to_reference(
    moving_image: np.ndarray,
    result: RegistrationResult,
    *,
    interpolation: int = cv2.INTER_LINEAR,
) -> np.ndarray:
    """Render a derived image without mutating the original source."""

    moving = _as_gray_uint8(moving_image, label="Moving")
    matrix = np.asarray(result.matrix, dtype=np.float64)
    _validate_similarity_matrix(matrix)
    return cv2.warpAffine(
        moving,
        matrix,
        result.reference_size_px,
        flags=interpolation,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
