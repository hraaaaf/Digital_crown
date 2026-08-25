import csv
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from scripts.p6_ceph_unet29 import (
    AARIZ_LANDMARK_COUNT,
    Aariz29Dataset,
    DCCephUNet29,
    gaussian_heatmaps,
)


def _write_synthetic_aariz(root: Path) -> None:
    image_id = "case001"
    image_dir = root / "train" / "Cephalograms"
    junior_dir = (
        root
        / "train"
        / "Annotations"
        / "Cephalometric Landmarks"
        / "Junior Orthodontists"
    )
    senior_dir = (
        root
        / "train"
        / "Annotations"
        / "Cephalometric Landmarks"
        / "Senior Orthodontists"
    )
    image_dir.mkdir(parents=True)
    junior_dir.mkdir(parents=True)
    senior_dir.mkdir(parents=True)
    Image.new("L", (200, 100), color=128).save(image_dir / f"{image_id}.png")

    def payload(offset: float) -> dict:
        return {
            "landmarks": [
                {
                    "title": f"L{index:02d}",
                    "value": {"x": float(index + 1 + offset), "y": float(index + 2 + offset)},
                }
                for index in range(AARIZ_LANDMARK_COUNT)
            ]
        }

    (junior_dir / f"{image_id}.json").write_text(json.dumps(payload(0.0)), encoding="utf-8")
    (senior_dir / f"{image_id}.json").write_text(json.dumps(payload(2.0)), encoding="utf-8")

    with (root / "cephalogram_machine_mappings.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["cephalogram_id", "pixel_size"])
        writer.writeheader()
        writer.writerow({"cephalogram_id": image_id, "pixel_size": "0.1"})


def test_loader_averages_two_readers_and_scales_coordinates(tmp_path: Path) -> None:
    _write_synthetic_aariz(tmp_path)
    dataset = Aariz29Dataset(tmp_path, "train", image_size=512, augment=False)
    item = dataset[0]
    assert item["image"].shape == (1, 512, 512)
    assert item["coords"].shape == (AARIZ_LANDMARK_COUNT, 2)
    # Reader mean for landmark 0 is x=2, y=3. Native image is 200x100.
    assert torch.allclose(item["coords"][0], torch.tensor([2.0 * 512 / 200, 3.0 * 512 / 100]))
    assert len(item["landmark_names"]) == AARIZ_LANDMARK_COUNT
    assert item["pixel_size_mm"] == pytest.approx(0.1)


def test_train_intensity_augmentation_is_deterministic(tmp_path: Path) -> None:
    _write_synthetic_aariz(tmp_path)
    first = Aariz29Dataset(tmp_path, "train", image_size=64, augment=True, seed=7)
    second = Aariz29Dataset(tmp_path, "train", image_size=64, augment=True, seed=7)
    first.set_epoch(3)
    second.set_epoch(3)
    assert torch.equal(first[0]["image"], second[0]["image"])
    assert torch.equal(first[0]["coords"], second[0]["coords"])


def test_augmentation_is_rejected_outside_train(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="train-only"):
        Aariz29Dataset(tmp_path, "valid", augment=True)


def test_unet29_preserves_spatial_shape() -> None:
    torch.manual_seed(1)
    model = DCCephUNet29(base_channels=16).eval()
    with torch.no_grad():
        output = model(torch.zeros((1, 1, 64, 64), dtype=torch.float32))
    assert output.shape == (1, AARIZ_LANDMARK_COUNT, 64, 64)


def test_gaussian_heatmaps_contract() -> None:
    coords = torch.full((AARIZ_LANDMARK_COUNT, 2), 16.0)
    heatmaps = gaussian_heatmaps(coords, 32, 32, sigma_px=2.0)
    assert heatmaps.shape == (AARIZ_LANDMARK_COUNT, 32, 32)
    peaks = torch.argmax(heatmaps.flatten(1), dim=1)
    expected_peak = 16 * 32 + 16
    assert np.all(peaks.cpu().numpy() == expected_peak)
