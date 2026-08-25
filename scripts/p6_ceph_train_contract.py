#!/usr/bin/env python3
"""Research-only efficient training/evaluation contract for DC-Ceph-UNet29.

The full-resolution smoke architecture is intentionally not the training default:
its measured GitHub CPU cost is too high for responsible iteration. This module
keeps the 512x512 input but predicts 1/4-resolution heatmaps (128x128), then
maps decoded coordinates through the reversible Aariz letterbox back to native
pixels before computing millimetric errors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

try:
    from scripts.p6_ceph_aariz_data import LetterboxTransform
    from scripts.p6_ceph_aariz_mapping import AARIZ_OFFICIAL_TITLES, AARIZ_TITLE_TO_DC
    from scripts.p6_ceph_unet29 import DoubleConv, UpBlock
except ImportError:
    from p6_ceph_aariz_data import LetterboxTransform
    from p6_ceph_aariz_mapping import AARIZ_OFFICIAL_TITLES, AARIZ_TITLE_TO_DC
    from p6_ceph_unet29 import DoubleConv, UpBlock

INPUT_SIZE = 512
HEATMAP_STRIDE = 4
HEATMAP_SIZE = INPUT_SIZE // HEATMAP_STRIDE
LANDMARK_COUNT = 29
SDR_THRESHOLDS_MM = (2.0, 2.5, 3.0, 4.0)
OFFICIAL_AARIZ_BASELINE_MRE_MM = 1.789
OFFICIAL_AARIZ_BASELINE_SDR2_PERCENT = 78.44
DC20_INDICES = tuple(
    index for index, title in enumerate(AARIZ_OFFICIAL_TITLES) if title in AARIZ_TITLE_TO_DC
)


class DCCephUNet29Q4(nn.Module):
    """U-Net-style 29-landmark model with 1/4-resolution heatmap head."""

    def __init__(self, base_channels: int = 16) -> None:
        super().__init__()
        if base_channels <= 0 or base_channels % 8 != 0:
            raise ValueError("base_channels must be a positive multiple of 8")
        c1, c2, c3, c4, c5 = [base_channels * factor for factor in (1, 2, 4, 8, 16)]
        self.enc1 = DoubleConv(1, c1)
        self.enc2 = DoubleConv(c1, c2)
        self.enc3 = DoubleConv(c2, c3)
        self.enc4 = DoubleConv(c3, c4)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = DoubleConv(c4, c5)
        self.up4 = UpBlock(c5, c4, c4)
        self.up3 = UpBlock(c4, c3, c3)
        self.head = nn.Conv2d(c3, LANDMARK_COUNT, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 4 or x.shape[1] != 1:
            raise ValueError(f"expected BCHW grayscale tensor, got {tuple(x.shape)}")
        if x.shape[-1] % 16 or x.shape[-2] % 16:
            raise ValueError("height and width must be divisible by 16")
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))
        bottleneck = self.bottleneck(self.pool(e4))
        d4 = self.up4(bottleneck, e4)
        d3 = self.up3(d4, e3)
        return self.head(d3)


def batch_gaussian_heatmaps(
    coords_network: torch.Tensor,
    sigma_heatmap_px: float = 2.0,
) -> torch.Tensor:
    """Build [B,29,128,128] Gaussian targets from 512-space coordinates."""
    if coords_network.ndim != 3 or coords_network.shape[1:] != (LANDMARK_COUNT, 2):
        raise ValueError(f"coords must be [B,{LANDMARK_COUNT},2], got {tuple(coords_network.shape)}")
    if sigma_heatmap_px <= 0:
        raise ValueError("sigma_heatmap_px must be positive")
    coords = coords_network / float(HEATMAP_STRIDE)
    ys = torch.arange(HEATMAP_SIZE, dtype=torch.float32, device=coords.device).view(1, 1, -1, 1)
    xs = torch.arange(HEATMAP_SIZE, dtype=torch.float32, device=coords.device).view(1, 1, 1, -1)
    cx = coords[:, :, 0].unsqueeze(-1).unsqueeze(-1)
    cy = coords[:, :, 1].unsqueeze(-1).unsqueeze(-1)
    return torch.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (2.0 * sigma_heatmap_px**2))


def decode_heatmaps_q4(heatmaps: torch.Tensor) -> torch.Tensor:
    """Argmax + quarter-pixel local gradient refinement, returned in 512-space."""
    if heatmaps.ndim != 4 or heatmaps.shape[1] != LANDMARK_COUNT:
        raise ValueError(f"heatmaps must be [B,{LANDMARK_COUNT},H,W], got {tuple(heatmaps.shape)}")
    batch, landmarks, height, width = heatmaps.shape
    flat_index = torch.argmax(heatmaps.reshape(batch, landmarks, -1), dim=-1)
    y = torch.div(flat_index, width, rounding_mode="floor").to(torch.float32)
    x = (flat_index % width).to(torch.float32)

    refined_x = x.clone()
    refined_y = y.clone()
    for batch_index in range(batch):
        for landmark_index in range(landmarks):
            xi = int(x[batch_index, landmark_index].item())
            yi = int(y[batch_index, landmark_index].item())
            if 1 <= xi < width - 1:
                dx = heatmaps[batch_index, landmark_index, yi, xi + 1] - heatmaps[
                    batch_index, landmark_index, yi, xi - 1
                ]
                refined_x[batch_index, landmark_index] += 0.25 * torch.sign(dx)
            if 1 <= yi < height - 1:
                dy = heatmaps[batch_index, landmark_index, yi + 1, xi] - heatmaps[
                    batch_index, landmark_index, yi - 1, xi
                ]
                refined_y[batch_index, landmark_index] += 0.25 * torch.sign(dy)

    return torch.stack((refined_x, refined_y), dim=-1) * float(HEATMAP_STRIDE)


def errors_mm_for_sample(
    prediction_network: np.ndarray,
    truth_original: np.ndarray,
    transform: LetterboxTransform,
    pixel_size_mm: float,
) -> np.ndarray:
    prediction_network = np.asarray(prediction_network, dtype=np.float32)
    truth_original = np.asarray(truth_original, dtype=np.float32)
    if prediction_network.shape != (LANDMARK_COUNT, 2) or truth_original.shape != (LANDMARK_COUNT, 2):
        raise ValueError("prediction and truth must both be [29,2]")
    if not np.isfinite(pixel_size_mm) or pixel_size_mm <= 0:
        raise ValueError("pixel_size_mm must be finite and positive")
    prediction_original = transform.inverse_xy(prediction_network)
    return np.linalg.norm(prediction_original - truth_original, axis=1) * float(pixel_size_mm)


def summarize_errors_mm(errors_mm: np.ndarray) -> dict[str, Any]:
    errors = np.asarray(errors_mm, dtype=np.float64)
    if errors.ndim != 2 or errors.shape[1] != LANDMARK_COUNT or errors.shape[0] == 0:
        raise ValueError(f"errors must be [N,{LANDMARK_COUNT}] with N>0, got {errors.shape}")
    if not np.all(np.isfinite(errors)) or np.any(errors < 0):
        raise ValueError("errors must be finite and non-negative")

    all_values = errors.reshape(-1)
    dc20_values = errors[:, DC20_INDICES].reshape(-1)

    def group(values: np.ndarray) -> dict[str, Any]:
        return {
            "mre_mm": round(float(np.mean(values)), 6),
            "std_mm": round(float(np.std(values)), 6),
            "sdr_percent": {
                str(threshold): round(float(np.mean(values <= threshold) * 100.0), 4)
                for threshold in SDR_THRESHOLDS_MM
            },
        }

    per_landmark = {
        title: round(float(np.mean(errors[:, index])), 6)
        for index, title in enumerate(AARIZ_OFFICIAL_TITLES)
    }
    all29 = group(all_values)
    return {
        "all29": all29,
        "dc20": group(dc20_values),
        "per_landmark_mre_mm": per_landmark,
        "official_reference": {
            "mre_mm": OFFICIAL_AARIZ_BASELINE_MRE_MM,
            "sdr_2mm_percent": OFFICIAL_AARIZ_BASELINE_SDR2_PERCENT,
        },
        "beats_official_reference": bool(
            all29["mre_mm"] <= OFFICIAL_AARIZ_BASELINE_MRE_MM
            and all29["sdr_percent"]["2.0"] >= OFFICIAL_AARIZ_BASELINE_SDR2_PERCENT
        ),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _train_step_benchmark(model: nn.Module, batch_size: int, iterations: int = 2) -> dict[str, Any]:
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.MSELoss()
    torch.manual_seed(20260825 + batch_size)
    images = torch.rand((batch_size, 1, INPUT_SIZE, INPUT_SIZE), dtype=torch.float32)
    coords = torch.rand((batch_size, LANDMARK_COUNT, 2), dtype=torch.float32) * (INPUT_SIZE - 1)
    targets = batch_gaussian_heatmaps(coords)
    times: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        output = model(images)
        loss = criterion(output, targets)
        loss.backward()
        optimizer.step()
        times.append(time.perf_counter() - started)
    median = statistics.median(times)
    return {
        "batch_size": batch_size,
        "iterations": iterations,
        "median_step_s": round(median, 4),
        "samples_per_second": round(batch_size / median, 3),
    }


def smoke(output_dir: Path) -> dict[str, Any]:
    import onnx
    import onnxruntime as ort

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    torch.manual_seed(20260825)
    model = DCCephUNet29Q4(base_channels=16).eval()
    dummy = torch.zeros((1, 1, INPUT_SIZE, INPUT_SIZE), dtype=torch.float32)
    with torch.no_grad():
        output = model(dummy)
    expected = (1, LANDMARK_COUNT, HEATMAP_SIZE, HEATMAP_SIZE)
    if tuple(output.shape) != expected:
        raise RuntimeError(f"PyTorch Q4 contract mismatch: {tuple(output.shape)} != {expected}")

    onnx_path = output_dir / "dc_ceph_unet29_q4_untrained.onnx"
    torch.onnx.export(
        model,
        dummy,
        str(onnx_path),
        opset_version=17,
        input_names=["image"],
        output_names=["heatmaps"],
        dynamic_axes=None,
    )
    checked = onnx.load(str(onnx_path))
    onnx.checker.check_model(checked)

    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    ort_input = np.zeros((1, 1, INPUT_SIZE, INPUT_SIZE), dtype=np.float32)
    session.run(None, {session.get_inputs()[0].name: ort_input})
    inference_ms: list[float] = []
    ort_output = None
    for _ in range(3):
        started = time.perf_counter()
        ort_output = session.run(None, {session.get_inputs()[0].name: ort_input})[0]
        inference_ms.append((time.perf_counter() - started) * 1000.0)
    if ort_output is None or tuple(ort_output.shape) != expected:
        raise RuntimeError("ONNX Q4 output contract mismatch")

    train_benchmarks = []
    for batch_size in (1, 2, 4):
        benchmark_model = DCCephUNet29Q4(base_channels=16)
        train_benchmarks.append(_train_step_benchmark(benchmark_model, batch_size))
    best = max(train_benchmarks, key=lambda item: item["samples_per_second"])

    report = {
        "result": "PASS",
        "status": "UNTRAINED_Q4_TRAINING_CONTRACT_SMOKE_ONLY",
        "contract": {
            "input": [1, 1, INPUT_SIZE, INPUT_SIZE],
            "output": list(expected),
            "heatmap_stride": HEATMAP_STRIDE,
            "landmarks": LANDMARK_COUNT,
            "dc20_indices": list(DC20_INDICES),
            "ground_truth": "official_v1_ceil",
            "evaluation_space": "original_pixels_then_mm_per_pixel",
            "test_set_policy": "frozen_final_evaluation_only",
        },
        "model": {
            "base_channels": 16,
            "parameters": sum(parameter.numel() for parameter in model.parameters()),
        },
        "onnx": {
            "opset": 17,
            "size_mb": round(onnx_path.stat().st_size / (1024 * 1024), 3),
            "sha256": _sha256(onnx_path),
            "inference_median_ms": round(float(np.median(inference_ms)), 2),
        },
        "cpu_training": {
            "benchmarks": train_benchmarks,
            "best_batch_size_by_samples_per_second": best["batch_size"],
            "best_samples_per_second": best["samples_per_second"],
            "estimated_raw_epoch_minutes": round(700 / best["samples_per_second"] / 60.0, 3),
        },
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
            "threads": torch.get_num_threads(),
        },
    }
    (output_dir / "q4_smoke.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("p6-ceph-q4-smoke"))
    args = parser.parse_args()
    if not args.smoke:
        parser.error("training contract currently exposes --smoke only")
    smoke(args.output)


if __name__ == "__main__":
    main()
