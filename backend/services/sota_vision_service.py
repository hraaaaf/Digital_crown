import hashlib
import logging
import os
import time
from typing import Optional

import cv2
import numpy as np

from backend.core.paths import AppPaths
from backend.services.srpose38_contract import (
    SOTA_LANDMARKS_MAPPING,
    SRPOSE38_MODEL_NAME,
    SRPOSE38_MODEL_SHA256,
    SRPOSE38_MODEL_SIZE_BYTES,
)
from backend.services.srpose38_pipeline import (
    SRPOSE38_NUM_LANDMARKS,
    decode_srpose38_heatmaps,
    prepare_srpose38_input,
)

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = logging.getLogger(__name__)

def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SOTAVisionEngine:
    """SRPose38 ONNX inference using the benchmark-certified runtime pipeline."""

    def __init__(self, model_path: Optional[str] = None):
        self.num_landmarks = SRPOSE38_NUM_LANDMARKS
        self.model_path = model_path or str(AppPaths.get_model_path(SRPOSE38_MODEL_NAME))
        self.session = None
        self.is_ready = False
        self._initialize_engine()

    def _initialize_engine(self):
        if ort is None:
            logger.warning("SOTAVisionEngine: onnxruntime non installé.")
            return
        if not os.path.isfile(self.model_path):
            logger.warning("SOTAVisionEngine: asset SRPose38 absent: %s", self.model_path)
            return
        if os.path.getsize(self.model_path) != SRPOSE38_MODEL_SIZE_BYTES:
            logger.error("SOTAVisionEngine: taille SRPose38 invalide; moteur désactivé.")
            return

        actual_sha256 = _sha256_file(self.model_path)
        if actual_sha256 != SRPOSE38_MODEL_SHA256:
            logger.error(
                "SOTAVisionEngine: SHA256 SRPose38 invalide (%s); moteur désactivé.",
                actual_sha256,
            )
            return

        try:
            start_time = time.time()
            # CPU is the only provider certified by the SRPose38 parity proof.
            # DirectML stays disabled until it has its own numerical certification.
            self.session = ort.InferenceSession(
                self.model_path,
                providers=["CPUExecutionProvider"],
            )
            inputs = self.session.get_inputs()
            outputs = self.session.get_outputs()
            if len(inputs) != 1 or len(outputs) != 1:
                raise ValueError("SRPose38 ONNX doit exposer exactement 1 entrée et 1 sortie")
            self.is_ready = True
            logger.info(
                "SOTAVisionEngine: SRPose38 certifié chargé en %.2fs via CPUExecutionProvider",
                time.time() - start_time,
            )
        except Exception as exc:
            self.session = None
            self.is_ready = False
            logger.error("SOTAVisionEngine: échec de chargement SRPose38: %s", exc)

    def predict_landmarks(self, file_location: str) -> Optional[dict]:
        if not self.is_ready or self.session is None:
            return None

        start_time = time.time()
        image_bgr = cv2.imread(file_location, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError(f"Image illisible : {file_location}")

        image_input, geometry = prepare_srpose38_input(image_bgr)
        input_name = self.session.get_inputs()[0].name
        heatmaps = self.session.run(None, {input_name: image_input})[0]
        points, scores = decode_srpose38_heatmaps(heatmaps, geometry)

        if points.shape != (self.num_landmarks, 2) or not np.isfinite(points).all():
            raise ValueError("SRPose38 n'a pas retourné exactement 38 points finis")

        final_landmarks = []
        for index, ((x_coord, y_coord), score) in enumerate(zip(points, scores)):
            final_landmarks.append(
                {
                    "id": SOTA_LANDMARKS_MAPPING.get(index, f"P_{index}"),
                    "x": float(x_coord),
                    "y": float(y_coord),
                    "confidence": float(score),
                }
            )

        return {
            "landmarks": final_landmarks,
            "mode_inference": "SOTA_ONNX_38",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "model_sha256": SRPOSE38_MODEL_SHA256,
            "runtime_provider": "CPUExecutionProvider",
        }


sota_vision_engine = SOTAVisionEngine()
