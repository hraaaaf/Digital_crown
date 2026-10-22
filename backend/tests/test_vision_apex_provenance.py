"""SRPose38-only apex provenance: no inferred or synthetic landmarks on failure."""
import numpy as np

from backend.services.cephalo_engine import CephaloEngine
from backend.services import vision_service


def test_srpose_failure_fabricates_no_incisor_apices(monkeypatch):
    engine = vision_service.VisionEngine()
    monkeypatch.setattr(vision_service.sota_vision_engine, "is_ready", False)
    monkeypatch.setattr(
        vision_service.cv2, "imread",
        lambda *_args, **_kwargs: np.zeros((20, 30), dtype=np.uint8),
    )
    result = engine.predict_landmarks("synthetic.png")

    assert result["mode_inference"] == "FAILED"
    assert result["landmarks"] == []
    assert "manuel" in result["warning"].lower()


def test_onnx_apices_are_preserved_without_replacement(monkeypatch):
    expected_landmarks = [
        {"id": "U1_incisal", "x": 10, "y": 20},
        {"id": "L1_incisal", "x": 12, "y": 30},
        {"id": "U1_apex", "x": 8, "y": 5},
        {"id": "L1_apex", "x": 14, "y": 45},
    ] + [{"id": f"SRPOSE_{i}", "x": 0, "y": 0} for i in range(34)]
    engine = vision_service.VisionEngine()
    monkeypatch.setattr(vision_service.sota_vision_engine, "is_ready", True)
    monkeypatch.setattr(
        vision_service.sota_vision_engine,
        "predict_landmarks",
        lambda _: {"landmarks": expected_landmarks, "mode_inference": "SOTA_ONNX_38"},
    )
    monkeypatch.setattr(
        vision_service.cv2, "imread",
        lambda *_args, **_kwargs: np.zeros((20, 30), dtype=np.uint8),
    )

    result = engine.predict_landmarks("sota.png")

    assert result["mode_inference"] == "SOTA_ONNX_38"
    assert result["landmarks"] == expected_landmarks


def test_missing_apices_leave_dependent_measurements_unavailable():
    points = {
        "Po": (0.0, 0.0), "Or": (10.0, 0.0),
        "Go": (0.0, 10.0), "Me": (10.0, 10.0),
        "U1_incisal": (8.0, 4.0), "L1_incisal": (6.0, 7.0),
    }

    dental = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(points).metrics.analyse_dentaire

    assert dental.IMPA.valeur is None
    assert dental.I_Francfort.valeur is None
    assert dental.Inter_Incisif.valeur is None


def test_explicit_manual_apices_enable_dependent_measurements():
    points = {
        "Po": (0.0, 0.0), "Or": (10.0, 0.0),
        "Go": (0.0, 10.0), "Me": (10.0, 10.0),
        "U1_incisal": (8.0, 4.0), "U1_apex": (7.0, 1.0),
        "L1_incisal": (6.0, 7.0), "L1_apex": (5.0, 9.0),
    }

    dental = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(points).metrics.analyse_dentaire

    assert dental.IMPA.valeur is not None
    assert dental.I_Francfort.valeur is not None
    assert dental.Inter_Incisif.valeur is not None
