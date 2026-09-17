import ast
import builtins
from pathlib import Path

import numpy as np

from backend.services import vision_service


def test_vision_service_has_no_top_level_torch_import():
    source_path = Path(vision_service.__file__)
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    top_level_imports = []
    for node in module.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_imports.append(node.module)

    assert "torch" not in top_level_imports


def test_vision_engine_constructor_does_not_initialize_legacy_runtime():
    engine = vision_service.VisionEngine()

    assert engine.legacy_init_attempted is False
    assert engine.torch is None
    assert engine.model is None
    assert engine.is_ready is False


def test_srpose_success_never_initializes_legacy_pytorch(monkeypatch, tmp_path):
    image_path = tmp_path / "ceph.png"
    image_path.write_bytes(b"placeholder")

    class FakeSOTA:
        is_ready = True

        @staticmethod
        def predict_landmarks(_path):
            return {
                "landmarks": [{"id": "S", "x": 10.0, "y": 20.0}],
                "mode_inference": "SOTA_ONNX_38",
            }

    monkeypatch.setattr(vision_service, "sota_vision_engine", FakeSOTA())
    monkeypatch.setattr(
        vision_service.cv2,
        "imread",
        lambda *_args, **_kwargs: np.zeros((32, 32), dtype=np.uint8),
    )

    engine = vision_service.VisionEngine()

    def fail_if_called():
        raise AssertionError("legacy PyTorch fallback must not initialize when SRPose succeeds")

    monkeypatch.setattr(engine, "_initialize_legacy_engine", fail_if_called)

    result = engine.predict_landmarks(str(image_path))

    assert result["mode_inference"] == "SOTA_ONNX_38"
    assert result["landmarks"] == [{"id": "S", "x": 10.0, "y": 20.0}]


def test_windows_torch_commit_limit_failure_is_fail_closed(monkeypatch):
    engine = vision_service.VisionEngine()
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "torch":
            raise OSError(1455, "Le fichier de pagination est insuffisant")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    engine._initialize_legacy_engine()

    assert engine.legacy_init_attempted is True
    assert engine.torch is None
    assert engine.model is None
    assert engine.is_ready is False
