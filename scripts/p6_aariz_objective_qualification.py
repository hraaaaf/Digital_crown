#!/usr/bin/env python3
"""Tiny-overfit gate for the Q4 DC-Ceph-UNet29 localization objective.

Research-only. This intentionally uses eight fixed training radiographs without
augmentation. If the Q4 model cannot materially reduce native millimetric error
on that tiny set, it must not receive an expensive full-dataset training run.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import resource
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

try:
    from p6_aariz_training_qualification import find_dataset_root
    from p6_ceph_aariz_data import Aariz29GeometryDataset, LetterboxTransform
    from p6_ceph_train_contract import (
        DCCephUNet29Q4,
        HEATMAP_STRIDE,
        INPUT_SIZE,
        batch_gaussian_heatmaps,
        decode_heatmaps_q4,
        errors_mm_for_sample,
        summarize_errors_mm,
    )
except ModuleNotFoundError:
    from scripts.p6_aariz_training_qualification import find_dataset_root
    from scripts.p6_ceph_aariz_data import Aariz29GeometryDataset, LetterboxTransform
    from scripts.p6_ceph_train_contract import (
        DCCephUNet29Q4,
        HEATMAP_STRIDE,
        INPUT_SIZE,
        batch_gaussian_heatmaps,
        decode_heatmaps_q4,
        errors_mm_for_sample,
        summarize_errors_mm,
    )

SEED = 20260825
COORDINATE_WEIGHT = 20.0
MIN_MRE_REDUCTION_PERCENT = 25.0


def spatial_gaussian_ce(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """Cross-entropy between per-landmark spatial softmax and Gaussian target."""
    if logits.shape != target.shape or logits.ndim != 4:
        raise ValueError(f"expected matching [B,L,H,W], got {logits.shape} and {target.shape}")
    batch, landmarks, _, _ = logits.shape
    flat_logits = logits.reshape(batch, landmarks, -1)
    flat_target = target.reshape(batch, landmarks, -1)
    mass = flat_target.sum(dim=-1, keepdim=True)
    if torch.any(mass <= 0):
        raise ValueError("every landmark target must have positive Gaussian mass")
    target_distribution = flat_target / mass
    return -(target_distribution * F.log_softmax(flat_logits, dim=-1)).sum(dim=-1).mean()


def spatial_soft_argmax_network_xy(logits: torch.Tensor) -> torch.Tensor:
    """Differentiable expected coordinates expressed in the 512-space canvas."""
    if logits.ndim != 4:
        raise ValueError(f"logits must be [B,L,H,W], got {logits.shape}")
    batch, landmarks, height, width = logits.shape
    probability = F.softmax(logits.reshape(batch, landmarks, -1), dim=-1).reshape(
        batch, landmarks, height, width
    )
    xs = torch.arange(width, dtype=logits.dtype, device=logits.device).view(1, 1, 1, width)
    ys = torch.arange(height, dtype=logits.dtype, device=logits.device).view(1, 1, height, 1)
    x_heatmap = (probability * xs).sum(dim=(-2, -1))
    y_heatmap = (probability * ys).sum(dim=(-2, -1))
    return torch.stack((x_heatmap, y_heatmap), dim=-1) * float(HEATMAP_STRIDE)


def localization_objective(
    logits: torch.Tensor,
    target_heatmaps: torch.Tensor,
    target_xy_network: torch.Tensor,
    coordinate_weight: float = COORDINATE_WEIGHT,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Spatial-distribution loss plus normalized coordinate regression."""
    if target_xy_network.ndim != 3 or target_xy_network.shape[-1] != 2:
        raise ValueError("target coordinates must be [B,L,2]")
    ce = spatial_gaussian_ce(logits, target_heatmaps)
    predicted_xy_network = spatial_soft_argmax_network_xy(logits)
    denominator = float(INPUT_SIZE - 1)
    coordinate = F.smooth_l1_loss(
        predicted_xy_network / denominator,
        target_xy_network / denominator,
    )
    total = ce + float(coordinate_weight) * coordinate
    return total, {
        "spatial_ce": float(ce.detach().cpu()),
        "coordinate_smooth_l1": float(coordinate.detach().cpu()),
        "total": float(total.detach().cpu()),
    }


def evaluate(
    model: DCCephUNet29Q4,
    dataset: Aariz29GeometryDataset,
    indices: list[int],
) -> dict[str, Any]:
    model.eval()
    per_image_errors: list[np.ndarray] = []
    with torch.no_grad():
        for index in indices:
            sample = dataset[index]
            logits = model(sample["image"].unsqueeze(0))
            predicted_network = decode_heatmaps_q4(logits)[0].cpu().numpy()
            transform = LetterboxTransform(**sample["transform"])
            errors = errors_mm_for_sample(
                predicted_network,
                sample["coords_original"].cpu().numpy(),
                transform,
                float(sample["pixel_size_mm"]),
            )
            per_image_errors.append(errors)
    return summarize_errors_mm(np.stack(per_image_errors, axis=0))


def _mre_reduction(before: dict[str, Any], after: dict[str, Any], group: str) -> float:
    before_mre = float(before[group]["mre_mm"])
    after_mre = float(after[group]["mre_mm"])
    if before_mre <= 0:
        raise RuntimeError(f"invalid initial {group} MRE: {before_mre}")
    return (before_mre - after_mre) / before_mre * 100.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extracted-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=25)
    args = parser.parse_args()
    if args.samples <= 0 or args.epochs <= 0:
        raise ValueError("samples and epochs must be positive")

    threads = min(4, os.cpu_count() or 1)
    torch.set_num_threads(threads)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.use_deterministic_algorithms(True)

    root = find_dataset_root(args.extracted_dir)
    train = Aariz29GeometryDataset(
        root,
        "train",
        image_size=INPUT_SIZE,
        ground_truth_policy="official_v1_ceil",
    )
    valid = Aariz29GeometryDataset(
        root,
        "valid",
        image_size=INPUT_SIZE,
        ground_truth_policy="official_v1_ceil",
    )
    train_indices = list(range(min(args.samples, len(train))))
    valid_indices = list(range(min(args.samples, len(valid))))

    model = DCCephUNet29Q4(base_channels=16)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)

    train_before = evaluate(model, train, train_indices)
    valid_before = evaluate(model, valid, valid_indices)
    history: list[dict[str, float]] = []
    started = time.perf_counter()

    for epoch in range(args.epochs):
        model.train()
        per_step: list[dict[str, float]] = []
        for index in train_indices:
            sample = train[index]
            image = sample["image"].unsqueeze(0)
            coords = sample["coords"].unsqueeze(0)
            target = batch_gaussian_heatmaps(coords, sigma_heatmap_px=2.0)
            optimizer.zero_grad(set_to_none=True)
            logits = model(image)
            loss, components = localization_objective(logits, target, coords)
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite objective at epoch={epoch}, sample={index}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()
            per_step.append(components)
        history.append(
            {
                key: round(statistics.fmean(step[key] for step in per_step), 7)
                for key in ("spatial_ce", "coordinate_smooth_l1", "total")
            }
        )

    train_after = evaluate(model, train, train_indices)
    valid_after = evaluate(model, valid, valid_indices)
    all29_reduction = _mre_reduction(train_before, train_after, "all29")
    dc20_reduction = _mre_reduction(train_before, train_after, "dc20")

    if not math.isfinite(all29_reduction) or all29_reduction < MIN_MRE_REDUCTION_PERCENT:
        raise RuntimeError(
            f"objective qualification failed: all29 train MRE reduction {all29_reduction:.2f}% "
            f"({train_before['all29']['mre_mm']} -> {train_after['all29']['mre_mm']} mm)"
        )
    if not math.isfinite(dc20_reduction) or dc20_reduction < MIN_MRE_REDUCTION_PERCENT:
        raise RuntimeError(
            f"objective qualification failed: dc20 train MRE reduction {dc20_reduction:.2f}% "
            f"({train_before['dc20']['mre_mm']} -> {train_after['dc20']['mre_mm']} mm)"
        )
    if history[-1]["total"] >= history[0]["total"]:
        raise RuntimeError(f"objective did not decrease: first={history[0]}, last={history[-1]}")

    report = {
        "result": "PASS",
        "status": "Q4_TINY_OVERFIT_OBJECTIVE_QUALIFICATION_NOT_CLINICAL",
        "seed": SEED,
        "config": {
            "model": "DC-Ceph-UNet29Q4",
            "input_size": INPUT_SIZE,
            "heatmap_stride": HEATMAP_STRIDE,
            "samples": len(train_indices),
            "epochs": args.epochs,
            "ground_truth_policy": "official_v1_ceil",
            "geometry": "isotropic letterbox; native-pixel inverse before mm evaluation",
            "optimizer": "AdamW",
            "learning_rate": 1e-3,
            "weight_decay": 1e-5,
            "objective": f"spatial Gaussian CE + {COORDINATE_WEIGHT:g}x normalized-coordinate SmoothL1",
            "augmentation": "none (intentional tiny-overfit gate)",
            "min_train_mre_reduction_percent": MIN_MRE_REDUCTION_PERCENT,
        },
        "objective_history": history,
        "metrics": {
            "train_before": train_before,
            "train_after": train_after,
            "train_mre_reduction_percent": {
                "all29": round(all29_reduction, 2),
                "dc20": round(dc20_reduction, 2),
            },
            "valid_before": valid_before,
            "valid_after": valid_after,
            "note": "validation is observational only; this gate tests eight-image memorization/learnability",
        },
        "runtime": {
            "elapsed_s": round(time.perf_counter() - started, 2),
            "threads": threads,
            "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2),
        },
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
