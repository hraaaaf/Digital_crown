import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
# Ajout du dossier racine au path
sys.path.append(os.getcwd())

from backend.services.calibration_service import calibration_service

IMAGE_PATH = "backend/ai_models/cephld_cca/data/test/0img/100.png"

print(f"Testing Auto-Calibration on: {IMAGE_PATH}")
ratio = calibration_service.detect_mm_per_pixel(IMAGE_PATH)

if ratio:
    print(f"SUCCESS! mm_per_pixel = {ratio:.6f}")
    print(f"100 pixels = {100 * ratio:.2f} mm")
else:
    print("FAILED to detect calibration ruler.")
