#!/usr/bin/env python3
"""Research-only all-29 Aariz cephalometric baseline.

No Digital Crown clinical runtime wiring is changed here. The module provides:
- a strict Aariz v1 loader that averages junior/senior annotations;
- deterministic intensity-only training augmentation;
- a Digital Crown-owned U-Net-style 29-heatmap model;
- an ONNX portability smoke command.

Geometric augmentation and Wits occlusal-point derivation are intentionally not
implemented in this baseline because both require separately validated geometry.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageEnhance
from torch import nn
from torch.utils.data import Dataset

AARIZ_LANDMARK_COUNT = 29
AARIZ_IMAGE_SIZE = 512
AARIZ_SPLITS = {"train", "valid", "test"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class AugmentationContract:
    version: str = "v1"
    train_only: bool = True
    horizontal_flip: bool = False
    geometric_transform: bool = False
    brightness_range: tuple[float, float] = (0.90, 1.10)
    contrast_range: tuple[float, float] = (0.90, 1.10)
    gaussian_noise_std: float = 0.01


AUGMENTATION_CONTRACT = AugmentationContract()


def _stable_rng(seed: int, epoch: int, image_id: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{seed}:{epoch}:{image_id}".encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def _annotation_file(root: Path, split: str, reader: str, image_id: str) -> Path:
    return (
        root
        / split
        / "Annotations"
        / "Cephalometric Landmarks"
        / reader
        / f"{image_id}.json"
    )


def _parse_annotation(path: Path) -> tuple[list[str], np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("landmarks")
    if not isinstance(items, list) or len(items) != AARIZ_LANDMARK_COUNT:
        raise ValueError(
            f"{path}: expected exactly {AARIZ_LANDMARK_COUNT} landmarks, "
            f"got {len(items) if isinstance(items, list) else type(items).__name__}"
        )

    names: list[str] = []
    coords: list[list[float]] = []
    for index, item in enumerate(items):
        try:
            name = str(item["title"]).strip()
            x = float(item["value"]["x"])
            y = float(item["value"]["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{path}: malformed landmark at index {index}") from exc
        if not name or not np.isfinite(x) or not np.isfinite(y):
            raise ValueError(f"{path}: invalid landmark at index {index}")
        names.append(name)
        coords.append([x, y])
    if len(set(names)) != AARIZ_LANDMARK_COUNT:
        raise ValueError(f"{path}: landmark titles must be unique")
    return names, np.asarray(coords, dtype=np.float32)


class Aariz29Dataset(Dataset):
    """Strict loader for the observed Aariz expanded train/valid/test layout."""

    def __init__(
        self,
        root: str | Path,
        split: str,
        image_size: int = AARIZ_IMAGE_SIZE,
        augment: bool = False,
        seed: int = 20260825,
    ) -> None:
        if split not in AARIZ_SPLITS:
            raise ValueError(f"split must be one of {sorted(AARIZ_SPLITS)}, got {split!r}")
        if augment and split != "train":
            raise ValueError("augmentation is train-only by contract")
        if image_size <= 0:
            raise ValueError("image_size must be positive")

        self.root = Path(root)
        self.split = split
        self.image_size = int(image_size)
        self.augment = augment
        self.seed = int(seed)
        self.epoch = 0

        image_dir = self.root / split / "Cephalograms"
        if not image_dir.is_dir():
            raise FileNotFoundError(f"missing Aariz image directory: {image_dir}")
        self.images = sorted(
            path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES
        )
        if not self.images:
            raise RuntimeError(f"no cephalograms found in {image_dir}")

        mapping_path = self.root / "cephalogram_machine_mappings.csv"
        if not mapping_path.is_file():
            raise FileNotFoundError(f"missing Aariz pixel-size mapping: {mapping_path}")
        self.pixel_size_mm: dict[str, float] = {}
        with mapping_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                image_id = str(row.get("cephalogram_id", "")).strip()
                try:
                    pixel_size = float(row.get("pixel_size", ""))
                except ValueError as exc:
                    raise ValueError(f"invalid pixel_size for {image_id!r}") from exc
                if not image_id or not np.isfinite(pixel_size) or pixel_size <= 0:
                    raise ValueError(f"invalid pixel-size mapping row: {row}")
                self.pixel_size_mm[image_id] = pixel_size

        # Fail early if any image lacks either annotation or calibration metadata.
        for image_path in self.images:
            image_id = image_path.stem
            for reader in ("Junior Orthodontists", "Senior Orthodontists"):
                annotation = _annotation_file(self.root, split, reader, image_id)
                if not annotation.is_file():
                    raise FileNotFoundError(f"missing Aariz annotation: {annotation}")
            if image_id not in self.pixel_size_mm:
                raise KeyError(f"missing pixel-size mapping for {image_id}")

    def set_epoch(self, epoch: int) -> None:
        self.epoch = int(epoch)

    def __len__(self) -> int:
        return len(self.images)

    def _apply_intensity_augmentation(self, image: Image.Image, image_id: str) -> Image.Image:
        rng = _stable_rng(self.seed, self.epoch, image_id)
        brightness = float(rng.uniform(*AUGMENTATION_CONTRACT.brightness_range))
        contrast = float(rng.uniform(*AUGMENTATION_CONTRACT.contrast_range))
        image = ImageEnhance.Brightness(image).enhance(brightness)
        image = ImageEnhance.Contrast(image).enhance(contrast)
        array = np.asarray(image, dtype=np.float32) / 255.0
        noise = rng.normal(0.0, AUGMENTATION_CONTRACT.gaussian_noise_std, array.shape)
        array = np.clip(array + noise, 0.0, 1.0)
        return Image.fromarray(np.rint(array * 255.0).astype(np.uint8), mode="L")

    def __getitem__(self, index: int) -> dict[str, Any]:
        image_path = self.images[index]
        image_id = image_path.stem
        junior_names, junior = _parse_annotation(
            _annotation_file(self.root, self.split, "Junior Orthodontists", image_id)
        )
        senior_names, senior = _parse_annotation(
            _annotation_file(self.root, self.split, "Senior Orthodontists", image_id)
        )
        if junior_names != senior_names:
            raise ValueError(f"{image_id}: junior/senior landmark name/order mismatch")

        coords = (junior + senior) * 0.5
        with Image.open(image_path) as source:
            image = source.convert("L")
        original_width, original_height = image.size
        if original_width <= 0 or original_height <= 0:
            raise ValueError(f"{image_path}: invalid image dimensions")

        image = image.resize((self.image_size, self.image_size), Image.Resampling.BICUBIC)
        coords[:, 0] *= self.image_size / float(original_width)
        coords[:, 1] *= self.image_size / float(original_height)
        if np.any(coords < 0) or np.any(coords[:, 0] >= self.image_size) or np.any(
            coords[:, 1] >= self.image_size
        ):
            raise ValueError(f"{image_id}: annotation lies outside resized image bounds")

        if self.augment:
            image = self._apply_intensity_augmentation(image, image_id)
        image_array = np.asarray(image, dtype=np.float32) / 255.0
        image_tensor = torch.from_numpy(image_array).unsqueeze(0)

        return {
            "image": image_tensor,
            "coords": torch.from_numpy(coords.astype(np.float32)),
            "landmark_names": tuple(junior_names),
            "image_id": image_id,
            "pixel_size_mm": float(self.pixel_size_mm[image_id]),
            "original_size": (int(original_width), int(original_height)),
        }


def gaussian_heatmaps(
    coords: torch.Tensor,
    height: int,
    width: int,
    sigma_px: float = 5.0,
) -> torch.Tensor:
    if coords.shape != (AARIZ_LANDMARK_COUNT, 2):
        raise ValueError(f"coords must be [{AARIZ_LANDMARK_COUNT}, 2], got {tuple(coords.shape)}")
    if sigma_px <= 0:
        raise ValueError("sigma_px must be positive")
    ys = torch.arange(height, dtype=torch.float32, device=coords.device).view(1, height, 1)
    xs = torch.arange(width, dtype=torch.float32, device=coords.device).view(1, 1, width)
    cx = coords[:, 0].view(-1, 1, 1)
    cy = coords[:, 1].view(-1, 1, 1)
    return torch.exp(-((xs - cx) ** 2 + (ys - cy) ** 2) / (2.0 * sigma_px**2))


class DoubleConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1, bias=False),
            nn.GroupNorm(min(8, out_channels), out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.GroupNorm(min(8, out_channels), out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class UpBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.conv = DoubleConv(out_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        if x.shape[-2:] != skip.shape[-2:]:
            raise RuntimeError(f"decoder/skip shape mismatch: {x.shape} vs {skip.shape}")
        return self.conv(torch.cat([skip, x], dim=1))


class DCCephUNet29(nn.Module):
    """Digital Crown-owned U-Net-style 29-landmark heatmap baseline."""

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
        self.up2 = UpBlock(c3, c2, c2)
        self.up1 = UpBlock(c2, c1, c1)
        self.head = nn.Conv2d(c1, AARIZ_LANDMARK_COUNT, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 4 or x.shape[1] != 1:
            raise ValueError(f"expected BCHW grayscale tensor, got {tuple(x.shape)}")
        if x.shape[-1] % 16 or x.shape[-2] % 16:
            raise ValueError("height and width must be divisible by 16")
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))
        b = self.bottleneck(self.pool(e4))
        d4 = self.up4(b, e4)
        d3 = self.up3(d4, e3)
        d2 = self.up2(d3, e2)
        d1 = self.up1(d2, e1)
        return self.head(d1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def smoke(output_dir: Path) -> dict[str, Any]:
    import onnx
    import onnxruntime as ort

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(20260825)
    model = DCCephUNet29(base_channels=16).eval()
    dummy = torch.zeros((1, 1, AARIZ_IMAGE_SIZE, AARIZ_IMAGE_SIZE), dtype=torch.float32)
    with torch.no_grad():
        output = model(dummy)
    expected = (1, AARIZ_LANDMARK_COUNT, AARIZ_IMAGE_SIZE, AARIZ_IMAGE_SIZE)
    if tuple(output.shape) != expected:
        raise RuntimeError(f"PyTorch contract mismatch: {tuple(output.shape)} != {expected}")

    onnx_path = output_dir / "dc_ceph_unet29_untrained.onnx"
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

    started = time.perf_counter()
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    cold_load_ms = (time.perf_counter() - started) * 1000.0
    ort_input = np.zeros((1, 1, AARIZ_IMAGE_SIZE, AARIZ_IMAGE_SIZE), dtype=np.float32)
    session.run(None, {session.get_inputs()[0].name: ort_input})
    times_ms: list[float] = []
    ort_output = None
    for _ in range(3):
        started = time.perf_counter()
        ort_output = session.run(None, {session.get_inputs()[0].name: ort_input})[0]
        times_ms.append((time.perf_counter() - started) * 1000.0)
    if ort_output is None or tuple(ort_output.shape) != expected:
        raise RuntimeError(f"ONNX contract mismatch: {None if ort_output is None else ort_output.shape}")

    report = {
        "result": "PASS",
        "status": "UNTRAINED_ARCHITECTURE_SMOKE_ONLY",
        "contract": {
            "input": [1, 1, AARIZ_IMAGE_SIZE, AARIZ_IMAGE_SIZE],
            "output": list(expected),
            "landmarks": AARIZ_LANDMARK_COUNT,
            "augmentation": asdict(AUGMENTATION_CONTRACT),
        },
        "model": {
            "base_channels": 16,
            "parameters": sum(parameter.numel() for parameter in model.parameters()),
        },
        "onnx": {
            "opset": 17,
            "size_mb": round(onnx_path.stat().st_size / (1024 * 1024), 3),
            "sha256": _sha256(onnx_path),
        },
        "cpu": {
            "provider": session.get_providers(),
            "cold_load_ms": round(cold_load_ms, 2),
            "inference_ms": {
                "iterations": 3,
                "mean": round(float(np.mean(times_ms)), 2),
                "median": round(float(np.median(times_ms)), 2),
                "min": round(float(np.min(times_ms)), 2),
                "max": round(float(np.max(times_ms)), 2),
            },
        },
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
        },
    }
    (output_dir / "smoke.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("p6-ceph-unet29-smoke"))
    args = parser.parse_args()
    if not args.smoke:
        parser.error("research baseline currently exposes --smoke only; training is a later gated step")
    smoke(args.output)


if __name__ == "__main__":
    main()
