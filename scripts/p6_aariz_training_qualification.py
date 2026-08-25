#!/usr/bin/env python3
"""Research-only training qualification for DC-Ceph-UNet29 on real Aariz v1.

This is not a clinical training run. It verifies the optimization loop, metric
math in physical millimetres after 512x512 resize, checkpoint reproducibility
metadata, and fail-closed dataset assumptions before any expensive full run.
"""
from __future__ import annotations

import argparse
import hashlib
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

try:
    from p6_ceph_unet29 import Aariz29Dataset, DCCephUNet29, gaussian_heatmaps
except ModuleNotFoundError:
    from scripts.p6_ceph_unet29 import Aariz29Dataset, DCCephUNet29, gaussian_heatmaps

MODEL_SIZE = 512
SEED = 20260825
SDR_THRESHOLDS_MM = (2.0, 2.5, 3.0, 4.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_dataset_root(extracted_dir: Path) -> Path:
    matches = list(extracted_dir.rglob("cephalogram_machine_mappings.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one Aariz calibration CSV, found {len(matches)}")
    root = matches[0].parent
    for split in ("train", "valid", "test"):
        if not (root / split / "Cephalograms").is_dir():
            raise RuntimeError(f"invalid Aariz root {root}: missing {split}/Cephalograms")
    return root


def decode_argmax_xy(heatmaps: torch.Tensor) -> torch.Tensor:
    """Decode [L,H,W] heatmaps to [L,2] x/y coordinates."""
    if heatmaps.ndim != 3:
        raise ValueError(f"heatmaps must be [L,H,W], got {tuple(heatmaps.shape)}")
    landmarks, height, width = heatmaps.shape
    flat = heatmaps.reshape(landmarks, -1)
    indices = torch.argmax(flat, dim=1)
    y = torch.div(indices, width, rounding_mode="floor").to(torch.float32)
    x = (indices % width).to(torch.float32)
    return torch.stack((x, y), dim=1)


def radial_errors_mm(
    pred_xy_resized: torch.Tensor,
    target_xy_resized: torch.Tensor,
    original_size: tuple[int, int],
    pixel_size_mm: float,
    resized_size: int = MODEL_SIZE,
) -> torch.Tensor:
    """Convert resized-space errors back to native pixel geometry, then mm.

    Aariz supplies one physical pixel-size value per original cephalogram. Since
    the loader independently rescales x and y to a square tensor, each axis must
    be returned to native pixels before applying mm/pixel. Treating resized
    pixels directly as physical pixels would bias MRE on non-square images.
    """
    if pred_xy_resized.shape != target_xy_resized.shape or pred_xy_resized.ndim != 2:
        raise ValueError("predicted and target coordinates must share [L,2] shape")
    if pred_xy_resized.shape[1] != 2:
        raise ValueError("coordinate tensors must contain x,y")
    width, height = original_size
    if width <= 0 or height <= 0 or resized_size <= 0 or pixel_size_mm <= 0:
        raise ValueError("image geometry and pixel size must be positive")

    delta = pred_xy_resized.to(torch.float64) - target_xy_resized.to(torch.float64)
    dx_mm = delta[:, 0] * (float(width) / resized_size) * pixel_size_mm
    dy_mm = delta[:, 1] * (float(height) / resized_size) * pixel_size_mm
    return torch.sqrt(dx_mm.square() + dy_mm.square())


def summarize_errors(errors_mm: list[float]) -> dict[str, Any]:
    if not errors_mm or not all(math.isfinite(value) and value >= 0 for value in errors_mm):
        raise ValueError("errors must be a non-empty finite non-negative sequence")
    array = np.asarray(errors_mm, dtype=np.float64)
    return {
        "count": int(array.size),
        "mre_mm": round(float(array.mean()), 4),
        "median_mm": round(float(np.median(array)), 4),
        "p95_mm": round(float(np.percentile(array, 95)), 4),
        "sdr_percent": {
            f"{threshold:.1f}": round(float((array <= threshold).mean() * 100.0), 2)
            for threshold in SDR_THRESHOLDS_MM
        },
    }


def weighted_heatmap_mse(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """Background-aware heatmap loss for the qualification path.

    A plain per-pixel MSE on 29 sparse Gaussian heatmaps can reward the trivial
    all-background solution. This weighted formulation keeps background signal
    while emphasizing annotated Gaussian support. It is a research baseline,
    not yet the final clinically validated loss.
    """
    if prediction.shape != target.shape:
        raise ValueError(f"prediction/target shape mismatch: {prediction.shape} vs {target.shape}")
    probability = torch.sigmoid(prediction)
    weight = 1.0 + 24.0 * target
    return ((probability - target).square() * weight).mean()


def evaluate(model: DCCephUNet29, dataset: Aariz29Dataset, count: int) -> dict[str, Any]:
    model.eval()
    errors: list[float] = []
    with torch.no_grad():
        for index in range(min(count, len(dataset))):
            sample = dataset[index]
            output = model(sample["image"].unsqueeze(0))[0]
            pred_xy = decode_argmax_xy(output)
            radial = radial_errors_mm(
                pred_xy,
                sample["coords"],
                sample["original_size"],
                float(sample["pixel_size_mm"]),
            )
            errors.extend(float(value) for value in radial.cpu().tolist())
    return summarize_errors(errors)


def train_epoch(
    model: DCCephUNet29,
    dataset: Aariz29Dataset,
    optimizer: torch.optim.Optimizer,
    count: int,
    epoch: int,
) -> float:
    dataset.set_epoch(epoch)
    model.train()
    losses: list[float] = []
    for index in range(min(count, len(dataset))):
        sample = dataset[index]
        image = sample["image"].unsqueeze(0)
        target = gaussian_heatmaps(sample["coords"], MODEL_SIZE, MODEL_SIZE, sigma_px=5.0).unsqueeze(0)
        optimizer.zero_grad(set_to_none=True)
        prediction = model(image)
        loss = weighted_heatmap_mse(prediction, target)
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite training loss at epoch={epoch}, index={index}")
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return statistics.fmean(losses)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extracted-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-samples", type=int, default=32)
    parser.add_argument("--valid-samples", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    if args.train_samples <= 0 or args.valid_samples <= 0 or args.epochs <= 0:
        raise ValueError("sample counts and epochs must be positive")

    threads = min(4, os.cpu_count() or 1)
    torch.set_num_threads(threads)
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    dataset_root = find_dataset_root(args.extracted_dir)
    train_aug = Aariz29Dataset(dataset_root, "train", image_size=MODEL_SIZE, augment=True, seed=SEED)
    train_eval = Aariz29Dataset(dataset_root, "train", image_size=MODEL_SIZE, augment=False, seed=SEED)
    valid_eval = Aariz29Dataset(dataset_root, "valid", image_size=MODEL_SIZE, augment=False, seed=SEED)

    model = DCCephUNet29(base_channels=16)
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)

    started = time.perf_counter()
    before_train = evaluate(model, train_eval, args.train_samples)
    before_valid = evaluate(model, valid_eval, args.valid_samples)

    epoch_losses: list[float] = []
    for epoch in range(args.epochs):
        epoch_losses.append(train_epoch(model, train_aug, optimizer, args.train_samples, epoch))

    after_train = evaluate(model, train_eval, args.train_samples)
    after_valid = evaluate(model, valid_eval, args.valid_samples)

    if not all(math.isfinite(value) for value in epoch_losses):
        raise RuntimeError("training produced non-finite epoch loss")
    loss_improvement_pct = (epoch_losses[0] - epoch_losses[-1]) / epoch_losses[0] * 100.0
    if epoch_losses[-1] >= epoch_losses[0] or loss_improvement_pct < 1.0:
        raise RuntimeError(
            f"qualification failed: loss did not improve enough: {epoch_losses}, "
            f"improvement={loss_improvement_pct:.2f}%"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.output.parent / "qualification_state.pt"
    torch.save(model.state_dict(), checkpoint_path)
    checkpoint_hash = sha256(checkpoint_path)

    # Prove the serialized state is loadable into the exact architecture.
    reloaded = DCCephUNet29(base_channels=16)
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    reloaded.load_state_dict(state, strict=True)
    reloaded.eval()
    with torch.no_grad():
        shape = list(reloaded(torch.zeros((1, 1, MODEL_SIZE, MODEL_SIZE))).shape)
    if shape != [1, 29, MODEL_SIZE, MODEL_SIZE]:
        raise RuntimeError(f"reloaded checkpoint contract mismatch: {shape}")

    report = {
        "result": "PASS",
        "status": "TRAINING_QUALIFICATION_ONLY_NOT_CLINICAL",
        "dataset_root_name": dataset_root.name,
        "seed": SEED,
        "threads": threads,
        "config": {
            "model": "DC-Ceph-UNet29",
            "base_channels": 16,
            "image_size": MODEL_SIZE,
            "train_samples": min(args.train_samples, len(train_aug)),
            "valid_samples": min(args.valid_samples, len(valid_eval)),
            "epochs": args.epochs,
            "optimizer": "Adam",
            "learning_rate": 3e-4,
            "loss": "sigmoid weighted heatmap MSE, weight=1+24*target",
            "sigma_px": 5.0,
        },
        "training": {
            "epoch_losses": [round(value, 8) for value in epoch_losses],
            "loss_improvement_percent": round(loss_improvement_pct, 2),
            "elapsed_s": round(time.perf_counter() - started, 2),
        },
        "metrics": {
            "train_before": before_train,
            "train_after": after_train,
            "valid_before": before_valid,
            "valid_after": after_valid,
            "note": "MRE/SDR here qualify metric plumbing only; this short run is not a performance claim.",
        },
        "checkpoint": {
            "sha256": checkpoint_hash,
            "size_bytes": checkpoint_path.stat().st_size,
            "reloaded_output_shape": shape,
        },
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "logical_cpu_count": os.cpu_count(),
            "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2),
        },
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checkpoint_path.unlink()
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
