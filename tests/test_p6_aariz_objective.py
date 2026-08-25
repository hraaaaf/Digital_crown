from __future__ import annotations

import torch

from scripts.p6_aariz_objective_qualification import (
    localization_objective,
    spatial_gaussian_ce,
    spatial_soft_argmax_network_xy,
)
from scripts.p6_ceph_train_contract import HEATMAP_STRIDE


def test_spatial_soft_argmax_network_xy_moves_to_dominant_peak():
    logits = torch.full((1, 1, 8, 8), -20.0)
    logits[0, 0, 6, 2] = 20.0
    xy = spatial_soft_argmax_network_xy(logits)
    expected = torch.tensor([[[2.0 * HEATMAP_STRIDE, 6.0 * HEATMAP_STRIDE]]])
    assert torch.allclose(xy, expected, atol=1e-5)


def test_spatial_gaussian_ce_prefers_aligned_peak():
    target = torch.zeros((1, 1, 8, 8))
    target[0, 0, 5, 3] = 1.0
    good = torch.zeros_like(target)
    bad = torch.zeros_like(target)
    good[0, 0, 5, 3] = 8.0
    bad[0, 0, 1, 1] = 8.0
    assert spatial_gaussian_ce(good, target) < spatial_gaussian_ce(bad, target)


def test_localization_objective_has_finite_gradient():
    logits = torch.zeros((1, 2, 16, 16), requires_grad=True)
    target = torch.zeros_like(logits)
    target[0, 0, 4, 7] = 1.0
    target[0, 1, 12, 3] = 1.0
    coords_network = torch.tensor(
        [[[7.0 * HEATMAP_STRIDE, 4.0 * HEATMAP_STRIDE], [3.0 * HEATMAP_STRIDE, 12.0 * HEATMAP_STRIDE]]]
    )
    loss, parts = localization_objective(logits, target, coords_network)
    loss.backward()
    assert torch.isfinite(loss)
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()
    assert parts["total"] > 0
