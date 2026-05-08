import cv2
import numpy as np
import logging
from typing import Optional, Tuple, Dict

logger = logging.getLogger(__name__)

class CalibrationService:
    """
    Automatic Calibration Service via Computer Vision.
    Detects millimeter markings on cephalometric radiographs.
    """

    def __init__(self):
        # Detection parameters
        self.ruler_expected_mm = 10.0  # Distance between two major ticks
        self.min_pixels_between_ticks = 5
        
    def detect_mm_per_pixel(self, image_path: str) -> Optional[float]:
        """
        Analyzes the image to find a ruler and calculate the mm/pixel ratio.
        """
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None: return None
            
            h, w = img.shape
            
            # 1. ROI Definition (Top of the image, 30% height)
            roi_y_max = int(h * 0.3)
            roi = img[0:roi_y_max, :]
            
            # 3. ADAPTIVE thresholding for robustness (Phase 4 Elite)
            thresh = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)
            
            # 4. Vertical structures detection (The ruler bar)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 20))
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # 5. Finding the ruler
            x_sum = np.sum(vertical_lines, axis=0)
            max_val = np.max(x_sum)
            logger.info(f"AutoCalibration DEBUG: Max X Sum = {max_val}")
            
            if max_val < 30: # Lowered threshold as adaptiveThreshold is more precise
                logger.warning("AutoCalibration: No vertical structure found.")
                return None
                
            best_x = np.argmax(x_sum)
            logger.info(f"AutoCalibration DEBUG: Best X = {best_x}")
            
            # 5. Look broadly around Best X to find ticks
            # Take 40 pixels wide to ensure tick coverage
            profile_roi = thresh[:, max(0, best_x-20):min(w, best_x+20)]
            profile = np.sum(profile_roi, axis=1)
            
            logger.info(f"AutoCalibration DEBUG: Profile Max = {np.max(profile)}")
            
            # 6. Peak detection on vertical profile (Local Maxima)
            peaks = []
            # Look for areas where intensity is significantly higher than local mean
            avg_p = np.mean(profile)
            for y in range(5, len(profile)-5):
                # A peak must be > mean and be a local maximum over 11 pixels
                if profile[y] > avg_p and profile[y] == np.max(profile[y-5:y+6]):
                    if profile[y] > profile[y-1]: # Rising condition to avoid plateaus
                        peaks.append(y)
            
            logger.info(f"AutoCalibration DEBUG: {len(peaks)} potential peaks detected (Local Maxima).")
            
            if len(peaks) < 5: # At least 5 ticks required for a ruler
                logger.warning(f"AutoCalibration: Not enough ticks detected ({len(peaks)}).")
                return None
                
            # 7. Calculate mean distance between peaks (10mm)
            # Eliminate peaks that are too close
            filtered_peaks = [peaks[0]]
            for p in peaks[1:]:
                if p - filtered_peaks[-1] > 10: # Min distance between 2 ticks
                    filtered_peaks.append(p)
            
            logger.info(f"AutoCalibration DEBUG: {len(filtered_peaks)} ticks after filtering.")
            
            if len(filtered_peaks) < 2: return None
            
            distances = [filtered_peaks[i] - filtered_peaks[i-1] for i in range(1, len(filtered_peaks))]
            avg_dist_px = np.median(distances)
            
            mm_per_pixel = self.ruler_expected_mm / avg_dist_px
            
            logger.info(f"AutoCalibration SUCCESS: {len(filtered_peaks)} ticks detected. Ratio: {mm_per_pixel:.4f} mm/px")
            return float(mm_per_pixel)
            
        except Exception as e:
            logger.error(f"Error during automatic calibration: {e}")
            return None

# Singleton
calibration_service = CalibrationService()
