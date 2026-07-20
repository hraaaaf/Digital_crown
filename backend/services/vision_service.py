import sys
import os
import cv2
import numpy as np
import time
import math
import logging


# --- 1. DYNAMIC PATH INJECTION (NAMESPACE HACK) ---
# Resolving absolute import issues from the 'CephLD-CCA' research repository
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.abspath(os.path.join(current_dir, "..", "ai_models", "cephld_cca"))

if repo_path not in sys.path:
    sys.path.insert(0, repo_path)

from .sota_vision_service import sota_vision_engine

# --- 2. SECURE IMPORTS ---
# Graceful PyTorch handling to avoid server crash if environment is not ready
try:
    import torch
except ImportError:
    torch = None

try:
    # Import now relies on injected sys.path and Pillow patch
    from models.unet_w_cartesian_se import U_Net_w_Cartesian_SE
except ImportError as e:
    U_Net_w_Cartesian_SE = None
    logging.getLogger(__name__).warning(f"WARNING: Could not import U_Net_w_Cartesian_SE: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 19 LANDMARKS NOMENCLATURE (Official ISBI 2015 Standard) ---
CEPH_LANDMARKS_MAPPING = {
    0: "S", 1: "N", 2: "Or", 3: "Po", 4: "A", 5: "B", 6: "Pog", 7: "Me",
    8: "Gn", 9: "Go", 10: "L1_incisal", 11: "U1_incisal", 12: "UL",
    13: "LL", 14: "Sn", 15: "Pog_soft", 16: "PNS", 17: "ANS", 18: "Ar"
}

class VisionEngine:
    """
    PyTorch Deep Learning Inference Engine for cephalometric landmark detection.
    Singleton implementation for CephLD-CCA architecture (U-Net + Cartesian SE).
    """

    def __init__(self):
        self.target_size = 512
        self.num_landmarks = 19
        self.model = None
        self.is_ready = False
        
        # Agnostic device configuration (GPU if available, else CPU)
        if torch is not None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = "cpu"
            
        # Path to PyTorch model weights
        self.weights_path = os.path.join(repo_path, "ceph_weights.pth")
        
        self._initialize_engine()

    def _initialize_engine(self):
        """Loads the PyTorch model into memory at Uvicorn server startup."""
        if torch is None:
            logger.error("CRITICAL: PyTorch is not installed. Vision inference will fallback to MOCK mode.")
            return

        if U_Net_w_Cartesian_SE is None:
            logger.error("CRITICAL: Model class not found. Check internal repo dependencies. MOCK mode enabled.")
            return

        if not os.path.exists(self.weights_path):
            logger.error(f"CRITICAL: Model weights not found at {self.weights_path}. MOCK mode enabled.")
            return

        try:
            logger.info(f"VisionEngine: Loading PyTorch model on [{self.device.type.upper()}]...")
            start_time = time.time()
            
            # Model instantiation: 1 input channel (grayscale), 19 output channels (heatmaps)
            self.model = U_Net_w_Cartesian_SE(img_ch=1, output_ch=self.num_landmarks)
            
            # Strict weight loading with map_location to avoid CUDA -> CPU crashes
            state_dict = torch.load(self.weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval() # Locked in inference mode (disables dropout/batchnorm training)
            
            self.is_ready = True
            logger.info(f"VisionEngine: PyTorch model loaded successfully in {time.time() - start_time:.2f}s.")
            
        except Exception as e:
            logger.error(f"Critical failure loading PyTorch Vision model: {e}")

    def predict_landmarks(self, file_location: str) -> dict:
        """
        Executes full pipeline: Read -> Tensor -> U-Net -> Heatmaps -> Absolute Coordinates.
        
        Returns a dictionary containing:
        - landmarks: List of detected points
        - mode_inference: "PRODUCTION" or "MOCK" 
        - warning: Warning message if MOCK mode
        - processing_time_ms: Processing time
        """
        start_time = time.time()
        
        # 1. Pre-processing: Strict OpenCV grayscale reading
        img = cv2.imread(file_location, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not read image at: {file_location}")
            
        orig_h, orig_w = img.shape
        
        # 2. Scale factors for Post-processing
        scale_x = orig_w / float(self.target_size)
        scale_y = orig_h / float(self.target_size)

        final_landmarks = []
        mode_inference = "PRODUCTION"
        warning_msg = None

        # 3. SOTA Inference Mode (ONNX) - Priority as it is ultra-fast on CPU
        if sota_vision_engine.is_ready:
            try:
                res = sota_vision_engine.predict_landmarks(file_location)
                if res and res.get("landmarks"):
                    # Retrieve SOTA points (which already include apex if available)
                    final_landmarks = res["landmarks"]
                    mode_inference = res["mode_inference"]
                else:
                    logger.warning("SOTA returned an empty list, falling back to PyTorch")
            except Exception as e:
                logger.error(f"SOTA engine failure, falling back to PyTorch: {e}")

        # 4. Real PyTorch Inference Mode (Legacy)
        if not final_landmarks and self.is_ready and self.model is not None and torch is not None:
            
            # Resizing and normalization
            img_resized = cv2.resize(img, (self.target_size, self.target_size))
            img_normalized = img_resized.astype(np.float32) / 255.0
            
            # Tensor conversion (Batch=1, Channels=1, Height=512, Width=512)
            input_tensor = torch.tensor(img_normalized).unsqueeze(0).unsqueeze(0).to(self.device)
            
            # Inference without gradients for performance
            with torch.no_grad():
                output_tensor = self.model(input_tensor) # Expected output: (1, 19, 512, 512)
                
            # Bring back to CPU and Numpy conversion for post-processing
            heatmaps = output_tensor.squeeze(0).cpu().numpy() # Shape: (19, 512, 512)
            
            # 4. Post-processing: Activation peaks extraction
            for idx in range(self.num_landmarks):
                heatmap = heatmaps[idx]
                
                # argmax returns the 1D index of the hottest pixel in the 512x512 matrix
                flat_idx = np.argmax(heatmap)
                y_pred = flat_idx // self.target_size
                x_pred = flat_idx % self.target_size
                
                # Rescaling to match native radiograph size
                final_x = int(x_pred * scale_x)
                final_y = int(y_pred * scale_y)
                
                point_id = CEPH_LANDMARKS_MAPPING.get(idx, f"P_{idx}")
                final_landmarks.append({"id": point_id, "x": final_x, "y": final_y})
                
        # 5. Mode Fallback Sécurisé
        elif not final_landmarks:
            mode_inference = "FAILED"
            warning_msg = "Moteurs d'IA (SOTA et PyTorch) indisponibles. Placement manuel requis."
            logger.error(f"VisionEngine: {warning_msg}")
            # Renvoyer une liste vide pour forcer le tracé manuel au lieu de points aléatoires
            final_landmarks = []

        exec_time = time.time() - start_time
        logger.info(f"Vision Inference finished in {exec_time:.3f}s. Mode: {mode_inference}. Native matrix: {orig_w}x{orig_h}")
        
        return {
            "landmarks": final_landmarks,
            "mode_inference": mode_inference,
            "warning": warning_msg,
            "processing_time_ms": round(exec_time * 1000, 2)
        }

# Singleton Instantiation
vision_engine = VisionEngine()
