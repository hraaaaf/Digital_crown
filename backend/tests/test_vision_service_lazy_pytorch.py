"""Regression: SRPose38 is the only automatic cephalometric model."""
import ast
from pathlib import Path

import numpy as np
from backend.services import vision_service


def test_no_legacy_torch_or_model_import():
    tree = ast.parse(Path(vision_service.__file__).read_text(encoding="utf-8"))
    assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) and "torch" in ast.unparse(n) for n in ast.walk(tree))
    assert not hasattr(vision_service.VisionEngine(), "_initialize_legacy_engine")


def test_srpose_success(monkeypatch):
    class SOTA:
        is_ready = True
        def predict_landmarks(self, _path):
            return {"landmarks": [{"id": str(i), "x": 1, "y": 2} for i in range(38)]}
    monkeypatch.setattr(vision_service, "sota_vision_engine", SOTA())
    monkeypatch.setattr(vision_service.cv2, "imread", lambda *a, **k: np.zeros((32, 32), dtype=np.uint8))
    result = vision_service.VisionEngine().predict_landmarks("ceph.png")
    assert result["mode_inference"] == "SOTA_ONNX_38"
    assert len(result["landmarks"]) == 38


def test_srpose_failure_is_manual_only(monkeypatch):
    class SOTA:
        is_ready = True
        def predict_landmarks(self, _path):
            raise RuntimeError("ONNX failure")
    monkeypatch.setattr(vision_service, "sota_vision_engine", SOTA())
    monkeypatch.setattr(vision_service.cv2, "imread", lambda *a, **k: np.zeros((32, 32), dtype=np.uint8))
    result = vision_service.VisionEngine().predict_landmarks("ceph.png")
    assert result["mode_inference"] == "FAILED"
    assert result["landmarks"] == []
    assert "manuel" in result["warning"]
