import cv2
import numpy as np
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CalibrationService:
    """Detect radiographic ruler candidates without inventing a physical scale.

    Detection is deliberately non-authoritative: this service returns image-space
    evidence only. A clinician must confirm the real-world distance through the
    audited calibration endpoint before millimetric cephalometric measurements are
    considered computable.
    """

    def __init__(self):
        self.min_pixels_between_ticks = 10
        self.min_tick_count = 5

    def detect_ruler_candidate(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Return a ruler/tick candidate in pixel coordinates, never mm/px.

        The candidate contains two adjacent representative tick positions and
        metadata useful for practitioner validation. No physical tick distance is
        assumed here.
        """
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return None

            h, w = img.shape
            roi_y_max = int(h * 0.3)
            roi = img[0:roi_y_max, :]

            thresh = cv2.adaptiveThreshold(
                roi,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11,
                2,
            )

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 20))
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            x_sum = np.sum(vertical_lines, axis=0)
            max_val = float(np.max(x_sum))
            logger.info("RulerCandidate DEBUG: Max X Sum = %s", max_val)

            if max_val < 30:
                logger.info("RulerCandidate: no vertical structure found")
                return None

            best_x = int(np.argmax(x_sum))
            profile_roi = thresh[:, max(0, best_x - 20):min(w, best_x + 20)]
            profile = np.sum(profile_roi, axis=1)
            avg_profile = float(np.mean(profile))

            peaks = []
            for y in range(5, len(profile) - 5):
                window = profile[y - 5:y + 6]
                if (
                    profile[y] > avg_profile
                    and profile[y] == np.max(window)
                    and profile[y] > profile[y - 1]
                ):
                    peaks.append(y)

            if len(peaks) < self.min_tick_count:
                logger.info("RulerCandidate: insufficient peaks (%s)", len(peaks))
                return None

            filtered_peaks = [peaks[0]]
            for peak in peaks[1:]:
                if peak - filtered_peaks[-1] > self.min_pixels_between_ticks:
                    filtered_peaks.append(peak)

            if len(filtered_peaks) < self.min_tick_count:
                logger.info(
                    "RulerCandidate: insufficient filtered ticks (%s)",
                    len(filtered_peaks),
                )
                return None

            distances = np.diff(filtered_peaks).astype(float)
            median_distance = float(np.median(distances))
            if not np.isfinite(median_distance) or median_distance <= 0:
                return None

            # Choose the actually observed adjacent interval nearest the median so
            # p1/p2 correspond to visible ticks rather than synthesized coordinates.
            representative_index = int(np.argmin(np.abs(distances - median_distance)))
            y1 = int(filtered_peaks[representative_index])
            y2 = int(filtered_peaks[representative_index + 1])
            distance_px = float(y2 - y1)

            # Purely image-space regularity metric. This is NOT clinical confidence.
            mad = float(np.median(np.abs(distances - median_distance)))
            spacing_regularity = max(0.0, min(1.0, 1.0 - (mad / median_distance)))

            candidate = {
                "method": "RULER_TICK_CANDIDATE_V1",
                "p1": [float(best_x), float(y1)],
                "p2": [float(best_x), float(y2)],
                "distance_px": distance_px,
                "tick_count": len(filtered_peaks),
                "spacing_regularity": round(spacing_regularity, 4),
                "requires_clinician_validation": True,
            }
            logger.info(
                "RulerCandidate: %s ticks, representative interval %.2f px",
                len(filtered_peaks),
                distance_px,
            )
            return candidate

        except Exception as exc:
            logger.error("Error during ruler candidate detection: %s", exc)
            return None

    def detect_mm_per_pixel(self, image_path: str) -> Optional[float]:
        """Deprecated fail-closed compatibility shim.

        Automatic ruler detection cannot establish a physical millimetric scale
        without a clinician-confirmed real-world distance.
        """
        candidate = self.detect_ruler_candidate(image_path)
        if candidate is not None:
            logger.warning(
                "Automatic ruler candidate detected but mm/pixel remains unverified"
            )
        return None


calibration_service = CalibrationService()
