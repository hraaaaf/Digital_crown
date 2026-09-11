import cv2
import numpy as np
import logging
from typing import Optional

from backend.services.cephalo_calibration_candidate import CalibrationCandidate

logger = logging.getLogger(__name__)


class CalibrationService:
    """Detect image-space ruler geometry without inventing a physical scale."""

    def __init__(self) -> None:
        self.min_pixels_between_ticks = 10
        self.min_candidate_ticks = 5

    def _candidate_from_threshold(self, thresh: np.ndarray) -> Optional[CalibrationCandidate]:
        """Extract a ruler candidate from a thresholded top-of-image ROI."""
        if thresh.ndim != 2 or thresh.size == 0:
            return None

        h, w = thresh.shape
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 20))
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        x_sum = np.sum(vertical_lines, axis=0)
        if x_sum.size == 0:
            return None
        max_val = float(np.max(x_sum))
        logger.info("AutoCalibration candidate: max vertical response=%s", max_val)
        if max_val < 30:
            return None

        best_x = int(np.argmax(x_sum))
        profile_roi = thresh[:, max(0, best_x - 20):min(w, best_x + 20)]
        if profile_roi.size == 0:
            return None
        profile = np.sum(profile_roi, axis=1)
        avg_profile = float(np.mean(profile))

        peaks: list[int] = []
        for y in range(5, len(profile) - 5):
            local = profile[y - 5:y + 6]
            if profile[y] > avg_profile and profile[y] == np.max(local) and profile[y] > profile[y - 1]:
                peaks.append(y)

        filtered_peaks: list[int] = []
        for peak in peaks:
            if not filtered_peaks or peak - filtered_peaks[-1] > self.min_pixels_between_ticks:
                filtered_peaks.append(peak)

        if len(filtered_peaks) < self.min_candidate_ticks:
            logger.info("AutoCalibration candidate rejected: %s filtered ticks", len(filtered_peaks))
            return None

        return CalibrationCandidate.from_ticks(
            axis_x_px=float(best_x),
            tick_positions_y_px=filtered_peaks,
        )

    def detect_candidate(self, image_path: str) -> Optional[CalibrationCandidate]:
        """Return unverified ruler geometry in original image coordinates."""
        try:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None or image.ndim != 2 or image.size == 0:
                return None

            height, _ = image.shape
            roi_y_max = int(height * 0.3)
            if roi_y_max <= 0:
                return None
            roi = image[:roi_y_max, :]
            thresh = cv2.adaptiveThreshold(
                roi,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11,
                2,
            )
            return self._candidate_from_threshold(thresh)
        except Exception as exc:
            logger.error("Error during automatic calibration candidate detection: %s", exc)
            return None

    def detect_mm_per_pixel(self, image_path: str) -> None:
        """Compatibility shim: automatic detection no longer yields verified mm/px."""
        candidate = self.detect_candidate(image_path)
        if candidate is not None:
            logger.info(
                "Automatic ruler candidate detected at x=%s with %s ticks; physical scale remains unverified",
                candidate.axis_x_px,
                len(candidate.tick_positions_y_px),
            )
        return None


calibration_service = CalibrationService()
