"""Conservative image-only ruler detection. No physical scale may be inferred.

A candidate requires a sustained vertical axis AND evenly spaced perpendicular
graduations. The earlier V1 detector confused arbitrary intensity peaks with
ticks, especially around radiograph borders. V2 remains unverified by design.
"""
from __future__ import annotations

from dataclasses import replace
import logging
from typing import Optional

import cv2
import numpy as np

from backend.services.cephalo_calibration_candidate import CalibrationCandidate

logger = logging.getLogger(__name__)


class CalibrationService:
    def __init__(self) -> None:
        self.min_candidate_ticks = 5
        # Image-geometry tolerance only, NOT a claimed mm measurement accuracy.
        self.max_detector_spacing_deviation_ratio = 0.065

    @staticmethod
    def _runs_of_marks(mask: np.ndarray, max_thickness: int) -> list[float]:
        positions = np.flatnonzero(mask)
        if len(positions) == 0:
            return []
        cuts = np.flatnonzero(np.diff(positions) > 1) + 1
        groups = np.split(positions, cuts)
        return [float(np.mean(group)) for group in groups if len(group) <= max_thickness]

    def _regular_runs(self, marks: list[float], height: int) -> list[tuple[float, ...]]:
        """Retain only observed, consecutive, near-periodic marks (no invented ticks)."""
        min_ticks = max(self.min_candidate_ticks, 8 if height >= 300 else 5)
        if len(marks) < min_ticks or len(marks) > 512:
            return []
        valid: list[tuple[float, ...]] = []
        for i in range(len(marks) - min_ticks + 1):
            for j in range(i + 1, min(i + 5, len(marks))):
                period = marks[j] - marks[i]
                if not 5 <= period <= height / max(min_ticks - 1, 1):
                    continue
                run = [marks[i], marks[j]]
                for mark in marks[j + 1:]:
                    diff = mark - run[-1]
                    if diff < 0.80 * period:
                        continue
                    if diff > 1.20 * period:
                        break
                    run.append(mark)
                if len(run) < min_ticks:
                    continue
                gaps = np.diff(run)
                median = float(np.median(gaps))
                if median <= 0:
                    continue
                deviation = float(np.max(np.abs(gaps - median) / median))
                if deviation <= self.max_detector_spacing_deviation_ratio:
                    valid.append(tuple(run))
        return valid

    def _candidate_from_threshold(self, thresh: np.ndarray) -> Optional[CalibrationCandidate]:
        """Detect a one-sided or two-sided vertical ruler, image-space only."""
        if thresh.ndim != 2 or thresh.size == 0:
            return None
        h, w = thresh.shape
        if h < 65 or w < 60:
            return None
        vertical_len = max(12, min(42, h // 15))
        horizontal_len = max(9, min(21, w // 85))
        side_radius = max(12, horizontal_len + 4)
        vertical = cv2.morphologyEx(
            thresh, cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_len)),
        )
        horizontal = cv2.morphologyEx(
            thresh, cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_len, 1)),
        )
        column_support = np.count_nonzero(vertical, axis=0)
        axes: list[int] = []
        for pos in np.argsort(column_support)[::-1][:min(w, 240)]:
            x = int(pos)
            if column_support[x] < max(45, h * 0.18):
                break
            if not (side_radius < x < w - side_radius - 1):
                continue
            if any(abs(x - earlier) < max(4, side_radius // 2) for earlier in axes):
                continue
            axes.append(x)
            if len(axes) >= 14:
                break

        results: list[tuple[float, int, tuple[float, ...]]] = []
        for x in axes:
            for side in (-1, 1):
                lo, hi = ((x - side_radius, x - 1) if side == -1
                          else (x + 2, x + side_radius + 1))
                support = np.count_nonzero(horizontal[:, lo:hi], axis=1)
                marks = self._runs_of_marks(
                    support >= max(3, horizontal_len // 3),
                    max_thickness=max(4, h // 110),
                )
                for run in self._regular_runs(marks, h):
                    # Reject short periodic film texture and unconnected edges.
                    if run[-1] - run[0] < max(80, h * 0.12):
                        continue
                    y0, y1 = int(run[0]), int(run[-1]) + 1
                    axis_segment = vertical[y0:y1, max(0, x - 2):min(w, x + 3)]
                    continuity = float(np.mean(np.any(axis_segment > 0, axis=1)))
                    if continuity < 0.65:
                        continue
                    gaps = np.diff(run)
                    median = float(np.median(gaps))
                    error = float(np.max(np.abs(gaps - median) / median))
                    score = len(run) * continuity / (1 + error)
                    results.append((score, x, run))

        if not results:
            return None
        results.sort(key=lambda item: (-item[0], item[1]))
        score, x, ticks = results[0]
        # When two distant equally convincing axes compete, never guess one.
        for second_score, second_x, _ in results[1:]:
            if second_score >= score * 0.8 and abs(second_x - x) > max(45, w * 0.05):
                logger.info("Calibration V2 refused ambiguous ruler geometry")
                return None
        candidate = CalibrationCandidate.from_ticks(
            axis_x_px=float(x), tick_positions_y_px=ticks,
        )
        return replace(candidate, detector_method="CLASSICAL_RULER_GEOMETRY_V2")

    def detect_candidate(self, image_path: str) -> Optional[CalibrationCandidate]:
        """Return an unverified ruler candidate in original pixel coordinates."""
        try:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None or image.ndim != 2 or image.size == 0:
                return None
            height, width = image.shape
            if height < 65 or width < 60 or height > 5000 or width > 5000:
                return None
            # Prefer top band where the fiducial usually appears, but allow a
            # lower ruler. Both polarities avoid bias to dark or light marks.
            bands = (image[:max(65, int(height * 0.30)), :], image)
            for region in bands:
                for polarity in (cv2.THRESH_BINARY_INV, cv2.THRESH_BINARY):
                    threshold = cv2.adaptiveThreshold(
                        region, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                        polarity, 11, 2,
                    )
                    candidate = self._candidate_from_threshold(threshold)
                    if candidate is not None:
                        logger.info(
                            "Calibration V2: %s observed unverified image ticks",
                            len(candidate.tick_positions_y_px),
                        )
                        return candidate
            return None
        except (cv2.error, ValueError, TypeError) as exc:
            logger.warning(
                "Calibration V2 detection failed closed: %s", type(exc).__name__,
            )
            return None

    def detect_mm_per_pixel(self, image_path: str) -> None:
        """Compatibility shim: images alone cannot certify any mm/pixel ratio."""
        self.detect_candidate(image_path)
        return None


calibration_service = CalibrationService()
