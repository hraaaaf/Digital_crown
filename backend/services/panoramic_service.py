import os
import time
import logging
import cv2
import numpy as np
from typing import List, Dict, Any

from backend.config import settings

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = logging.getLogger(__name__)


def _is_clinical_environment() -> bool:
    """En production ou cabinet, aucune simulation clinique n'est tolérée."""
    return str(getattr(settings, "ENVIRONMENT", "development")).lower() in {"production", "cabinet"}

class PanoramicEngine:
    """
    Moteur Vision ELITE SOTA (v1.8) pour radiographies panoramiques (OPG).
    Utilise le modèle YOLO11x optimisé avec compensation de la Smile Curve (v4.3).
    """
    def __init__(self):
        self.session = None
        self.is_ready = False
        self.input_size = 1280
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, "ai_models", "panoramic_model.onnx")
        self.classes = ["Carie", "Carie Profonde", "Lésion Périapicale", "Dent Incluse"]

    async def initialize(self):
        """Initialisation appelée au démarrage de FastAPI."""
        if ort is None:
            logger.error("PanoramicEngine : ONNX Runtime n'est pas installé.")
            return
        if not os.path.exists(self.model_path):
            logger.warning(f"PanoramicEngine : Modèle ELITE {self.model_path} introuvable.")
            return
        try:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 4
            available_providers = ort.get_available_providers()
            providers = ['DmlExecutionProvider', 'CPUExecutionProvider'] if 'DmlExecutionProvider' in available_providers else ['CPUExecutionProvider']
            self.session = ort.InferenceSession(self.model_path, sess_options=opts, providers=providers)
            self.is_ready = True
            logger.info(f"✅ Moteur Panoramique ELITE activé : {self.model_path} ({self.session.get_providers()[0]})")
        except Exception as e:
            logger.error(f"❌ Échec initialisation ONNX : {e}")

    def _letterbox(self, img: np.ndarray, new_shape=(1280, 1280)) -> tuple:
        shape = img.shape[:2]
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        dw /= 2
        dh /= 2
        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        return img, r, (dw, dh)

    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        try:
            if len(img.shape) == 3:
                lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=4.5, tileGridSize=(12, 12))
                cl = clahe.apply(l)
                img = cv2.merge((cl, a, b))
                return cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
            return img
        except Exception:
            return img

    def detect_teeth_only(self, image_path: str) -> dict:
        from backend.services.sota_panoramic_service import panoramic_engine as sota_engine
        try:
            sota_result = sota_engine.analyze(image_path)
            if sota_result.get("status") != "SUCCESS":
                logger.warning(f"SOTA analyze retourna status={sota_result.get('status')}")
                return {
                    "status": "UNAVAILABLE",
                    "mode_inference": sota_result.get("inference_mode", "UNAVAILABLE"),
                    "detections_data": {
                        "detections": [],
                        "summary": "Détection automatique indisponible — repérage manuel requis par le praticien"
                    },
                }
            detections = sota_result.get("detections", [])
            CONFIDENCE_THRESHOLD_DEFAULT = 0.70
            CONFIDENCE_THRESHOLD_WISDOM = 0.80
            WISDOM_TEETH = {18, 28, 38, 48}
            filtered_detections = []
            for det in detections:
                tooth_fdi = det.get("tooth")
                confidence = det.get("confidence", 0.0)
                threshold = CONFIDENCE_THRESHOLD_WISDOM if tooth_fdi in WISDOM_TEETH else CONFIDENCE_THRESHOLD_DEFAULT
                if confidence >= threshold:
                    bbox = det.get("bbox", [0, 0, 0, 0])
                    filtered_detections.append({
                        "fdi": tooth_fdi,
                        "label": f"Tooth {tooth_fdi}",
                        "confidence": float(confidence),
                        "bbox": {
                            "x_min": float(bbox[0]),
                            "y_min": float(bbox[1]),
                            "x_max": float(bbox[2]),
                            "y_max": float(bbox[3])
                        },
                        "present": True
                    })
            return {
                "status": "SUCCESS",
                "mode_inference": "SOTA_TOOTH_DETECTION",
                "detections_data": {
                    "detections": filtered_detections,
                    "summary": f"Détection SOTA: {len(filtered_detections)} dents détectées — annotation manuelle par le praticien",
                    "detection_count": len(filtered_detections)
                },
            }
        except Exception as e:
            logger.error(f"❌ Erreur détection dents SOTA: {e}")
            return {
                "status": "UNAVAILABLE",
                "mode_inference": "FALLBACK_EMPTY",
                "detections_data": {
                    "detections": [],
                    "summary": "Détection automatique indisponible — repérage manuel requis par le praticien",
                    "error": str(e)
                },
            }

    def predict(self, image_path: str) -> dict:
        if not self.is_ready:
            if _is_clinical_environment():
                raise RuntimeError(
                    "Modèle IA panoramique indisponible : l'analyse est refusée en environnement clinique. Aucun résultat clinique simulé n'est généré."
                )
            sim_result = self._run_simulation()
            sim_result["is_simulation"] = True
            sim_result["simulation_warning"] = (
                "⚠️ SIMULATION — Le modèle IA panoramique n'est pas disponible sur ce poste. Ces résultats sont FICTIFS et ne doivent PAS être utilisés cliniquement."
            )
            return sim_result
        try:
            original_img = cv2.imread(image_path)
            if original_img is None:
                raise ValueError("Image illisible")
            processed_img = self._apply_clahe(original_img)
            processed_img = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
            img_padded, r, (dw, dh) = self._letterbox(processed_img, (self.input_size, self.input_size))
            img_in = img_padded.astype(np.float32) / 255.0
            img_in = np.transpose(img_in, (2, 0, 1))[np.newaxis, :]
            start_time = time.perf_counter()
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: img_in})
            output = outputs[0][0]
            detections = []
            class_thresholds = {"Lésion Périapicale": 0.12, "Carie": 0.22, "Carie Profonde": 0.22, "Dent Incluse": 0.30}
            for i in range(output.shape[1]):
                scores = output[4:, i]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                class_name = self.classes[class_id] if class_id < len(self.classes) else "Inconnu"
                threshold = class_thresholds.get(class_name, 0.25)
                if confidence > threshold:
                    xc, yc, wb, hb = output[:4, i]
                    x_rel = (xc - dw) / (self.input_size - 2*dw)
                    y_rel = (yc - dh) / (self.input_size - 2*dh)
                    tooth_fdi = self._map_fdi_elite(x_rel, y_rel)
                    x1 = (xc - wb/2 - dw) / r
                    y1 = (yc - hb/2 - dh) / r
                    x2 = (xc + wb/2 - dw) / r
                    y2 = (yc + hb/2 - dh) / r
                    detections.append({
                        "pathology": class_name,
                        "label": class_name,
                        "confidence": float(confidence),
                        "tooth": int(tooth_fdi),
                        "fdi": int(tooth_fdi),
                        "bbox": {
                            "x_min": float(round(x1, 1)),
                            "y_min": float(round(y1, 1)),
                            "x_max": float(round(x2, 1)),
                            "y_max": float(round(y2, 1)),
                            "confidence": float(confidence)
                        }
                    })
            refined_detections = self._apply_nms(detections)
            exec_time = time.perf_counter() - start_time
            return {
                "status": "SUCCESS",
                "mode_inference": "PRODUCTION_ELITE_YOLO11x",
                "detections_data": {"detections": refined_detections, "summary": f"{len(refined_detections)} anomalies identifiées"},
                "processing_time_ms": round(exec_time * 1000, 2)
            }
        except Exception as e:
            logger.error(f"PanoramicEngine Error : {e}")
            if _is_clinical_environment():
                raise
            sim_result = self._run_simulation()
            sim_result["is_simulation"] = True
            sim_result["simulation_warning"] = "Erreur d'inférence IA panoramique. Les résultats affichés sont une simulation et ne doivent pas être utilisés cliniquement."
            sim_result["runtime_error"] = str(e)
            return sim_result

    def _map_fdi_elite(self, x_rel: float, y_rel: float) -> int:
        x_rel = max(0, min(1, x_rel))
        y_rel = max(0, min(1, y_rel))
        curvature = 0.15
        center_y = 0.52
        occlusal_y = curvature * (x_rel - 0.5)**2 + center_y
        is_upper = y_rel < occlusal_y
        is_right_side = x_rel < 0.5
        quadrant = (1 if is_right_side else 2) if is_upper else (4 if is_right_side else 3)
        dist_from_center = abs(x_rel - 0.5) * 2
        if dist_from_center < 0.08: tooth_num = 1
        elif dist_from_center < 0.15: tooth_num = 2
        elif dist_from_center < 0.22: tooth_num = 3
        elif dist_from_center < 0.30: tooth_num = 4
        elif dist_from_center < 0.38: tooth_num = 5
        elif dist_from_center < 0.55: tooth_num = 6
        elif dist_from_center < 0.75: tooth_num = 7
        else: tooth_num = 8
        return quadrant * 10 + tooth_num

    def _apply_nms(self, detections: List[Dict]) -> List[Dict]:
        if not detections:
            return []
        sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        refined = []
        for det in sorted_dets:
            is_duplicate = False
            for r in refined:
                if r['fdi'] == det['fdi'] and r['pathology'] == det['pathology']:
                    b1, b2 = det['bbox'], r['bbox']
                    c1 = [(b1['x_min'] + b1['x_max'])/2, (b1['y_min'] + b1['y_max'])/2]
                    c2 = [(b2['x_min'] + b2['x_max'])/2, (b2['y_min'] + b2['y_max'])/2]
                    dist = ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)**0.5
                    if dist < 50:
                        is_duplicate = True
                        break
            if not is_duplicate:
                refined.append(det)
        return refined

    def _run_simulation(self) -> dict:
        return {"status": "MOCK", "mode_inference": "SIMULATION_EXPERT", "detections_data": {"detections": []}}

panoramic_engine = PanoramicEngine()
