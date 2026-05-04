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

# Mapping des labels YOLO (Loki-Silvres / Dentex) vers les termes cliniques français
PANORAMIC_LABELS_MAPPING = {
    "Impacted": "Dent incluse",
    "Caries": "Carie dentaire",
    "Periapical Lesion": "Lésion périapicale",
    "Deep Caries": "Carie profonde",
    "Implant": "Implant dentaire",
    "Crown": "Couronne / Prothèse",
    "Endodontic": "Traitement canalaire",
    "Missing": "Agénésie / Absence",
    "Restoration": "Obturation / Composite"
}

# Mapping des indices (si le modèle renvoie des entiers)
# Basé sur la nomenclature standard Dentex/YOLO
PANORAMIC_INDEX_MAPPING = {
    0: "Impacted",
    1: "Caries",
    2: "Periapical Lesion",
    3: "Deep Caries",
    4: "Implant",
    5: "Crown",
    6: "Endodontic",
    7: "Restoration"
}

class PanoramicEngine:
    """
    Moteur d'inférence ONNX pour les radiographies panoramiques (OPG).
    Utilise le modèle Loki-Silvres converti pour une performance CPU optimale.
    """
    def __init__(self):
        self.session = None
        self.is_ready = False
        self.input_size = 640  # Standard YOLOv8/v11
        
        # Chemins potentiels
        self.model_path = os.path.join("backend", "ai_models", "panoramic_model.onnx")
        
    async def initialize(self):
        """Initialisation asynchrone appelée au démarrage de FastAPI."""
        if ort is None:
            logger.error("PanoramicEngine : ONNX Runtime n'est pas installé.")
            return

        if not os.path.exists(self.model_path):
            logger.warning(f"PanoramicEngine : Modèle {self.model_path} introuvable. Inférence désactivée.")
            return

        try:
            logger.info(f"PanoramicEngine : Initialisation du runtime ONNX sur {self.model_path}...")
            start_time = time.time()
            
            # Configuration des providers (DirectML pour accélération Windows si dispo, sinon CPU)
            available_providers = ort.get_available_providers()
            providers = []
            if 'DmlExecutionProvider' in available_providers:
                providers.append('DmlExecutionProvider')
            providers.append('CPUExecutionProvider')

            # Chargement de la session
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.is_ready = True
            
            logger.info(f"PanoramicEngine : Modèle chargé avec succès en {time.time() - start_time:.2f}s (Provider: {self.session.get_providers()[0]})")
        except Exception as e:
            logger.error(f"PanoramicEngine : Échec de l'initialisation : {e}")

    def _preprocess(self, img):
        """
        Pré-processing de l'image (Letterboxing + Normalisation).
        Préserve l'aspect ratio en ajoutant des bandes (padding).
        """
        h, w = img.shape[:2]
        
        # Calcul du scale pour conserver le ratio
        scale = min(self.input_size / h, self.input_size / w)
        nh, nw = int(h * scale), int(w * scale)
        
        img_resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        
        # Création d'un canevas carré (gris neutre YOLO = 114)
        canvas = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        
        # Centrage de l'image redimensionnée
        top = (self.input_size - nh) // 2
        left = (self.input_size - nw) // 2
        canvas[top:top+nh, left:left+nw] = img_resized
        
        # Conversion BGR (OpenCV) -> RGB
        img_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        
        # Normalisation 0.0 - 1.0
        img_norm = img_rgb.astype(np.float32) / 255.0
        
        # HWC -> NCHW (Format attendu par ONNX)
        img_input = np.transpose(img_norm, (2, 0, 1))[np.newaxis, :]
        
        return img_input, scale, (left, top)

    def predict(self, image_path: str) -> dict:
        """
        Pipeline complet : Lecture -> Pré-processing -> Inférence ONNX -> Post-processing -> FDI Mapping.
        """
        if not self.is_ready:
            logger.warning("PanoramicEngine : Session ONNX non initialisée. Retour mode simulation.")
            return self._run_simulation()

        try:
            # 1. Chargement et Pré-processing
            original_img = cv2.imread(image_path)
            if original_img is None: raise ValueError("Image illisible")
            
            img_input, scale, (dw, dh) = self._preprocess(original_img)
            
            # 2. Inférence ONNX
            start_time = time.time()
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: img_input})
            
            # YOLOv8/v11 output shape: [1, 4 + num_classes, 8400]
            # On récupère le premier batch
            output = outputs[0][0] 
            
            # 3. Post-processing
            detections = []
            conf_threshold = 0.25
            
            # Liste des classes (doit correspondre au modèle Loki-Silvres)
            classes = list(PANORAMIC_INDEX_MAPPING.values())
            
            # Transposer pour avoir [8400, 4 + num_classes]
            output = output.transpose()
            
            for row in output:
                scores = row[4:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > conf_threshold:
                    xc, yc, wb, hb = row[:4]
                    
                    # Conversion vers coordonnées relatives (0-1) dans le canevas 640x640
                    # Puis conversion vers l'image originale en enlevant le padding
                    x_rel = (xc - dw) / (self.input_size - 2*dw)
                    y_rel = (yc - dh) / (self.input_size - 2*dh)
                    
                    # Mapping FDI
                    tooth_fdi = self._map_fdi_refined(x_rel, y_rel)
                    
                    # Bounding Box en pixels (format x1, y1, x2, y2)
                    x1 = (xc - wb/2 - dw) / scale
                    y1 = (yc - hb/2 - dh) / scale
                    x2 = (xc + wb/2 - dw) / scale
                    y2 = (yc + hb/2 - dh) / scale
                    
                    detections.append({
                        "pathology": classes[class_id] if class_id < len(classes) else "unknown",
                        "confidence": float(confidence),
                        "tooth": int(tooth_fdi),
                        "bbox": [float(round(x1, 1)), float(round(y1, 1)), float(round(x2, 1)), float(round(y2, 1))]
                    })

            # 4. Suppression des doublons (NMS simplifié)
            final_detections = self._apply_nms(detections)
            
            exec_time = time.time() - start_time
            return {
                "status": "SUCCESS",
                "detections": final_detections,
                "processing_time_ms": round(exec_time * 1000, 2),
                "mode_inference": "PRODUCTION_ONNX_LOKI"
            }
            
        except Exception as e:
            logger.error(f"PanoramicEngine : Erreur d'inférence : {e}")
            return self._run_simulation()

    def _map_fdi_refined(self, x_rel: float, y_rel: float) -> int:
        """Mapping FDI avec compensation de la courbure occlusale (Smile Curve)."""
        x_rel = max(0, min(1, x_rel))
        y_rel = max(0, min(1, y_rel))
        
        # Équation simplifiée de la Smile Curve (parabole)
        curvature = 0.15
        center_y = 0.52
        occlusal_y = curvature * (x_rel - 0.5)**2 + center_y
        
        is_upper = y_rel < occlusal_y
        is_right_side = x_rel < 0.5 # Radio inversée : droite patient = gauche image
        
        if is_upper:
            quadrant = 1 if is_right_side else 2
        else:
            quadrant = 4 if is_right_side else 3
            
        # Distribution horizontale des dents
        dist = abs(x_rel - 0.5) * 2
        if dist < 0.08: tooth = 1
        elif dist < 0.14: tooth = 2
        elif dist < 0.20: tooth = 3
        elif dist < 0.28: tooth = 4
        elif dist < 0.36: tooth = 5
        elif dist < 0.55: tooth = 6
        elif dist < 0.75: tooth = 7
        else: tooth = 8
        
        return quadrant * 10 + tooth

    def _apply_nms(self, detections, iou_threshold=0.45):
        """Non-Maximum Suppression simplifiée par proximité."""
        if not detections: return []
        sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        keep = []
        
        for det in sorted_dets:
            overlap = False
            for k in keep:
                if k['tooth'] == det['tooth'] and k['pathology'] == det['pathology']:
                    # Calcul de distance des centres
                    b1, b2 = det['bbox'], k['bbox']
                    c1 = [(b1[0]+b1[2])/2, (b1[1]+b1[3])/2]
                    c2 = [(b2[0]+b2[2])/2, (b2[1]+b2[3])/2]
                    dist = ((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)**0.5
                    if dist < 50: # Seuil de proximité en pixels
                        overlap = True
                        break
            if not overlap:
                keep.append(det)
        return keep

    def _run_simulation(self):
        """Mode dégradé si le modèle est absent."""
        return {
            "status": "MOCK",
            "detections": [
                {"tooth": 18, "pathology": "Impacted", "confidence": 0.95, "bbox": [50, 50, 150, 150]},
                {"tooth": 36, "pathology": "Caries", "confidence": 0.85, "bbox": [400, 300, 480, 380]}
            ],
            "processing_time_ms": 0,
            "mode_inference": "MOCK_EXPERT"
        }

# Instance Singleton
panoramic_engine = PanoramicEngine()
