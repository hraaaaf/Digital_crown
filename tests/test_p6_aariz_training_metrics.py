from __future__ import annotations

import math

import pytest
import torch

from scripts.p6_aariz_training_qualification import (
    decode_argmax_xy,
    radial_errors_mm,
    summarize_errors,
    weighted_heatmap_mse,
)


def test_decode_argmax_xy_uses_x_y_order():
    heatmaps = torch.zeros((2, 8, 10), dtype=torch.float32)
    heatmaps[0, 3, 7] = 9.0
    heatmaps[1, 6, 2] = 4.0
    assert torch.equal(decode_argmax_xy(heatmaps), torch.tensor([[7.0, 3.0], [2.0, 6.0]]))


def test_radial_error_restores_native_non_square_geometry_before_mm():
    # 512 square model tensor came from a 2048x1024 native image.
    # +1 resized px x = +4 native px, +2 resized px y = +4 native px.
    # With 0.1 mm/native-px this is sqrt(0.4^2 + 0.4^2) mm.
    pred = torch.tensor([[101.0, 202.0]])
    target = torch.tensor([[100.0, 200.0]])
    error = radial_errors_mm(pred, target, (2048, 1024), 0.1)
    assert error.item() == pytest.approx(math.sqrt(0.32), rel=1e-6)


def test_sdr_thresholds_and_mre_are_exact():
    result = summarize_errors([1.0, 2.0, 2.6, 4.1])
    assert result["mre_mm"] == pytest.approx(2.425)
    assert result["sdr_percent"] == {
        "2.0": 50.0,
        "2.5": 50.0,
        "3.0": 75.0,
        "4.0": 75.0,
    }


def test_weighted_heatmap_loss_rejects_shape_mismatch_and_is_finite():
    prediction = torch.zeros((1, 29, 16, 16))
    target = torch.zeros_like(prediction)
    target[:, :, 8, 8] = 1.0
    loss = weighted_heatmap_mse(prediction, target)
    assert torch.isfinite(loss)
    assert loss.item() > 0
    with pytest.raises(ValueError, match="shape mismatch"):
        weighted_heatmap_mse(prediction, target[:, :, :-1, :])
