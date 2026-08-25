#!/usr/bin/env python3
"""One-shot Aariz v1 provenance, schema and CPU-training feasibility probe.

Research-only. The public Aariz archive is downloaded by CI, verified, inspected
locally on the runner and then deleted with the workspace. Only a compact JSON
manifest is uploaded. No radiograph or annotation is re-published as an artifact.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import resource
import statistics
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from p6_ceph_aariz_mapping import AARIZ_OFFICIAL_TITLES
from p6_ceph_unet29 import Aariz29Dataset, DCCephUNet29, gaussian_heatmaps

EXPECTED_FILE_ID = 51041642
EXPECTED_FILE_NAME = "Aariz.zip"
EXPECTED_SIZE_BYTES = 2_098_209_792
EXPECTED_MD5 = "e0bd645bca6759abdae4f199d841bda6"
EXPECTED_SPLITS = {"train": 700, "valid": 150, "test": 150}
EXPECTED_CSV_COLUMNS = {"cephalogram_id", "pixel_size"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def _hash_file(path: Path) -> dict[str, str]:
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return {"md5": md5.hexdigest(), "sha256": sha256.hexdigest()}


def _safe_extract(zip_path: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    resolved_destination = destination.resolve()
    started = time.perf_counter()
    with zipfile.ZipFile(zip_path) as archive:
        members = archive.infolist()
        if not members:
            raise RuntimeError("Aariz archive is empty")
        total_uncompressed = sum(item.file_size for item in members)
        if total_uncompressed > 12 * 1024**3:
            raise RuntimeError(f"refusing unexpectedly large expanded archive: {total_uncompressed}")
        for item in members:
            if item.flag_bits & 0x1:
                raise RuntimeError(f"encrypted archive member is not allowed: {item.filename}")
            target = (destination / item.filename).resolve()
            if target != resolved_destination and resolved_destination not in target.parents:
                raise RuntimeError(f"unsafe archive path: {item.filename}")
        archive.extractall(destination)
    return {
        "members": len(members),
        "uncompressed_bytes": total_uncompressed,
        "elapsed_s": round(time.perf_counter() - started, 3),
    }


def _find_dataset_root(extracted: Path) -> Path:
    matches = list(extracted.rglob("cephalogram_machine_mappings.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one calibration CSV, found {len(matches)}")
    root = matches[0].parent
    for split in EXPECTED_SPLITS:
        if not (root / split / "Cephalograms").is_dir():
            raise RuntimeError(f"missing expected split directory under {root}: {split}")
    return root


def _read_calibration(csv_path: Path) -> tuple[dict[str, float], dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = [str(name).strip() for name in (reader.fieldnames or [])]
        if not EXPECTED_CSV_COLUMNS.issubset(fieldnames):
            raise RuntimeError(
                f"unexpected calibration CSV schema: {fieldnames}; "
                f"required={sorted(EXPECTED_CSV_COLUMNS)}"
            )
        mapping: dict[str, float] = {}
        extra_columns = [name for name in fieldnames if name not in EXPECTED_CSV_COLUMNS]
        for line_number, row in enumerate(reader, start=2):
            image_id = str(row.get("cephalogram_id", "")).strip()
            try:
                pixel_size = float(row.get("pixel_size", ""))
            except ValueError as exc:
                raise RuntimeError(f"invalid pixel_size at CSV line {line_number}") from exc
            if not image_id or not np.isfinite(pixel_size) or pixel_size <= 0:
                raise RuntimeError(f"invalid calibration row at line {line_number}: {row}")
            if image_id in mapping:
                raise RuntimeError(f"duplicate cephalogram_id in calibration CSV: {image_id}")
            mapping[image_id] = pixel_size
    if len(mapping) != 1000:
        raise RuntimeError(f"expected 1000 calibration rows, got {len(mapping)}")
    values = list(mapping.values())
    return mapping, {
        "columns": fieldnames,
        "extra_columns": extra_columns,
        "rows": len(mapping),
        "pixel_size_mm_per_px": {
            "min": min(values),
            "max": max(values),
            "median": statistics.median(values),
        },
    }


def _load_annotation(path: Path) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    landmarks = payload.get("landmarks")
    if not isinstance(landmarks, list) or len(landmarks) != 29:
        raise RuntimeError(f"{path}: expected 29 landmarks")
    titles: list[str] = []
    symbols: list[str] = []
    key_shapes: list[str] = []
    for index, item in enumerate(landmarks):
        if not isinstance(item, dict):
            raise RuntimeError(f"{path}: landmark {index} is not an object")
        value = item.get("value")
        if not isinstance(value, dict) or "x" not in value or "y" not in value:
            raise RuntimeError(f"{path}: malformed coordinate at landmark {index}")
        x, y = float(value["x"]), float(value["y"])
        if not np.isfinite(x) or not np.isfinite(y):
            raise RuntimeError(f"{path}: non-finite coordinate at landmark {index}")
        titles.append(str(item.get("title", "")).strip())
        symbols.append(str(item.get("symbol", "")).strip())
        key_shapes.append(",".join(sorted(item.keys())))
    return tuple(titles), tuple(symbols), tuple(key_shapes)


def _audit_dataset(root: Path, calibration: dict[str, float]) -> dict[str, Any]:
    expected_title_set = set(AARIZ_OFFICIAL_TITLES)
    all_ids: set[str] = set()
    observed_key_shapes: set[str] = set()
    observed_title_orders: set[tuple[str, ...]] = set()
    observed_symbol_orders: set[tuple[str, ...]] = set()
    split_report: dict[str, Any] = {}

    for split, expected_count in EXPECTED_SPLITS.items():
        split_root = root / split
        image_dir = split_root / "Cephalograms"
        images = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
        image_ids = [p.stem for p in images]
        if len(images) != expected_count or len(set(image_ids)) != expected_count:
            raise RuntimeError(
                f"{split}: expected {expected_count} unique images, got {len(images)} / {len(set(image_ids))}"
            )
        overlap = all_ids.intersection(image_ids)
        if overlap:
            raise RuntimeError(f"split leakage detected in {split}: {sorted(overlap)[:5]}")
        all_ids.update(image_ids)

        annotator_counts: dict[str, int] = {}
        for reader in ("Junior Orthodontists", "Senior Orthodontists"):
            ann_dir = split_root / "Annotations" / "Cephalometric Landmarks" / reader
            files = sorted(ann_dir.glob("*.json"))
            annotator_counts[reader] = len(files)
            if len(files) != expected_count:
                raise RuntimeError(f"{split}/{reader}: expected {expected_count} annotations, got {len(files)}")
            ann_ids = {p.stem for p in files}
            if ann_ids != set(image_ids):
                raise RuntimeError(f"{split}/{reader}: annotation/image ID mismatch")
            for path in files:
                titles, symbols, key_shapes = _load_annotation(path)
                observed_title_orders.add(titles)
                observed_symbol_orders.add(symbols)
                observed_key_shapes.update(key_shapes)
                if any(titles):
                    if set(titles) != expected_title_set or len(set(titles)) != 29:
                        raise RuntimeError(f"{path}: title ontology does not match official Aariz 29")

        missing_calibration = sorted(set(image_ids) - calibration.keys())
        if missing_calibration:
            raise RuntimeError(f"{split}: missing calibration for {missing_calibration[:5]}")
        split_report[split] = {
            "images": len(images),
            "annotations": annotator_counts,
        }

    if len(all_ids) != 1000:
        raise RuntimeError(f"expected 1000 unique IDs across splits, got {len(all_ids)}")
    extra_calibration = sorted(calibration.keys() - all_ids)
    if extra_calibration:
        raise RuntimeError(f"calibration CSV contains IDs outside split images: {extra_calibration[:5]}")

    title_orders_nonempty = [order for order in observed_title_orders if any(order)]
    return {
        "unique_image_ids": len(all_ids),
        "splits": split_report,
        "annotation_item_key_shapes": sorted(observed_key_shapes),
        "distinct_title_orders": len(title_orders_nonempty),
        "distinct_symbol_orders": len([order for order in observed_symbol_orders if any(order)]),
        "title_field_present": bool(title_orders_nonempty),
        "symbol_field_present": any(any(order) for order in observed_symbol_orders),
    }


def _real_loader_probe(root: Path) -> dict[str, Any]:
    dataset = Aariz29Dataset(root, "train", image_size=512, augment=False)
    sample = dataset[0]
    titles = tuple(sample["landmark_names"])
    if set(titles) != set(AARIZ_OFFICIAL_TITLES):
        raise RuntimeError("production candidate loader did not preserve the official Aariz ontology")
    return {
        "samples": len(dataset),
        "first_image_id": sample["image_id"],
        "image_shape": list(sample["image"].shape),
        "coords_shape": list(sample["coords"].shape),
        "pixel_size_mm": sample["pixel_size_mm"],
        "landmarks": len(titles),
    }


def _cpu_training_probe(root: Path, iterations: int = 3) -> dict[str, Any]:
    threads = min(4, os.cpu_count() or 1)
    torch.set_num_threads(threads)
    dataset = Aariz29Dataset(root, "train", image_size=512, augment=False)
    sample = dataset[0]
    image = sample["image"].unsqueeze(0)
    coords = sample["coords"]
    target = gaussian_heatmaps(coords, 512, 512, sigma_px=5.0).unsqueeze(0)

    torch.manual_seed(20260825)
    model = DCCephUNet29(base_channels=16).train()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.MSELoss()

    times: list[float] = []
    losses: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        optimizer.zero_grad(set_to_none=True)
        output = model(image)
        if output.shape != target.shape:
            raise RuntimeError(f"training tensor mismatch: output={output.shape}, target={target.shape}")
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        times.append(time.perf_counter() - started)
        losses.append(float(loss.detach()))

    median_s = statistics.median(times)
    estimated_epoch_minutes = median_s * EXPECTED_SPLITS["train"] / 60.0
    return {
        "threads": threads,
        "batch_size": 1,
        "iterations": iterations,
        "step_seconds": {
            "min": round(min(times), 3),
            "median": round(median_s, 3),
            "max": round(max(times), 3),
        },
        "estimated_epoch_minutes_batch1": round(estimated_epoch_minutes, 2),
        "losses": [round(value, 8) for value in losses],
        "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    parser.add_argument("--extract-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)

    started = time.perf_counter()
    size_bytes = zip_path.stat().st_size
    hashes = _hash_file(zip_path)
    if size_bytes != EXPECTED_SIZE_BYTES:
        raise RuntimeError(f"Figshare file-size mismatch: expected {EXPECTED_SIZE_BYTES}, got {size_bytes}")
    if hashes["md5"] != EXPECTED_MD5:
        raise RuntimeError(f"Figshare MD5 mismatch: expected {EXPECTED_MD5}, got {hashes['md5']}")

    extract_report = _safe_extract(zip_path, Path(args.extract_dir))
    root = _find_dataset_root(Path(args.extract_dir))
    calibration, csv_report = _read_calibration(root / "cephalogram_machine_mappings.csv")
    dataset_report = _audit_dataset(root, calibration)
    loader_report = _real_loader_probe(root)
    training_report = _cpu_training_probe(root)

    payload = {
        "result": "PASS",
        "status": "RESEARCH_DATA_PROBE_ONLY",
        "figshare": {
            "article_id": 27986417,
            "file_id": EXPECTED_FILE_ID,
            "file_name": EXPECTED_FILE_NAME,
            "size_bytes": size_bytes,
            **hashes,
            "license": "CC BY 4.0",
        },
        "archive": extract_report,
        "dataset_root_name": root.name,
        "calibration_csv": csv_report,
        "dataset": dataset_report,
        "loader": loader_report,
        "cpu_training_probe": training_report,
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
            "logical_cpu_count": os.cpu_count(),
        },
        "elapsed_s": round(time.perf_counter() - started, 3),
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
