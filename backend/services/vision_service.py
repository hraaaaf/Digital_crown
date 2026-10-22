"""Single-engine cephalometric landmark detection: certified SRPose38 ONNX only.

If the certified engine is unavailable or inference fails, return no inferred
landmarks. The caller can offer manual landmark placement; no legacy PyTorch
weights are loaded or silently substituted.
"""
import logging
import time

import cv2

from .sota_vision_service import sota_vision_engine

logger = logging.getLogger(__name__)


class VisionEngine:
    def predict_landmarks(self, file_location: str) -> dict:
        start_time = time.time()
        if cv2.imread(file_location, cv2.IMREAD_GRAYSCALE) is None:
            raise ValueError(f"Could not read image at: {file_location}")

        landmarks = []
        mode = "FAILED"
        warning = "SRPose38 indisponible ou en échec. Placement manuel requis."
        if sota_vision_engine.is_ready:
            try:
                result = sota_vision_engine.predict_landmarks(file_location)
                if result and len(result.get("landmarks", [])) == 38:
                    landmarks = result["landmarks"]
                    mode = "SOTA_ONNX_38"
                    warning = None
                else:
                    logger.error("SRPose38 returned no valid 38-point prediction")
            except Exception:
                logger.exception("SRPose38 inference failed; manual placement required")
        else:
            logger.error("SRPose38 runtime unavailable; manual placement required")

        return {
            "landmarks": landmarks,
            "mode_inference": mode,
            "warning": warning,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


vision_engine = VisionEngine()
