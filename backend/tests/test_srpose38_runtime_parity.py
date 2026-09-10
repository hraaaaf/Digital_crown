import json
from pathlib import Path

import numpy as np

from backend.services import sota_vision_service
from backend.services.srpose38_pipeline import (
    _refine_keypoints_dark,
    full_image_center_scale,
    get_warp_matrix,
)


def test_full_image_geometry_matches_certified_stack1_shape():
    center, scale = full_image_center_scale((2400, 1935, 3))
    np.testing.assert_allclose(center, [967.5, 1200.0], atol=1e-6)
    np.testing.assert_allclose(scale, [3000.0, 3000.0], atol=1e-6)

    warp = get_warp_matrix(center, scale)
    mapped_center = warp @ np.array([center[0], center[1], 1.0])
    np.testing.assert_allclose(mapped_center, [512.0, 512.0], atol=1e-4)


def test_darkpose_recovers_subpixel_gaussian_center():
    height = width = 64
    center_x, center_y = 22.35, 35.70
    yy, xx = np.mgrid[:height, :width]
    heatmap = np.exp(
        -((xx - center_x) ** 2 + (yy - center_y) ** 2) / (2 * 2.0**2)
    ).astype(np.float32)
    y_peak, x_peak = np.unravel_index(int(np.argmax(heatmap)), heatmap.shape)
    points = np.array([[[x_peak, y_peak]]], dtype=np.float32)

    refined = _refine_keypoints_dark(points, heatmap[None, ...].copy(), 11)[0, 0]
    np.testing.assert_allclose(refined, [center_x, center_y], atol=0.02)


def test_missing_asset_fails_closed(tmp_path):
    missing = tmp_path / "srpose38-tta-1024.onnx"
    engine = sota_vision_service.SOTAVisionEngine(model_path=str(missing))
    assert engine.is_ready is False
    assert engine.session is None
    assert engine.predict_landmarks("unused.png") is None


def test_invalid_asset_hash_fails_closed(tmp_path, monkeypatch):
    invalid = tmp_path / "srpose38-tta-1024.onnx"
    invalid.write_bytes(b"invalid")
    monkeypatch.setattr(sota_vision_service, "SRPOSE38_MODEL_SIZE_BYTES", len(b"invalid"))
    engine = sota_vision_service.SOTAVisionEngine(model_path=str(invalid))
    assert engine.is_ready is False
    assert engine.session is None


def test_reference_fixture_pins_certified_external_asset():
    fixture_path = (
        Path(__file__).parent / "fixtures" / "cephalo" / "srpose38_stack1_reference.json"
    )
    reference = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert reference["onnx_sha256"] == sota_vision_service.SRPOSE38_MODEL_SHA256
    assert reference["onnx_size_bytes"] == sota_vision_service.SRPOSE38_MODEL_SIZE_BYTES
    assert len(reference["onnx_points"]) == 38
    assert np.isfinite(np.asarray(reference["onnx_points"], dtype=float)).all()
