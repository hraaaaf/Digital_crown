import sys
import os
import time
import logging
import cv2
import numpy as np

# --- 0. MONKEY PATCH POUR LE CODE LEGACY (PILLOW_VERSION) ---
# Empêche le crash de l'import torchvision/CephLD-CCA lié à Pillow > 7.0.0
import PIL
if not hasattr(PIL, 'PILLOW_VERSION'):
    PIL.PILLOW_VERSION = PIL.__version__
# ------------------------------------------------------------

# --- 1. INJECTION DYNAMIQUE DU CHEMIN (HACK NAMESPACE) ---
# Résolution du problème d'imports absolus du repository de recherche 'CephLD-CCA'
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.abspath(os.path.join(current_dir, "..", "ai_models", "cephld_cca"))

if repo_path not in sys.path:
    sys.path.insert(0, repo_path)

# --- 2. IMPORTATIONS SÉCURISÉES ---
# Gestion gracieuse de PyTorch pour éviter un crash serveur si l'environnement n'est pas prêt
try:
    import torch
except ImportError:
    torch = None

try:
    # L'importation s'appuie désormais sur le sys.path injecté et le patch Pillow
    from models.unet_w_cartesian_se import U_Net_w_Cartesian_SE
except ImportError as e:
    U_Net_w_Cartesian_SE = None
    logging.getLogger(__name__).warning(f"ATTENTION : Impossible d'importer U_Net_w_Cartesian_SE : {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- NOMENCLATURE DES 19 POINTS (Standard ISBI 2015 officiel) ---
CEPH_LANDMARKS_MAPPING = {
    0: "S", 1: "N", 2: "Or", 3: "Po", 4: "A", 5: "B", 6: "Pog", 7: "Me",
    8: "Gn", 9: "Go", 10: "L1_incisal", 11: "U1_incisal", 12: "UL",
    13: "LL", 14: "Sn", 15: "Pog_soft", 16: "PNS", 17: "ANS", 18: "Ar"
}

class VisionEngine:
    """
    Moteur d'Inférence Deep Learning PyTorch pour la détection de points céphalométriques.
    Implémentation Singleton pour l'architecture CephLD-CCA (U-Net + Cartesian SE).
    """

    def __init__(self):
        self.target_size = 512
        self.num_landmarks = 19
        self.model = None
        self.is_ready = False
        
        # Configuration agnostique du device (GPU si dispo, sinon CPU)
        if torch is not None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = "cpu"
            
        # Chemin vers les poids du modèle PyTorch
        self.weights_path = os.path.join(repo_path, "ceph_weights.pth")
        
        self._initialize_engine()

    def _initialize_engine(self):
        """Charge le modèle PyTorch en mémoire au démarrage du serveur Uvicorn."""
        if torch is None:
            logger.error("CRITIQUE : PyTorch n'est pas installé. L'inférence vision basculera en mode MOCK.")
            return

        if U_Net_w_Cartesian_SE is None:
            logger.error("CRITIQUE : Classe du modèle introuvable. Vérifiez les dépendances internes du repo. Mode MOCK activé.")
            return

        if not os.path.exists(self.weights_path):
            logger.error(f"CRITIQUE : Poids du modèle introuvables à {self.weights_path}. Mode MOCK activé.")
            return

        try:
            logger.info(f"VisionEngine : Chargement du modèle PyTorch sur [{self.device.type.upper()}]...")
            start_time = time.time()
            
            # Instanciation du modèle : 1 canal en entrée (grayscale), 19 canaux en sortie (heatmaps)
            self.model = U_Net_w_Cartesian_SE(img_ch=1, output_ch=self.num_landmarks)
            
            # Chargement strict des poids avec map_location pour éviter les crashs CUDA -> CPU
            state_dict = torch.load(self.weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval() # Verrouillage en mode inférence (désactive le dropout/batchnorm training)
            
            self.is_ready = True
            logger.info(f"VisionEngine : Modèle PyTorch chargé avec succès en {time.time() - start_time:.2f}s.")
            
        except Exception as e:
            logger.error(f"Échec critique du chargement du modèle Vision PyTorch : {e}")

    def predict_landmarks(self, file_location: str) -> dict:
        """
        Exécute la pipeline complète : Lecture -> Tensor -> U-Net -> Heatmaps -> Coordonnées Absolues.
        
        Retourne un dictionnaire contenant:
        - landmarks: Liste des points détectés
        - mode_inference: "PRODUCTION" ou "MOCK" 
        - warning: Message d'avertissement si mode MOCK
        - processing_time_ms: Temps de traitement
        """
        start_time = time.time()
        
        # 1. Pre-processing : Lecture OpenCV stricte en niveaux de gris
        img = cv2.imread(file_location, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Impossible de lire l'image à l'emplacement : {file_location}")
            
        orig_h, orig_w = img.shape
        
        # 2. Facteurs d'échelle pour le Post-processing
        scale_x = orig_w / float(self.target_size)
        scale_y = orig_h / float(self.target_size)

        final_landmarks = []
        mode_inference = "PRODUCTION"
        warning_msg = None

        # 3. Mode Inférence Réelle PyTorch
        if self.is_ready and self.model is not None and torch is not None:
            
            # Redimensionnement et normalisation
            img_resized = cv2.resize(img, (self.target_size, self.target_size))
            img_normalized = img_resized.astype(np.float32) / 255.0
            
            # Conversion en Tensor format (Batch=1, Channels=1, Height=512, Width=512)
            input_tensor = torch.tensor(img_normalized).unsqueeze(0).unsqueeze(0).to(self.device)
            
            # Inférence sans calcul de gradients pour la performance
            with torch.no_grad():
                output_tensor = self.model(input_tensor) # Sortie attendue : (1, 19, 512, 512)
                
            # Rapatriement sur CPU et conversion Numpy pour le post-processing
            heatmaps = output_tensor.squeeze(0).cpu().numpy() # Shape : (19, 512, 512)
            
            # 4. Post-processing : Extraction des pics d'activation
            for idx in range(self.num_landmarks):
                heatmap = heatmaps[idx]
                
                # argmax retourne l'index 1D du pixel le plus chaud de la matrice 512x512
                flat_idx = np.argmax(heatmap)
                y_pred = flat_idx // self.target_size
                x_pred = flat_idx % self.target_size
                
                # Remise à l'échelle pour correspondre à la radiographie native
                final_x = int(x_pred * scale_x)
                final_y = int(y_pred * scale_y)
                
                point_id = CEPH_LANDMARKS_MAPPING.get(idx, f"P_{idx}")
                final_landmarks.append({"id": point_id, "x": final_x, "y": final_y})
                
        # 5. Mode Mock (Fallback de sécurité pour la robustesse de l'API)
        else:
            mode_inference = "MOCK"
            warning_msg = "Modèle IA non disponible - Points placés aléatoirement pour démonstration"
            logger.warning(f"VisionEngine : {warning_msg}")
            
            for idx in range(self.num_landmarks):
                final_x = int(np.random.randint(0, self.target_size) * scale_x)
                final_y = int(np.random.randint(0, self.target_size) * scale_y)
                point_id = CEPH_LANDMARKS_MAPPING.get(idx, f"P_{idx}")
                final_landmarks.append({"id": point_id, "x": final_x, "y": final_y})

        # --- INJECTION DES APEX DENTAIRES (Normes COM par défaut) ---
        # L'apex est placé pour respecter :
        # - IMPA = 90° : axe L1 perpendiculaire au plan mandibulaire (Go→Me)
        # - I/Francfort = 107° : axe U1 à 107° du plan Francfort (Po→Or)
        
        import math
        
        u1_inc = next((p for p in final_landmarks if p['id'] == 'U1_incisal'), None)
        l1_inc = next((p for p in final_landmarks if p['id'] == 'L1_incisal'), None)
        go = next((p for p in final_landmarks if p['id'] == 'Go'), None)
        me = next((p for p in final_landmarks if p['id'] == 'Me'), None)
        po = next((p for p in final_landmarks if p['id'] == 'Po'), None)
        or_ = next((p for p in final_landmarks if p['id'] == 'Or'), None)
        
        # Longueur standard de la dent (distance incisal → apex)
        TOOTH_LENGTH = 85  # pixels
        
        # === PLACEMENT L1_apex : IMPA = 90° (perpendiculaire au plan mandibulaire) ===
        if l1_inc and go and me:
            # Angle du plan mandibulaire Go→Me
            mand_angle = math.atan2(me['y'] - go['y'], me['x'] - go['x'])
            # Pour IMPA = 90°, l'axe de la dent est perpendiculaire au plan mandibulaire
            # L'apex est "derrière" (vers le bas) par rapport à l'incisal
            tooth_angle = mand_angle - math.pi/2  # -90° pour être perpendiculaire
            
            l1_apex_x = l1_inc['x'] + TOOTH_LENGTH * math.cos(tooth_angle)
            l1_apex_y = l1_inc['y'] + TOOTH_LENGTH * math.sin(tooth_angle)
            
            final_landmarks.append({"id": "L1_apex", "x": round(l1_apex_x, 2), "y": round(l1_apex_y, 2)})
            logger.info(f"[APEX] L1_apex placé selon IMPA=90° (perpendiculaire à Go-Me)")
        elif l1_inc:
            # Fallback : placement vertical simple
            final_landmarks.append({"id": "L1_apex", "x": l1_inc['x'], "y": l1_inc['y'] + TOOTH_LENGTH})
        
        # === PLACEMENT U1_apex : I/Francfort = 107° ===
        if u1_inc and po and or_:
            # Angle du plan de Francfort Po→Or
            fh_angle = math.atan2(or_['y'] - po['y'], or_['x'] - po['x'])
            # Pour I/F = 107°, l'axe de la dent fait 107° avec le plan Francfort
            # L'apex est vers le haut et l'arrière par rapport à l'incisal
            # 107° = angle entre axe dent et plan Francfort
            # Donc angle de l'axe = angle_Francfort - 107°
            tooth_angle = fh_angle - math.radians(107)
            
            u1_apex_x = u1_inc['x'] + TOOTH_LENGTH * math.cos(tooth_angle)
            u1_apex_y = u1_inc['y'] + TOOTH_LENGTH * math.sin(tooth_angle)
            
            final_landmarks.append({"id": "U1_apex", "x": round(u1_apex_x, 2), "y": round(u1_apex_y, 2)})
            logger.info(f"[APEX] U1_apex placé selon I/Francfort=107°")
        elif u1_inc:
            # Fallback : placement vertical simple vers le haut
            final_landmarks.append({"id": "U1_apex", "x": u1_inc['x'], "y": max(0, u1_inc['y'] - TOOTH_LENGTH)})

        exec_time = time.time() - start_time
        logger.info(f"Inférence Vision terminée en {exec_time:.3f}s. Mode: {mode_inference}. Matrice native : {orig_w}x{orig_h}")
        
        return {
            "landmarks": final_landmarks,
            "mode_inference": mode_inference,
            "warning": warning_msg,
            "processing_time_ms": round(exec_time * 1000, 2)
        }

# Instanciation du Singleton
vision_engine = VisionEngine()