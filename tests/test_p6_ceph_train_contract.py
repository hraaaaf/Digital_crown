from __future__ import annotations

import numpy as np
import pytest
import torch

from scripts.p6_ceph_aariz_data import LetterboxTransform
from scripts.p6_ceph_train_contract import (
    DC20_INDICES,
    HEATMAP_SIZE,
    LANDMARK_COUNT,
    DCCephUNet29Q4,
    batch_gaussian_heatmaps,
    decode_heatmaps_q4,
    errors_mm_for_sample,
    summarize_errors_mm,
)


def test_q4_model_contract() -> None:
    torch.manual_seed(1)
    model = DCCephUNet29Q4(base_channels=16).eval()
    with torch.no_grad():
        output = model(torch.zeros((1, 1, 512, 512), dtype=torch.float32))
    assert output.shape == (1, LANDMARK_COUNT, HEATMAP_SIZE, HEATMAP_SIZE)
    assert len(DC20_INDICES) == 20


def test_q4_gaussian_decode_round_trip_on_integer_heatmap_center() -> None:
    coords = torch.zeros((1, LANDMARK_COUNT, 2), dtype=torch.float32)
    coords[:, :, 0] = 100.0
    coords[:, :, 1] = 200.0
    heatmaps = batch_gaussian_heatmaps(coords, sigma_heatmap_px=2.0)
    decoded = decode_heatmaps_q4(heatmaps)
    assert torch.allclose(decoded, coords, atol=1e-6)


def test_mm_error_is_computed_after_inverse_letterbox() -> None:
    transform = LetterboxTransform.build(200, 120, 512)
    truth = np.tile(np.asarray([[50.0, 60.0]], dtype=np.float32), (LANDMARK_COUNT, 1))
    network = transform.forward_xy(truth)
    errors = errors_mm_for_sample(network, truth, transform, pixel_size_mm=0.1)
    assert errors.shape == (LANDMARK_COUNT,)
    assert np.allclose(errors, 0.0, atol=1e-6)


def test_metric_summary_reports_all29_and_dc20() -> None:
    errors = np.ones((2, LANDMARK_COUNT), dtype=np.float32)
    summary = summarize_errors_mm(errors)
    assert summary["all29"]["mre_mm"] == pytest.approx(1.0)
    assert summary["dc20"]["mre_mm"] == pytest.approx(1.0)
    assert summary["all29"]["sdr_percent"]["2.0"] == pytest.approx(100.0)
    assert summary["beats_official_reference"] is True


def test_metric_summary_rejects_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="errors must be"):
        summarize_errors_mm(np.zeros((0, LANDMARK_COUNT), dtype=np.float32))
