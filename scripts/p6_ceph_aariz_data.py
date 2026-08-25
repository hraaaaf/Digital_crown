#!/usr/bin/env python3
"""Strict research data contract for Aariz v1.

This module supersedes the initial square-stretch smoke loader for any future
training/evaluation work. It deliberately:
- keys annotations by anatomical title, never JSON array position;
- reproduces Aariz v1 benchmark ground truth with ceil(mean junior, senior);
- optionally exposes the unrounded mean as an explicit research policy;
- letterboxes with one isotropic scale and reversible coordinate metadata;
- validates calibration CSV requirements and duplicate IDs fail-closed.

No Digital Crown clinical runtime is wired here.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

try:  # package import under pytest/repo tooling
    from scripts.p6_ceph_aariz_mapping import AARIZ_OFFICIAL_TITLES
except ImportError:  # direct execution from scripts/
    from p6_ceph_aariz_mapping import AARIZ_OFFICIAL_TITLES

AARIZ_LANDMARK_COUNT = 29
AARIZ_SPLITS = {"train", "valid", "test"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
REQUIRED_CALIBRATION_COLUMNS = {"cephalogram_id", "pixel_size"}
GroundTruthPolicy = Literal["official_v1_ceil", "mean_float"]


@dataclass(frozen=True)
class LetterboxTransform:
    source_width: int
    source_height: int
    target_size: int
    scale: float
    resized_width: int
    resized_height: int
    pad_left: int
    pad_top: int

    @classmethod
    def build(cls, source_width: int, source_height: int, target_size: int) -> "LetterboxTransform":
        if source_width <= 0 or source_height <= 0 or target_size <= 0:
            raise ValueError("image dimensions and target_size must be positive")
        scale = min(target_size / float(source_width), target_size / float(source_height))
        resized_width = max(1, min(target_size, int(round(source_width * scale))))
        resized_height = max(1, min(target_size, int(round(source_height * scale))))
        pad_left = (target_size - resized_width) // 2
        pad_top = (target_size - resized_height) // 2
        return cls(
            source_width=source_width,
            source_height=source_height,
            target_size=target_size,
            scale=scale,
            resized_width=resized_width,
            resized_height=resized_height,
            pad_left=pad_left,
            pad_top=pad_top,
        )

    def forward_xy(self, coords: np.ndarray) -> np.ndarray:
        array = np.asarray(coords, dtype=np.float32)
        if array.ndim != 2 or array.shape[1] != 2:
            raise ValueError(f"coords must have shape [N,2], got {array.shape}")
        result = array.copy()
        result[:, 0] = result[:, 0] * self.scale + self.pad_left
        result[:, 1] = result[:, 1] * self.scale + self.pad_top
        return result

    def inverse_xy(self, coords: np.ndarray) -> np.ndarray:
        array = np.asarray(coords, dtype=np.float32)
        if array.ndim != 2 or array.shape[1] != 2:
            raise ValueError(f"coords must have shape [N,2], got {array.shape}")
        result = array.copy()
        result[:, 0] = (result[:, 0] - self.pad_left) / self.scale
        result[:, 1] = (result[:, 1] - self.pad_top) / self.scale
        return result

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _annotation_file(root: Path, split: str, reader: str, image_id: str) -> Path:
    return (
        root
        / split
        / "Annotations"
        / "Cephalometric Landmarks"
        / reader
        / f"{image_id}.json"
    )


def _parse_annotation_by_title(path: Path) -> dict[str, np.ndarray]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("landmarks")
    if not isinstance(items, list) or len(items) != AARIZ_LANDMARK_COUNT:
        raise ValueError(f"{path}: expected exactly {AARIZ_LANDMARK_COUNT} landmarks")

    by_title: dict[str, np.ndarray] = {}
    for index, item in enumerate(items):
        try:
            title = str(item["title"]).strip()
            x = float(item["value"]["x"])
            y = float(item["value"]["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{path}: malformed landmark at index {index}") from exc
        if not title or not np.isfinite(x) or not np.isfinite(y):
            raise ValueError(f"{path}: invalid landmark at index {index}")
        if title in by_title:
            raise ValueError(f"{path}: duplicate landmark title {title!r}")
        by_title[title] = np.asarray([x, y], dtype=np.float32)

    observed = set(by_title)
    expected = set(AARIZ_OFFICIAL_TITLES)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(f"{path}: Aariz ontology mismatch; missing={missing}, extra={extra}")
    return by_title


def merge_reader_ground_truth(
    junior_path: Path,
    senior_path: Path,
    policy: GroundTruthPolicy = "official_v1_ceil",
) -> np.ndarray:
    if policy not in {"official_v1_ceil", "mean_float"}:
        raise ValueError(f"unsupported ground-truth policy: {policy!r}")
    junior = _parse_annotation_by_title(junior_path)
    senior = _parse_annotation_by_title(senior_path)
    merged = np.asarray(
        [(junior[title] + senior[title]) * 0.5 for title in AARIZ_OFFICIAL_TITLES],
        dtype=np.float32,
    )
    if policy == "official_v1_ceil":
        merged = np.ceil(merged).astype(np.float32)
    return merged


def load_pixel_size_map(csv_path: Path) -> tuple[dict[str, float], tuple[str, ...]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(str(name).strip() for name in (reader.fieldnames or ()))
        if not REQUIRED_CALIBRATION_COLUMNS.issubset(fieldnames):
            raise ValueError(
                f"calibration CSV missing required columns; observed={list(fieldnames)}, "
                f"required={sorted(REQUIRED_CALIBRATION_COLUMNS)}"
            )
        mapping: dict[str, float] = {}
        for line_number, row in enumerate(reader, start=2):
            image_id = str(row.get("cephalogram_id", "")).strip()
            try:
                pixel_size = float(row.get("pixel_size", ""))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid pixel_size at CSV line {line_number}") from exc
            if not image_id or not np.isfinite(pixel_size) or pixel_size <= 0:
                raise ValueError(f"invalid calibration row at CSV line {line_number}")
            if image_id in mapping:
                raise ValueError(f"duplicate cephalogram_id in calibration CSV: {image_id}")
            mapping[image_id] = pixel_size
    if not mapping:
        raise ValueError("calibration CSV contains no rows")
    return mapping, fieldnames


def letterbox_grayscale(image: Image.Image, transform: LetterboxTransform) -> Image.Image:
    source = image.convert("L")
    if source.size != (transform.source_width, transform.source_height):
        raise ValueError("letterbox transform does not match source image dimensions")
    resized = source.resize(
        (transform.resized_width, transform.resized_height),
        Image.Resampling.BICUBIC,
    )
    canvas = Image.new("L", (transform.target_size, transform.target_size), color=0)
    canvas.paste(resized, (transform.pad_left, transform.pad_top))
    return canvas


class Aariz29GeometryDataset(Dataset):
    """Aariz v1 loader with title-keyed truth and reversible isotropic letterbox."""

    def __init__(
        self,
        root: str | Path,
        split: str,
        image_size: int = 512,
        ground_truth_policy: GroundTruthPolicy = "official_v1_ceil",
    ) -> None:
        if split not in AARIZ_SPLITS:
            raise ValueError(f"split must be one of {sorted(AARIZ_SPLITS)}, got {split!r}")
        if image_size <= 0:
            raise ValueError("image_size must be positive")
        if ground_truth_policy not in {"official_v1_ceil", "mean_float"}:
            raise ValueError(f"unsupported ground-truth policy: {ground_truth_policy!r}")

        self.root = Path(root)
        self.split = split
        self.image_size = int(image_size)
        self.ground_truth_policy = ground_truth_policy

        image_dir = self.root / split / "Cephalograms"
        if not image_dir.is_dir():
            raise FileNotFoundError(f"missing Aariz image directory: {image_dir}")
        self.images = sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
        if not self.images:
            raise RuntimeError(f"no cephalograms found in {image_dir}")
        image_ids = [path.stem for path in self.images]
        if len(set(image_ids)) != len(image_ids):
            raise RuntimeError("duplicate cephalogram stems across image extensions")

        calibration_path = self.root / "cephalogram_machine_mappings.csv"
        if not calibration_path.is_file():
            raise FileNotFoundError(f"missing Aariz pixel-size mapping: {calibration_path}")
        self.pixel_size_mm, self.calibration_columns = load_pixel_size_map(calibration_path)

        for image_path in self.images:
            image_id = image_path.stem
            for reader in ("Junior Orthodontists", "Senior Orthodontists"):
                annotation_path = _annotation_file(self.root, split, reader, image_id)
                if not annotation_path.is_file():
                    raise FileNotFoundError(f"missing Aariz annotation: {annotation_path}")
            if image_id not in self.pixel_size_mm:
                raise KeyError(f"missing pixel-size mapping for {image_id}")

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, index: int) -> dict[str, Any]:
        image_path = self.images[index]
        image_id = image_path.stem
        coords_original = merge_reader_ground_truth(
            _annotation_file(self.root, self.split, "Junior Orthodontists", image_id),
            _annotation_file(self.root, self.split, "Senior Orthodontists", image_id),
            self.ground_truth_policy,
        )

        with Image.open(image_path) as source:
            image = source.convert("L")
        width, height = image.size
        if np.any(coords_original < 0) or np.any(coords_original[:, 0] >= width) or np.any(
            coords_original[:, 1] >= height
        ):
            raise ValueError(f"{image_id}: annotation lies outside original image bounds")

        transform = LetterboxTransform.build(width, height, self.image_size)
        network_image = letterbox_grayscale(image, transform)
        coords_network = transform.forward_xy(coords_original)
        if np.any(coords_network < 0) or np.any(coords_network >= self.image_size):
            raise ValueError(f"{image_id}: transformed annotation lies outside network canvas")

        image_array = np.asarray(network_image, dtype=np.float32) / 255.0
        return {
            "image": torch.from_numpy(image_array).unsqueeze(0),
            "coords": torch.from_numpy(coords_network.astype(np.float32)),
            "coords_original": torch.from_numpy(coords_original.astype(np.float32)),
            "landmark_names": AARIZ_OFFICIAL_TITLES,
            "image_id": image_id,
            "pixel_size_mm": float(self.pixel_size_mm[image_id]),
            "original_size": (width, height),
            "ground_truth_policy": self.ground_truth_policy,
            "transform": transform.as_dict(),
        }
