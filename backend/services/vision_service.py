import sys
import os
import cv2
import numpy as np
import time
import logging


# --- 1. DYNAMIC PATH INJECTION (NAMESPACE HACK) ---
# Resolving absolute import issues from the 'CephLD-CCA' research repository.
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_path = os.path.abspath(os.path.join(current_dir, "..", "ai_models", "cephld_cca"))

if repo_path not in sys.path:
    sys.path.insert(0, repo_path)

from .sota_vision_service import sota_vision_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 19 LANDMARKS NOMENCLATURE (Official ISBI 2015 Standard) ---
CEPH_LANDMARKS_MAPPING = {
    0: "S", 1: "N", 2: "Or", 3: "Po", 4: "A", 5: "B", 6: "Pog", 7: "Me",
    8: "Gn", 9: "Go", 10: "L1_incisal", 11: "U1_incisal", 12: "UL",
    13: "LL", 14: "Sn", 15: "Pog_soft", 16: "PNS", 17: "ANS", 18: "Ar"
}


class VisionEngine:
    """Cephalometric landmark detection orchestrator.

    SRPose38/ONNX is the certified primary runtime. The legacy PyTorch
    CephLD-CCA engine is intentionally loaded lazily only when a fallback is
    actually required. This keeps backend boot independent from PyTorch DLL
    loading and Windows commit-limit/pagefile failures.
    """

    def __init__(self):
        self.target_size = 512
        self.num_landmarks = 19
        self.model = None
        self.is_ready = False
        self.device = "cpu"
        self.torch = None
        self.model_class = None
        self.legacy_init_attempted = False
        self.weights_path = os.path.join(repo_path, "ceph_weights.pth")

    def _initialize_legacy_engine(self):
        """Load the optional PyTorch fallback on first demand, never at boot."""
        if self.legacy_init_attempted:
            return
        self.legacy_init_attempted = True

        try:
            import torch
        except Exception as exc:
            # Importing torch on Windows can fail with OSError/WinError 1455,
            # not only ImportError. Fail closed without taking down the backend.
            logger.error("Legacy PyTorch runtime unavailable: %s", exc)
            return

        # Tests and controlled callers may inject an already-prepared legacy model.
        # In that case only bind the lazy torch runtime; do not re-import the legacy
        # model class or touch weights. This preserves the no-PyTorch-at-boot contract
        # while honoring an explicitly ready runtime.
        if self.is_ready and self.model is not None:
            self.torch = torch
            if self.device == "cpu":
                self.device = torch.device("cpu")
            return

        try:
            from models.unet_w_cartesian_se import U_Net_w_Cartesian_SE
        except Exception as exc:
            logger.error("Legacy CephLD-CCA model class unavailable: %s", exc)
            return

        if not os.path.exists(self.weights_path):
            logger.error("Legacy CephLD-CCA weights absent: %s", self.weights_path)
            return

        try:
            self.torch = torch
            self.model_class = U_Net_w_Cartesian_SE
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info("VisionEngine: loading legacy PyTorch model on [%s]...", self.device.type.upper())
            start_time = time.time()
            self.model = self.model_class(img_ch=1, output_ch=self.num_landmarks)
            state_dict = torch.load(self.weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self.is_ready = True
            logger.info(
                "VisionEngine: legacy PyTorch model loaded successfully in %.2fs.",
                time.time() - start_time,
            )
        except Exception as exc:
            self.model = None
            self.is_ready = False
            logger.error("Legacy PyTorch model initialization failed: %s", exc)

    def predict_landmarks(self, file_location: str) -> dict:
        """Run SRPose38 first, then optional legacy PyTorch, else fail closed."""
        start_time = time.time()

        img = cv2.imread(file_location, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not read image at: {file_location}")

        orig_h, orig_w = img.shape
        scale_x = orig_w / float(self.target_size)
        scale_y = orig_h / float(self.target_size)

        final_landmarks = []
        mode_inference = "PRODUCTION"
        warning_msg = None

        # Certified primary path: SRPose38 ONNX.
        if sota_vision_engine.is_ready:
            try:
                res = sota_vision_engine.predict_landmarks(file_location)
                if res and res.get("landmarks"):
                    final_landmarks = res["landmarks"]
                    mode_inference = res["mode_inference"]
                else:
                    logger.warning("SOTA returned an empty list, trying legacy PyTorch fallback")
            except Exception as exc:
                logger.error("SOTA engine failure, trying legacy PyTorch fallback: %s", exc)

        # Optional legacy path is initialized only when actually needed.
        if not final_landmarks:
            self._initialize_legacy_engine()

        torch = self.torch
        if not final_landmarks and self.is_ready and self.model is not None and torch is not None:
            img_resized = cv2.resize(img, (self.target_size, self.target_size))
            img_normalized = img_resized.astype(np.float32) / 255.0
            input_tensor = torch.tensor(img_normalized).unsqueeze(0).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output_tensor = self.model(input_tensor)

            heatmaps = output_tensor.squeeze(0).cpu().numpy()
            for idx in range(self.num_landmarks):
                heatmap = heatmaps[idx]
                flat_idx = np.argmax(heatmap)
                y_pred = flat_idx // self.target_size
                x_pred = flat_idx % self.target_size
                final_x = int(x_pred * scale_x)
                final_y = int(y_pred * scale_y)
                point_id = CEPH_LANDMARKS_MAPPING.get(idx, f"P_{idx}")
                final_landmarks.append({"id": point_id, "x": final_x, "y": final_y})

            mode_inference = "PRODUCTION_LEGACY_PYTORCH"

        if not final_landmarks:
            mode_inference = "FAILED"
            warning_msg = "Moteurs d'IA (SOTA et PyTorch) indisponibles. Placement manuel requis."
            logger.error("VisionEngine: %s", warning_msg)

        exec_time = time.time() - start_time
        logger.info(
            "Vision Inference finished in %.3fs. Mode: %s. Native matrix: %sx%s",
            exec_time,
            mode_inference,
            orig_w,
            orig_h,
        )

        return {
            "landmarks": final_landmarks,
            "mode_inference": mode_inference,
            "warning": warning_msg,
            "processing_time_ms": round(exec_time * 1000, 2),
        }


# Singleton instantiation is now lightweight: no PyTorch import/model load here.
vision_engine = VisionEngine()
