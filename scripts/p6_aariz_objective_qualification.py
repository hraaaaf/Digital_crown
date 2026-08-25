#!/usr/bin/env python3
"""Tiny-overfit qualification for the DC-Ceph-UNet29 localization objective.

Research-only. A landmark model that cannot strongly reduce physical localization
error on eight fixed training radiographs must not receive an expensive full run.
The gate uses the strict Q4 Aariz geometry loader when available.
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
    from p6_ceph_unet29 import DCCephUNet29, gaussian_heatmaps
    from p6_ceph_aariz_data import Aariz29GeometryDataset
    from p6_ceph_train_contract import decode_heatmap_argmax, radial_errors_mm_native, summarize_errors
    from p6_aariz_training_qualification import find_dataset_root
except ModuleNotFoundError:
    from scripts.p6_ceph_unet29 import DCCephUNet29, gaussian_heatmaps
    from scripts.p6_ceph_aariz_data import Aariz29GeometryDataset
    from scripts.p6_ceph_train_contract import decode_heatmap_argmax, radial_errors_mm_native, summarize_errors
    from scripts.p6_aariz_training_qualification import find_dataset_root

SEED = 20260825
IMAGE_SIZE = 256
SIGMA_PX = 2.5


def spatial_gaussian_ce(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """Cross-entropy between spatial softmax and normalized Gaussian heatmaps."""
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


def spatial_soft_argmax_xy(logits: torch.Tensor) -> torch.Tensor:
    """Differentiable expected x/y coordinate from per-landmark spatial logits."""
    if logits.ndim != 4:
        raise ValueError(f"logits must be [B,L,H,W], got {logits.shape}")
    batch, landmarks, height, width = logits.shape
    probability = F.softmax(logits.reshape(batch, landmarks, -1), dim=-1).reshape(
        batch, landmarks, height, width
    )
    xs = torch.linspace(0.0, 1.0, width, dtype=logits.dtype, device=logits.device).view(1, 1, 1, width)
    ys = torch.linspace(0.0, 1.0, height, dtype=logits.dtype, device=logits.device).view(1, 1, height, 1)
    x = (probability * xs).sum(dim=(-2, -1))
    y = (probability * ys).sum(dim=(-2, -1))
    return torch.stack((x, y), dim=-1)


def localization_objective(
    logits: torch.Tensor,
    target_heatmaps: torch.Tensor,
    target_xy_px: torch.Tensor,
    coordinate_weight: float = 10.0,
) -> tuple[torch.Tensor, dict[str, float]]:
    if target_xy_px.ndim != 3 or target_xy_px.shape[-1] != 2:
        raise ValueError("target coordinates must be [B,L,2]")
    ce = spatial_gaussian_ce(logits, target_heatmaps)
    predicted_xy_normalized = spatial_soft_argmax_xy(logits)
    _, _, height, width = logits.shape
    normalizer = target_xy_px.new_tensor([max(width - 1, 1), max(height - 1, 1)])
    target_xy_normalized = target_xy_px / normalizer
    coordinate = F.smooth_l1_loss(predicted_xy_normalized, target_xy_normalized)
    total = ce + coordinate_weight * coordinate
    return total, {
        "spatial_ce": float(ce.detach().cpu()),
        "coordinate_smooth_l1": float(coordinate.detach().cpu()),
        "total": float(total.detach().cpu()),
    }


def evaluate(model: DCCephUNet29, dataset: Aariz29GeometryDataset, indices: list[int]) -> dict[str, Any]:
    model.eval()
    errors: list[float] = []
    with torch.no_grad():
        for index in indices:
            sample = dataset[index]
            logits = model(sample["image"].unsqueeze(0))[0]
            predicted_network = decode_heatmap_argmax(logits)
            radial = radial_errors_mm_native(
                predicted_network,
                sample["coords_original"],
                sample["transform"],
                float(sample["pixel_size_mm"]),
            )
            errors.extend(float(value) for value in radial.tolist())
    return summarize_errors(errors)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extracted-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    if args.samples <= 0 or args.epochs <= 0:
        raise ValueError("samples and epochs must be positive")

    threads = min(4, os.cpu_count() or 1)
    torch.set_num_threads(threads)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.use_deterministic_algorithms(True)

    root = find_dataset_root(args.extracted_dir)
    train = Aariz29GeometryDataset(root, "train", image_size=IMAGE_SIZE, ground_truth_policy="official_v1_ceil")
    valid = Aariz29GeometryDataset(root, "valid", image_size=IMAGE_SIZE, ground_truth_policy="official_v1_ceil")
    train_indices = list(range(min(args.samples, len(train))))
    valid_indices = list(range(min(args.samples, len(valid))))

    model = DCCephUNet29(base_channels=16)
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
            target = gaussian_heatmaps(sample["coords"], IMAGE_SIZE, IMAGE_SIZE, sigma_px=SIGMA_PX).unsqueeze(0)
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
    mre_reduction = (train_before["mre_mm"] - train_after["mre_mm"]) / train_before["mre_mm"] * 100.0

    if not math.isfinite(mre_reduction) or mre_reduction < 35.0:
        raise RuntimeError(
            f"objective qualification failed: train MRE reduction only {mre_reduction:.2f}% "
            f"({train_before['mre_mm']} -> {train_after['mre_mm']} mm)"
        )
    if history[-1]["total"] >= history[0]["total"]:
        raise RuntimeError(f"objective did not decrease: first={history[0]}, last={history[-1]}")

    report = {
        "result": "PASS",
        "status": "TINY_OVERFIT_OBJECTIVE_QUALIFICATION_NOT_CLINICAL",
        "seed": SEED,
        "config": {
            "model": "DC-Ceph-UNet29",
            "image_size": IMAGE_SIZE,
            "samples": len(train_indices),
            "epochs": args.epochs,
            "sigma_px": SIGMA_PX,
            "ground_truth_policy": "official_v1_ceil",
            "geometry": "isotropic letterbox with reversible native-mm evaluation",
            "optimizer": "AdamW",
            "learning_rate": 1e-3,
            "weight_decay": 1e-5,
            "objective": "spatial Gaussian cross-entropy + 10x normalized-coordinate SmoothL1",
            "augmentation": "none (intentional tiny-overfit gate)",
        },
        "objective_history": history,
        "metrics": {
            "train_before": train_before,
            "train_after": train_after,
            "train_mre_reduction_percent": round(mre_reduction, 2),
            "valid_before": valid_before,
            "valid_after": valid_after,
            "note": "validation is observational only; this gate tests memorization/learnability on eight train images",
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
