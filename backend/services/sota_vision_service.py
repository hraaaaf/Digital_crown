import os
import time
import logging
import cv2
import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = logging.getLogger(__name__)

# Mapping des 38 points SOTA vers les IDs cliniques
# Le modèle utilise la nomenclature CL-Detection (38 points), différente de ISBI 2015.
SOTA_LANDMARKS_MAPPING = {
    0: "S", 1: "N", 2: "Or", 3: "Po", 4: "A", 5: "B", 6: "Pog", 7: "Me",
    8: "Gn", 9: "Go", 10: "L1_incisal", 11: "U1_incisal", 12: "Ls",
    13: "Li", 14: "Sn", 15: "Pog_soft", 16: "PNS", 17: "ANS", 18: "Ar",
    19: "L1_apex", 20: "U1_apex", 21: "G_soft", 22: "N_soft", 23: "Prn",
    24: "Cm", 25: "A_soft", 26: "St", 27: "B_soft", 28: "Co", 29: "PTM", 30: "Ba",
    31: "U6m", 32: "U6d", 33: "L6m", 34: "L6d", 35: "U3t", 36: "L3t", 37: "Me_soft"
}

class SOTAVisionEngine:
    """
    Moteur d'Inférence ONNX Haute Performance (SOTA).
    Optimisé pour les CPU de cabinet dentaire.
    """
    def __init__(self):
        self.target_size = 1024
        self.num_landmarks = 38
        self.session = None
        self.is_ready = False
        
        # Chemins potentiels pour le modèle ONNX
        self.possible_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai_models", "model.onnx")),
            "C:\\Users\\lenovo\\Documents\\Cabinet\\DigitalCrown_SOTA\\backend\\ai_models\\cephalometric_sota\\model.onnx"
        ]
        
        self._initialize_engine()

    def _initialize_engine(self):
        if ort is None:
            logger.warning("SOTAVisionEngine : onnxruntime non installé.")
            return

        model_path = None
        for path in self.possible_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path:
            logger.warning("SOTAVisionEngine : model.onnx introuvable. Mode SOTA désactivé.")
            return

        try:
            logger.info(f"SOTAVisionEngine : Chargement du modèle ONNX depuis {model_path}...")
            start_time = time.time()
            
            # Utilisation de DirectML sur Windows si disponible, sinon CPU
            providers = ['DmlExecutionProvider', 'CPUExecutionProvider'] if 'DmlExecutionProvider' in ort.get_available_providers() else ['CPUExecutionProvider']
            
            self.session = ort.InferenceSession(model_path, providers=providers)
            self.is_ready = True
            logger.info(f"SOTAVisionEngine : Chargé en {time.time() - start_time:.2f}s avec {self.session.get_providers()[0]}")
        except Exception as e:
            logger.error(f"Erreur chargement SOTAVisionEngine : {e}")

    def predict_landmarks(self, file_location: str) -> dict:
        if not self.is_ready:
            return None

        start_time = time.time()
        
        # 1. Pre-processing
        img = cv2.imread(file_location)
        if img is None:
            raise ValueError(f"Image illisible : {file_location}")
            
        orig_h, orig_w = img.shape[:2]
        
        # Redimensionnement vers 1024x1024 (résolution SOTA)
        img_resized = cv2.resize(img, (self.target_size, self.target_size))
        
        # Normalisation (SOTA utilise Mean/Std spécifique HRNet)
        # mean=[121.25, 121.25, 121.25], std=[76.5, 76.5, 76.5]
        img_norm = (img_resized.astype(np.float32) - 121.25) / 76.5
        
        # Format NCHW : [1, 3, 1024, 1024]
        img_input = np.transpose(img_norm, (2, 0, 1))[np.newaxis, :]
        
        # 2. Inférence ONNX
        input_name = self.session.get_inputs()[0].name
        heatmaps = self.session.run(None, {input_name: img_input})[0] # [1, 38, 1024, 1024]
        heatmaps = heatmaps[0] # [38, 1024, 1024]
        
        # 3. Post-processing (Argmax heatmap)
        final_landmarks = []
        scale_x = orig_w / self.target_size
        scale_y = orig_h / self.target_size
        
        for i in range(self.num_landmarks):
            hm = heatmaps[i]
            flat_idx = np.argmax(hm)
            y_pred, x_pred = np.unravel_index(flat_idx, hm.shape)
            
            final_x = int(x_pred * scale_x)
            final_y = int(y_pred * scale_y)
            
            point_id = SOTA_LANDMARKS_MAPPING.get(i, f"P_{i}")
            final_landmarks.append({"id": point_id, "x": final_x, "y": final_y})
            
        exec_time = time.time() - start_time
        return {
            "landmarks": final_landmarks,
            "mode_inference": "SOTA_ONNX_38",
            "processing_time_ms": round(exec_time * 1000, 2)
        }

# Instance singleton
sota_vision_engine = SOTAVisionEngine()
