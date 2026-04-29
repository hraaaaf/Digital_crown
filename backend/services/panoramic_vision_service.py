import os
import time
import logging
import cv2
import numpy as np
from backend.services.sota_panoramic_service import panoramic_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PanoramicVisionEngine:
    """
    Bridge Service for SOTA Panoramic Inference.
    Connects the high-performance ONNX YOLO11x engine to the API.
    """

    def __init__(self):
        # Le moteur SOTA est géré par sota_panoramic_service
        self.engine = panoramic_engine
        logger.info("✅ PanoramicVisionEngine : Pont SOTA activé.")

    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        """
        Amélioration du contraste pour une meilleure détection clinique.
        """
        if len(img.shape) == 3:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l_channel)
            enhanced_img = cv2.merge((cl, a, b))
            return cv2.cvtColor(enhanced_img, cv2.COLOR_LAB2BGR)
        return img

    def predict_abnormalities(self, file_location: str) -> dict:
        """
        Exécute l'analyse via le moteur SOTA ONNX.
        """
        start_time = time.time()
        
        # 1. Analyse SOTA
        result = self.engine.analyze(file_location)
        
        exec_time = time.time() - start_time
        
        # On injecte les métadonnées pour le front-end
        result["processing_time_ms"] = round(exec_time * 1000, 2)
        result["model_info"] = "DENTEX-SOTA-YOLO11x-ONNX"
        
        logger.info(f"🚀 Inférence SOTA terminée en {exec_time:.3f}s. Mode: {result['status']}")
        
        return result

# Singleton
panoramic_vision_engine = PanoramicVisionEngine()
