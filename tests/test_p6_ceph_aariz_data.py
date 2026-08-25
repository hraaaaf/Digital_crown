from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from scripts.p6_ceph_aariz_data import (
    Aariz29GeometryDataset,
    LetterboxTransform,
    load_pixel_size_map,
    merge_reader_ground_truth,
)
from scripts.p6_ceph_aariz_mapping import AARIZ_OFFICIAL_TITLES


def _annotation_payload(order: tuple[str, ...], offset: float) -> dict:
    coordinate_book = {
        title: {
            "x": float(10 + index * 2) + offset,
            "y": float(20 + index * 2) + offset,
        }
        for index, title in enumerate(AARIZ_OFFICIAL_TITLES)
    }
    return {
        "landmarks": [
            {
                "landmark_id": f"id-{title}",
                "symbol": f"sym-{title}",
                "title": title,
                "value": coordinate_book[title],
            }
            for title in order
        ]
    }


def _write_case(root: Path, *, csv_columns=None) -> tuple[Path, Path]:
    image_id = "case001"
    split = root / "train"
    image_dir = split / "Cephalograms"
    junior_dir = split / "Annotations" / "Cephalometric Landmarks" / "Junior Orthodontists"
    senior_dir = split / "Annotations" / "Cephalometric Landmarks" / "Senior Orthodontists"
    image_dir.mkdir(parents=True)
    junior_dir.mkdir(parents=True)
    senior_dir.mkdir(parents=True)

    # Deliberately non-square. All landmarks remain inside native bounds.
    Image.new("L", (200, 120), color=128).save(image_dir / f"{image_id}.png")
    junior_path = junior_dir / f"{image_id}.json"
    senior_path = senior_dir / f"{image_id}.json"
    junior_path.write_text(
        json.dumps(_annotation_payload(AARIZ_OFFICIAL_TITLES, 0.2)), encoding="utf-8"
    )
    # Reverse one reader's JSON order to prove title-keyed merge.
    senior_path.write_text(
        json.dumps(_annotation_payload(tuple(reversed(AARIZ_OFFICIAL_TITLES)), 1.2)),
        encoding="utf-8",
    )

    columns = csv_columns or ["cephalogram_id", "machine", "pixel_size", "image_format", "mode"]
    with (root / "cephalogram_machine_mappings.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        row = {
            "cephalogram_id": image_id,
            "machine": "Synthetic",
            "pixel_size": "0.1",
            "image_format": "png",
            "mode": "synthetic",
        }
        writer.writerow({key: row[key] for key in columns})
    return junior_path, senior_path


def test_official_ground_truth_is_title_keyed_mean_then_ceil(tmp_path: Path) -> None:
    junior, senior = _write_case(tmp_path)
    merged = merge_reader_ground_truth(junior, senior, "official_v1_ceil")
    # First official title: junior=(10.2,20.2), senior=(11.2,21.2), mean=(10.7,20.7).
    assert torch.equal(torch.from_numpy(merged[0]), torch.tensor([11.0, 21.0]))


def test_unrounded_mean_is_explicit_research_policy(tmp_path: Path) -> None:
    junior, senior = _write_case(tmp_path)
    merged = merge_reader_ground_truth(junior, senior, "mean_float")
    assert np.allclose(merged[0], np.asarray([10.7, 20.7], dtype=np.float32))


def test_letterbox_preserves_aspect_and_inverse_coordinates(tmp_path: Path) -> None:
    _write_case(tmp_path)
    dataset = Aariz29GeometryDataset(tmp_path, "train", image_size=100)
    item = dataset[0]
    transform = LetterboxTransform(**item["transform"])

    assert item["image"].shape == (1, 100, 100)
    assert transform.scale == pytest.approx(0.5)
    assert transform.resized_width == 100
    assert transform.resized_height == 60
    assert transform.pad_left == 0
    assert transform.pad_top == 20

    restored = transform.inverse_xy(item["coords"].numpy())
    assert np.allclose(restored, item["coords_original"].numpy(), atol=1e-5)
    # Official ceil point (11,21) -> isotropic scale 0.5 + vertical pad 20.
    assert torch.allclose(item["coords"][0], torch.tensor([5.5, 30.5]))


def test_real_csv_shape_with_bom_and_extra_columns_is_accepted(tmp_path: Path) -> None:
    _write_case(tmp_path)
    mapping, columns = load_pixel_size_map(tmp_path / "cephalogram_machine_mappings.csv")
    assert mapping == {"case001": pytest.approx(0.1)}
    assert columns == ("cephalogram_id", "machine", "pixel_size", "image_format", "mode")


def test_missing_required_csv_column_fails_closed(tmp_path: Path) -> None:
    _write_case(tmp_path, csv_columns=["cephalogram_id", "machine"])
    with pytest.raises(ValueError, match="missing required columns"):
        load_pixel_size_map(tmp_path / "cephalogram_machine_mappings.csv")


def test_duplicate_calibration_id_fails_closed(tmp_path: Path) -> None:
    _write_case(tmp_path)
    csv_path = tmp_path / "cephalogram_machine_mappings.csv"
    with csv_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("case001,Synthetic,0.1,png,synthetic\n")
    with pytest.raises(ValueError, match="duplicate cephalogram_id"):
        load_pixel_size_map(csv_path)
