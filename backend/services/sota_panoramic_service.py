import os
import cv2
import numpy as np
import logging
from typing import List, Dict, Any

from backend.config import settings

try:
    import onnxruntime as ort
except ImportError:
    ort = None

logger = logging.getLogger(__name__)


def _is_production() -> bool:
    """En production, aucune simulation IA clinique silencieuse n'est tolérée (P0.8)."""
    return str(getattr(settings, "ENVIRONMENT", "development")).lower() == "production"

class SOTAPanoramicEngine:
    """
    Moteur Vision SOTA Elite pour radios panoramiques.
    Optimisé pour YOLO11x avec respect du ratio d'aspect (Letterbox).
    """
    
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, "ai_models", "panoramic_model.onnx")
        self.session = None
        self.classes = ["Caries", "Deep Caries", "Impacted", "Periapical Lesion"]
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
                clahe = cv2.createCLAHE(clipLimit=4.5, tileGridSize=(12, 12))
                cl = clahe.apply(l)
                img = cv2.merge((cl, a, b))
                return cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
            return img
        except: return img

    def analyze(self, image_path: str) -> Dict[str, Any]:
        if self.session is None:
            if _is_production():
                logger.error(
                    "SOTAPanoramicEngine : modèle ONNX indisponible en PRODUCTION — "
                    "analyse refusée (aucune simulation clinique silencieuse)."
                )
                raise RuntimeError(
                    "Modèle IA panoramique indisponible : l'analyse est refusée en production. "
                    "Aucun résultat clinique simulé n'est généré."
                )
            return self._run_simulation()

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
            # Seuils adaptatifs (Elite Standard)
            # Les lésions périapicales sont souvent plus subtiles aux apex
            class_thresholds = {
                "Periapical Lesion": 0.15,
                "Caries": 0.25,
                "Deep Caries": 0.25,
                "Impacted": 0.25
            }
            
            for i in range(output.shape[1]):
                scores = output[4:, i]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                class_name = self.classes[class_id] if class_id < len(self.classes) else "Inconnu"
                
                # Seuil spécifique à la classe ou défaut
                threshold = class_thresholds.get(class_name, 0.25)
                
                if confidence > threshold:
                    xc, yc, wb, hb = output[:4, i]
                    
                    # Coordonnées normalisées réelles (0-1)
                    x_rel = (xc - dw) / (self.input_size - 2*dw)
                    y_rel = (yc - dh) / (self.input_size - 2*dh)
                    
                    tooth_fdi = self._map_fdi_refined(x_rel, y_rel)
                    
                    x1 = (xc - wb/2 - dw) / r
                    y1 = (yc - hb/2 - dh) / r
                    x2 = (xc + wb/2 - dw) / r
                    y2 = (yc + hb/2 - dh) / r
                    
                    detections.append({
                        "pathology": class_name,
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
            if _is_production():
                logger.error(
                    "SOTAPanoramicEngine : erreur d'inférence en PRODUCTION — "
                    "propagation de l'erreur (aucune simulation clinique silencieuse)."
                )
                raise
            return self._run_simulation()

    def _map_fdi_refined(self, x_rel: float, y_rel: float) -> int:
        """
        Mapping FDI Elite avec compensation de la 'Smile Curve' (Parabole occlusale).
        """
        x_rel = max(0, min(1, x_rel))
        y_rel = max(0, min(1, y_rel))
        
        # 1. Équation de la Smile Curve (Occlusal Plane)
        # y = a(x-0.5)^2 + k
        # k est le centre vertical (env 0.52), a est la courbure (positif = bords remontent)
        curvature = 0.15
        center_y = 0.52
        occlusal_y = curvature * (x_rel - 0.5)**2 + center_y
        
        is_upper = y_rel < occlusal_y
        is_right_side = x_rel < 0.5 # Dans une radio, le côté DROIT du patient est à GAUCHE de l'image
        
        # Quadrants FDI : 1 (Haut Droit), 2 (Haut Gauche), 3 (Bas Gauche), 4 (Bas Droit)
        if is_upper:
            quadrant = 1 if is_right_side else 2
        else:
            quadrant = 4 if is_right_side else 3
            
        # 2. Distribution X non-linéaire des dents (Calibration Elite v1.5.1)
        dist_from_center = abs(x_rel - 0.5) * 2 # 0 à 1
        
        if dist_from_center < 0.08: tooth_num = 1    # Centrales
        elif dist_from_center < 0.14: tooth_num = 2  # Latérales
        elif dist_from_center < 0.20: tooth_num = 3  # Canines
        elif dist_from_center < 0.28: tooth_num = 4  # 1ères Prémos
        elif dist_from_center < 0.36: tooth_num = 5  # 2èmes Prémos
        elif dist_from_center < 0.55: tooth_num = 6  # 1ères Molaires
        elif dist_from_center < 0.75: tooth_num = 7  # 2èmes Molaires
        else: tooth_num = 8                          # Dents de sagesse
        
        return quadrant * 10 + tooth_num

    def _apply_smart_nms(self, detections: List[Dict]) -> List[Dict]:
        if not detections: return []
        # Tri par confiance décroissante
        sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        refined = []
        
        for det in sorted_dets:
            is_duplicate = False
            for r in refined:
                # Si même dent et même pathologie, on vérifie la proximité
                if r['tooth'] == det['tooth'] and r['pathology'] == det['pathology']:
                    b1, b2 = det['bbox'], r['bbox']
                    # Calcul de l'IoU simple ou distance des centres
                    c1 = [(b1[0] + b1[2])/2, (b1[1] + b1[3])/2]
                    c2 = [(b2[0] + b2[2])/2, (b2[1] + b2[3])/2]
                    dist = ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)**0.5
                    
                    # Seuil de proximité dynamique (environ 5% de la largeur image typique)
                    if dist < 60: 
                        is_duplicate = True
                        break
            if not is_duplicate: refined.append(det)
            
        return refined

    def _run_simulation(self) -> Dict[str, Any]:
        """
        Simulation de la nouvelle vision produit : On retourne uniquement les Bounding Boxes des 32 dents.
        Aucune pathologie n'est devinée par l'IA (Friction Zéro). C'est le dentiste qui cliquera.
        """
        teeth_detections = []
        
        # Dimensions standards d'une radio pano (simulation)
        img_w, img_h = 1280, 640
        center_y = img_h * 0.52
        curvature = 0.15
        
        # Quadrants : Haut Droit (1), Haut Gauche (2), Bas Gauche (3), Bas Droit (4)
        for quad in [1, 2, 3, 4]:
            is_upper = quad in [1, 2]
            is_right_side = quad in [1, 4] # Droite du patient = gauche de l'image
            
            for tooth_idx in range(1, 9):
                # Calcul de la position X
                # Distance depuis le centre
                dist_factor = {1: 0.04, 2: 0.11, 3: 0.17, 4: 0.24, 5: 0.32, 6: 0.45, 7: 0.65, 8: 0.85}[tooth_idx]
                x_rel = 0.5 - (dist_factor / 2.0) if is_right_side else 0.5 + (dist_factor / 2.0)
                
                # Calcul de la position Y (Smile Curve)
                occlusal_y = curvature * (x_rel - 0.5)**2 + center_y
                
                # Taille de la dent
                tooth_w = 40 if tooth_idx < 4 else 60 # Molaires plus larges
                tooth_h = 80 if is_upper else 70
                
                # Bounding box
                cx = x_rel * img_w
                cy = occlusal_y - (tooth_h/2) if is_upper else occlusal_y + (tooth_h/2)
                
                bbox = [
                    cx - tooth_w/2,
                    cy - tooth_h/2,
                    cx + tooth_w/2,
                    cy + tooth_h/2
                ]
                
                teeth_detections.append({
                    "tooth": quad * 10 + tooth_idx,
                    "confidence": 0.99, # IA très confiante sur la détection des dents
                    "bbox": [round(b, 1) for b in bbox],
                    "pathology": "None" # La pathologie sera définie par le médecin via l'UI
                })

        return {
            "status": "SIMULATED_INTERACTIVE_GRID",
            "inference_mode": "TOOTH_DETECTION_ONLY",
            "detections": teeth_detections
        }

panoramic_engine = SOTAPanoramicEngine()
