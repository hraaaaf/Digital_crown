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
    "Caries": "Carie",
    "Crown": "Couronne",
    "Filling": "Obturation",
    "Implant": "Implant",
    "Malaligned": "Malposition",
    "Mandibular Canal": "Canal Mandibulaire",
    "Missing teeth": "Dent absente",
    "Periapical lesion": "Lésion périapicale",
    "Retained root": "Racine résiduelle",
    "Root Canal Treatment": "Traitement endodontique",
    "Root Piece": "Fragment radiculaire",
    "Impacted tooth": "Dent incluse",
    "Maxillary sinus": "Sinus maxillaire",
    "Bone Loss": "Perte osseuse",
    "Fractured teeth": "Dent fracturée",
    "Permanent Teeth": "Dent permanente",
    "Supra Eruption": "Égression",
    "TAD": "Minivis (TAD)",
    "Abutment": "Pilier implantaire",
    "Attrition": "Attrition",
    "Bone defect": "Défaut osseux",
    "Gingival former": "Vis de cicatrisation",
    "Metal band": "Bague orthodontique",
    "Orthodontic brackets": "Bracket orthodontique",
    "Permanent retainer": "Contention collée",
    "Post-core": "Inlay-core",
    "Plating": "Plaque d'ostéosynthèse",
    "Wire": "Arc orthodontique",
    "Cyst": "Kyste",
    "Root resorption": "Résorption radiculaire",
    "Primary teeth": "Dent temporaire"
}

# Mapping exact extrait des métadonnées du fichier best.pt (31 classes)
PANORAMIC_INDEX_MAPPING = {
    0: "Caries", 1: "Crown", 2: "Filling", 3: "Implant", 4: "Malaligned", 
    5: "Mandibular Canal", 6: "Missing teeth", 7: "Periapical lesion", 8: "Retained root", 
    9: "Root Canal Treatment", 10: "Root Piece", 11: "Impacted tooth", 12: "Maxillary sinus", 
    13: "Bone Loss", 14: "Fractured teeth", 15: "Permanent Teeth", 16: "Supra Eruption", 
    17: "TAD", 18: "Abutment", 19: "Attrition", 20: "Bone defect", 21: "Gingival former", 
    22: "Metal band", 23: "Orthodontic brackets", 24: "Permanent retainer", 25: "Post-core", 
    26: "Plating", 27: "Wire", 28: "Cyst", 29: "Root resorption", 30: "Primary teeth"
}

class PanoramicEngine:
    """
    Moteur d'inférence ONNX pour les radiographies panoramiques (OPG).
    Utilise le modèle Loki-Silvres converti pour une performance CPU optimale.
    """
    def __init__(self):
        self.session = None
        self.is_ready = False
        self.input_size = 1280  # Le modèle Loki-Silvres attend 1280x1280
        
        # Pointons vers le nouveau modèle optimisé (YOLOv8x-seg à 31 classes)
        self.model_path = os.path.join("backend", "ai_models", "best.onnx")
        
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
            start_time = time.perf_counter()
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: img_input})
            
            # YOLOv8x-seg output shape: [1, 67, 33600]
            output = outputs[0][0] 
            
            # Tâche 3.1 : Tranchage du Tenseur et Vectorisation
            output = output[:35, :] # Ignorer les 32 canaux de masque
            output = output.T       # (33600, 35)
            
            scores = output[:, 4:35]
            class_ids = np.argmax(scores, axis=1)
            confidences = np.max(scores, axis=1)
            
            # Thresholding initial
            conf_threshold = 0.15
            mask = confidences > conf_threshold
            
            filtered_output = output[mask]
            filtered_class_ids = class_ids[mask]
            filtered_confidences = confidences[mask]
            
            detections_raw = []
            if len(filtered_output) > 0:
                boxes_np = filtered_output[:, :4]
                xc = boxes_np[:, 0]
                yc = boxes_np[:, 1]
                w = boxes_np[:, 2]
                h = boxes_np[:, 3]
                
                # Conversion top-left pour cv2.dnn.NMSBoxes
                x_tl = (xc - w/2 - dw) / scale
                y_tl = (yc - h/2 - dh) / scale
                w_scaled = w / scale
                h_scaled = h / scale
                
                bboxes_list = np.column_stack((x_tl, y_tl, w_scaled, h_scaled)).tolist()
                scores_list = filtered_confidences.tolist()
                
                # Tâche 3.1 : Exécution NMSBoxes vectorisée (Class-aware NMS)
                # On ajoute un grand décalage basé sur la classe pour séparer mathématiquement les classes lors du NMS
                max_coord = 10000
                bboxes_shifted = []
                for i, box in enumerate(bboxes_list):
                    c = filtered_class_ids[i]
                    bboxes_shifted.append([box[0] + c * max_coord, box[1] + c * max_coord, box[2], box[3]])
                    
                indices = cv2.dnn.NMSBoxes(bboxes_shifted, scores_list, conf_threshold, 0.45)
                indices = indices.flatten() if len(indices) > 0 else []
                
                for i in indices:
                    x, y, bw, bh = bboxes_list[i]
                    x1, y1 = x, y
                    x2, y2 = x + bw, y + bh
                    class_id = filtered_class_ids[i]
                    conf = scores_list[i]
                    
                    detections_raw.append({
                        "class_id": class_id,
                        "pathology": PANORAMIC_INDEX_MAPPING.get(class_id, "Unknown"),
                        "confidence": float(conf),
                        "bbox": [float(round(x1, 1)), float(round(y1, 1)), float(round(x2, 1)), float(round(y2, 1))]
                    })

            # Tâche 3.2 : Heuristique d'Assignation FDI via Barycentre Dynamique
            teeth_centers = []
            for d in detections_raw:
                bbox = d["bbox"]
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                # Considérer les dents permanentes (15), primaires (30) et quelques ancres fiables
                if d["class_id"] in [1, 3, 6, 11, 14, 15, 30]:
                    teeth_centers.append((cx, cy))
            
            if teeth_centers:
                avg_cx = sum(c[0] for c in teeth_centers) / len(teeth_centers)
                avg_cy = sum(c[1] for c in teeth_centers) / len(teeth_centers)
            else:
                avg_cx = original_img.shape[1] / 2
                avg_cy = original_img.shape[0] / 2

            # Calcul de la largeur moyenne d'une dent (pour la détection des gaps)
            tooth_widths = [d["bbox"][2] - d["bbox"][0] for d in detections_raw if d["class_id"] in [1, 3, 6, 11, 14, 15, 30]]
            avg_width = sum(tooth_widths) / len(tooth_widths) if tooth_widths else original_img.shape[1] / 16

            # Tâche 3.2 : Clustering et Assignation FDI Intelligente (Gap-Aware)
            general_findings = []
            tooth_items = []
            
            for d in detections_raw:
                if d["class_id"] in [5, 12, 13, 20, 28]: # Canal mand., Sinus, Perte osseuse, Défaut, Kyste
                    general_findings.append({
                        "label": PANORAMIC_LABELS_MAPPING.get(d["pathology"], d["pathology"]),
                        "confidence": d["confidence"],
                        "bbox": {
                            "x_min": d["bbox"][0], "y_min": d["bbox"][1],
                            "x_max": d["bbox"][2], "y_max": d["bbox"][3],
                            "confidence": d["confidence"]
                        }
                    })
                else:
                    tooth_items.append(d)

            # Division en quadrants
            quadrants = {1: [], 2: [], 3: [], 4: []}
            for d in tooth_items:
                bbox = d["bbox"]
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                is_upper = cy < avg_cy
                is_right_side = cx < avg_cx # Droite patient = Gauche image (X petit)
                q = (1 if is_right_side else 2) if is_upper else (4 if is_right_side else 3)
                quadrants[q].append({"det": d, "cx": cx})

            teeth_map = {}
            for q, items in quadrants.items():
                if not items: continue
                
                # Tri depuis la ligne médiane vers l'extérieur
                # Q1 et Q4 sont à gauche de l'image (X < avg_cx). Pour partir du centre (avg_cx) vers l'extérieur, on doit aller de grand X vers petit X (reverse=True)
                reverse_sort = True if q in [1, 4] else False
                items.sort(key=lambda x: x["cx"], reverse=reverse_sort)
                
                # Regroupement des détections superposées (ex: Carie + Dent = même cluster)
                clusters = []
                for item in items:
                    placed = False
                    for cluster in clusters:
                        if abs(item["cx"] - cluster["cx"]) < avg_width * 0.6:
                            cluster["items"].append(item["det"])
                            placed = True
                            break
                    if not placed:
                        clusters.append({"cx": item["cx"], "items": [item["det"]]})
                
                # Assignation des numéros avec détection d'espaces (gaps)
                current_tooth_num = 1
                prev_cx = avg_cx # Départ au milieu
                
                for cluster in clusters:
                    dist_to_prev = abs(cluster["cx"] - prev_cx)
                    
                    if prev_cx != avg_cx: # Sauf pour la première dent
                        # Combien d'espaces de dents on a franchi ?
                        gaps = int(round(dist_to_prev / avg_width))
                        if gaps > 1:
                            current_tooth_num += (gaps - 1)
                            
                    if current_tooth_num > 8:
                        current_tooth_num = 8
                        
                    fdi = q * 10 + current_tooth_num
                    
                    if fdi not in teeth_map:
                        teeth_map[fdi] = {
                            "fdi_number": fdi,
                            "bbox": None,
                            "findings": []
                        }
                    
                    for d in cluster["items"]:
                        label_fr = PANORAMIC_LABELS_MAPPING.get(d["pathology"], d["pathology"])
                        finding = {
                            "label": label_fr,
                            "confidence": d["confidence"],
                            "bbox": {
                                "x_min": d["bbox"][0], "y_min": d["bbox"][1],
                                "x_max": d["bbox"][2], "y_max": d["bbox"][3],
                                "confidence": d["confidence"]
                            }
                        }
                        if d["class_id"] in [15, 30]:
                            teeth_map[fdi]["bbox"] = finding["bbox"]
                        else:
                            teeth_map[fdi]["findings"].append(finding)
                            
                    prev_cx = cluster["cx"]
                    current_tooth_num += 1

            # Fallback pour les dents sans bounding box "Permanent Tooth"
            for fdi, tooth in teeth_map.items():
                if tooth["bbox"] is None and tooth["findings"]:
                    tooth["bbox"] = tooth["findings"][0]["bbox"]
            
            exec_time = time.perf_counter() - start_time
            
            full_analysis = {
                "teeth": list(teeth_map.values()),
                "general_findings": general_findings
            }

            return {
                "status": "SUCCESS",
                "detections_data": full_analysis,
                "processing_time_ms": round(exec_time * 1000, 2),
                "mode_inference": "PRODUCTION_ONNX_LOKI"
            }
            
        except Exception as e:
            logger.error(f"PanoramicEngine : Erreur d'inférence : {e}")
            return self._run_simulation()

    def _run_simulation(self):
        """Mode dégradé si le modèle est absent."""
        return {
            "status": "MOCK",
            "detections_data": {
                "teeth": [],
                "general_findings": []
            },
            "processing_time_ms": 0,
            "mode_inference": "MOCK_EXPERT"
        }

# Instance Singleton
panoramic_engine = PanoramicEngine()
