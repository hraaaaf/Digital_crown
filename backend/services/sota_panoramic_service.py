import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Any

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = logging.getLogger(__name__)

class SOTAPanoramicEngine:
    """
    Moteur Vision SOTA Elite pour radios panoramiques.
    Optimisé pour YOLO11x avec respect du ratio d'aspect (Letterbox).
    """
    
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, "ai_models", "panoramic_model.onnx")
        self.session = None
        self.classes = ["Caries", "Deep Caries", "Periapical Lesions", "Impacted Teeth"]
        self.input_size = 1280
        self._load_model()

    def _load_model(self):
        if ort is None: return
        if os.path.exists(self.model_path):
            try:
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 4 
                self.session = ort.InferenceSession(self.model_path, sess_options=opts)
                logger.info(f"✅ Moteur SOTA Panoramique active : {self.model_path}")
            except Exception as e:
                logger.error(f"❌ Erreur ONNX : {e}")

    def _letterbox(self, img: np.ndarray, new_shape=(1280, 1280)) -> tuple:
        shape = img.shape[:2] # [h, w]
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
                clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                img = cv2.merge((cl, a, b))
                return cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
            return img
        except: return img

    def analyze(self, image_path: str) -> Dict[str, Any]:
        if self.session is None: return self._run_simulation()

        try:
            original_img = cv2.imread(image_path)
            if original_img is None: raise ValueError("Image illisible")
            
            h0, w0 = original_img.shape[:2]
            processed_img = self._apply_clahe(original_img)
            processed_img = cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB)
            
            img_padded, r, (dw, dh) = self._letterbox(processed_img, (self.input_size, self.input_size))
            
            img_in = img_padded.astype(np.float32) / 255.0
            img_in = np.transpose(img_in, (2, 0, 1))
            img_in = np.expand_dims(img_in, axis=0)

            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: img_in})
            
            output = outputs[0][0] 
            detections = []
            conf_threshold = 0.10
            
            for i in range(output.shape[1]):
                scores = output[4:, i]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > conf_threshold:
                    xc, yc, wb, hb = output[:4, i]
                    
                    # Mapping FDI sur coordonnées RÉELLES (sans padding)
                    x_orig_rel = (xc - dw) / (self.input_size - 2*dw)
                    y_orig_rel = (yc - dh) / (self.input_size - 2*dh)
                    tooth_fdi = self._map_fdi_refined(x_orig_rel, y_orig_rel)
                    
                    x1 = (xc - wb/2 - dw) / r
                    y1 = (yc - hb/2 - dh) / r
                    x2 = (xc + wb/2 - dw) / r
                    y2 = (yc + hb/2 - dh) / r
                    
                    detections.append({
                        "pathology": self.classes[class_id] if class_id < len(self.classes) else "Inconnu",
                        "confidence": float(confidence),
                        "tooth": int(tooth_fdi),
                        "bbox": [float(round(x1, 1)), float(round(y1, 1)), float(round(x2, 1)), float(round(y2, 1))]
                    })

            refined_detections = self._apply_smart_nms(detections)

            return {
                "status": "SUCCESS",
                "inference_mode": "LOCAL_SOTA_YOLO11x",
                "detections": sorted(refined_detections, key=lambda x: x['confidence'], reverse=True)[:50]
            }
        except Exception as e:
            logger.error(f"⚠️ Inference Error : {e}")
            return self._run_simulation()

    def _map_fdi_refined(self, x_rel: float, y_rel: float) -> int:
        # Assurer que x_rel et y_rel sont entre 0 et 1 (protection contre le clipping)
        x_rel = max(0, min(1, x_rel))
        y_rel = max(0, min(1, y_rel))
        
        dist_from_center = abs(x_rel - 0.5) * 2
        y_sep = 0.54 - (0.08 * dist_from_center) 
        is_upper = y_rel < y_sep
        is_right_side = x_rel < 0.5
        quadrant = (1 if is_right_side else 2) if is_upper else (4 if is_right_side else 3)
        
        if dist_from_center < 0.08: tooth_num = 1
        elif dist_from_center < 0.17: tooth_num = 2
        elif dist_from_center < 0.28: tooth_num = 3
        elif dist_from_center < 0.40: tooth_num = 4
        elif dist_from_center < 0.52: tooth_num = 5
        elif dist_from_center < 0.68: tooth_num = 6
        elif dist_from_center < 0.84: tooth_num = 7
        else: tooth_num = 8
        return quadrant * 10 + tooth_num

    def _apply_smart_nms(self, detections: List[Dict]) -> List[Dict]:
        if not detections: return []
        sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        refined = []
        for det in sorted_dets:
            is_duplicate = False
            for r in refined:
                if r['tooth'] == det['tooth'] and r['pathology'] == det['pathology']:
                    b1, b2 = det['bbox'], r['bbox']
                    c1 = [(b1[0] + b1[2])/2, (b1[1] + b1[3])/2]
                    c2 = [(b2[0] + b2[2])/2, (b2[1] + b2[3])/2]
                    dist = ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)**0.5
                    if dist < 40: 
                        is_duplicate = True
                        break
            if not is_duplicate: refined.append(det)
        return refined

    def _run_simulation(self) -> Dict[str, Any]:
        return {
            "status": "SIMULATED",
            "inference_mode": "FALLBACK_EXPERT",
            "detections": [
                {"tooth": 18, "pathology": "Impacted Teeth", "confidence": 0.94, "bbox": [100.0, 100.0, 300.0, 300.0]},
                {"tooth": 36, "pathology": "Caries", "confidence": 0.88, "bbox": [800.0, 600.0, 950.0, 750.0]}
            ]
        }

panoramic_engine = SOTAPanoramicEngine()
