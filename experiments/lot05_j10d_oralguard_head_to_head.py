#!/usr/bin/env python3
"""LOT05/05.7-J10D: research-only 4-class OralGuard benchmark on DENTEX.

The same first 74 annotated DENTEX diagnosis/test films as Noah baseline.
No patient identifiers, images, model bytes, or predictions retained as CI artifacts.
Metrics are exploratory due to potential source/training overlap; not diagnosis.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import statistics
import time
import traceback

from datasets import load_dataset
from huggingface_hub import HfApi, hf_hub_download
from ultralytics import YOLO

REPOSITORY = "Enosh729/oralguard"
FILENAME = "oralguard_det_best.pt"
OUT = Path(os.environ.get("LOT05_ORALGUARD_REPORT", "lot05-oralguard-head-to-head.json"))
THRESHOLDS = (0.10, 0.25, 0.45)
RESOLUTIONS = (640, 1024)
EXPECTED_CASES = 74
MATCH_IOU = 0.50
CLASS_NAMES = ("Caries", "Deep Caries", "Impacted", "Periapical Lesion")
GROUND_TO_CANONICAL = {0: 2, 1: 0, 2: 3, 3: 1}
report = {
    "mission": "LOT05/05.7-J10D",
    "model": REPOSITORY,
    "weight_file": FILENAME,
    "dataset": "tirandazdylan/dentex-panoramic",
    "dataset_split": "diagnosis/test",
    "images_requested": EXPECTED_CASES,
    "compared_against": "NoahOksuz/DentalXrayAI exploratory 74-image report",
    "licensing": "HF model card MIT; upstream Ultralytics and DENTEX licensing NOT cleared",
    "status": "PENDING",
    "clinical_acceptance": False,
    "commercial_authorization_verified": False,
    "overlapping_training_images_excluded": False,
    "confidence_thresholds": THRESHOLDS,
    "input_resolutions": RESOLUTIONS,
    "match_iou": MATCH_IOU,
    "score_definition": "greedy one-to-one IoU>=0.5 matched object precision/recall, not AP",
}


def normalize_label(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


MODEL_TO_CANONICAL = {
    "caries": 0, "deepcaries": 1, "impacted": 2, "impactedtooth": 2,
    "periapicallesion": 3, "periapicallesions": 3, "periapical": 3,
}


def inspect_model_classes(names: dict) -> dict[int, int]:
    values = {int(k): str(v) for k, v in names.items()}
    observed = {}
    for index, name in values.items():
        key = normalize_label(name)
        if key not in MODEL_TO_CANONICAL:
            raise ValueError(f"Unrecognised checkpoint pathology class: {index}={name}")
        observed[index] = MODEL_TO_CANONICAL[key]
    if len(observed) != 4 or set(observed.values()) != set(range(4)):
        raise ValueError(f"Expected four distinct pathology classes, got {values} mapped {observed}")
    report["checkpoint_classes"] = values
    report["checkpoint_index_to_canonical"] = observed
    return observed


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ground_truth(row):
    objects = row["objects"]
    if isinstance(objects, dict):
        boxes, labels = objects["bbox"], objects["diagnosis"]
    else:
        boxes = [item["bbox"] for item in objects]
        labels = [item["diagnosis"] for item in objects]
    ground = []
    for box, label in zip(boxes, labels):
        x, y, width, height = map(float, box)
        key = int(label)
        if key not in GROUND_TO_CANONICAL:
            raise ValueError(f"Unknown DENTEX diagnosis index: {key}")
        ground.append((GROUND_TO_CANONICAL[key], [x, y, x + width, y + height]))
    return ground


def overlap(a, b):
    width = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    height = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = width * height
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return intersection / max(1e-9, area_a + area_b - intersection)


def match(ground, predictions, minimum_confidence):
    stats = [{"tp": 0, "fp": 0, "fn": 0, "gt": 0} for _ in range(4)]
    for class_index, _ in ground:
        stats[class_index]["gt"] += 1
    matched = set()
    for class_index, conf, box in predictions:
        if conf < minimum_confidence:
            continue
        elig = [(idx, overlap(box, expected)) for idx, (key, expected) in enumerate(ground)
                if key == class_index and idx not in matched]
        if elig:
            idx, score = max(elig, key=lambda entry: entry[1])
            if score >= MATCH_IOU:
                matched.add(idx)
                stats[class_index]["tp"] += 1
                continue
        stats[class_index]["fp"] += 1
    for idx, (class_index, _) in enumerate(ground):
        if idx not in matched:
            stats[class_index]["fn"] += 1
    return stats


try:
    metadata = HfApi().model_info(REPOSITORY)
    revision = str(metadata.sha)
    if len(revision) != 40:
        raise ValueError(f"Unpinned model revision: {revision}")
    weight_path = Path(hf_hub_download(repo_id=REPOSITORY, filename=FILENAME, revision=revision))
    report.update({
        "source_commit": revision, "weight_sha256": sha256(weight_path),
        "weight_bytes": weight_path.stat().st_size,
    })
    if not 20_000_000 <= report["weight_bytes"] <= 100_000_000:
        raise ValueError("Unexpected OralGuard YOLOv8m checkpoint size")

    # PyTorch checkpoint may contain pickle; CI runner must have no persisted
    # GitHub credentials or secrets, and files are never shipped to cabinets.
    model = YOLO(str(weight_path), task="detect")
    index_map = inspect_model_classes(model.names)
    count = {f"{resolution}/{threshold}": [
        {"tp": 0, "fp": 0, "fn": 0, "gt": 0} for _ in range(4)
    ] for resolution in RESOLUTIONS for threshold in THRESHOLDS}
    durations = {str(resolution): [] for resolution in RESOLUTIONS}
    processed = 0
    for row in load_dataset("tirandazdylan/dentex-panoramic", "diagnosis", split="test", streaming=True):
        image = row["image"].convert("RGB")
        truth = ground_truth(row)
        for resolution in RESOLUTIONS:
            begin = time.perf_counter()
            prediction = model.predict(
                source=image, imgsz=resolution, conf=0.10, iou=0.50,
                device="cpu", verbose=False,
            )[0]
            durations[str(resolution)].append(time.perf_counter() - begin)
            found = sorted((
                (
                    index_map[int(cls)], float(conf),
                    [float(x) for x in xyxy]
                )
                for cls, conf, xyxy in zip(
                    prediction.boxes.cls.tolist(),
                    prediction.boxes.conf.tolist(),
                    prediction.boxes.xyxy.tolist(),
                )
            ), key=lambda x: x[1], reverse=True)
            for threshold in THRESHOLDS:
                inc = match(truth, found, threshold)
                for idx, row_stats in enumerate(inc):
                    for key, value in row_stats.items():
                        count[f"{resolution}/{threshold}"][idx][key] += value
        processed += 1
        if processed >= EXPECTED_CASES:
            break
    if processed != EXPECTED_CASES:
        raise RuntimeError(f"Expected 74 DENTEX images, found {processed}")
    result = {}
    for pair, per_class in count.items():
        detail = {}
        for name, row in zip(CLASS_NAMES, per_class):
            tp, fp, fn = row["tp"], row["fp"], row["fn"]
            detail[name] = {
                **row,
                "precision": tp / (tp + fp) if tp + fp else None,
                "recall": tp / (tp + fn) if tp + fn else None,
            }
        total = {k: sum(v[k] for v in per_class) for k in ["tp", "fp", "fn", "gt"]}
        detail["micro"] = {
            **total,
            "precision": total["tp"] / (total["tp"] + total["fp"]) if total["tp"] + total["fp"] else None,
            "recall": total["tp"] / (total["tp"] + total["fn"]) if total["tp"] + total["fn"] else None,
        }
        result[pair] = detail
    report.update({
        "status": "COMPLETED_EXPLORATORY",
        "images_evaluated": processed,
        "results": result,
        "cpu_latency_median_seconds": {
            key: round(statistics.median(series), 4) for key, series in durations.items()
        },
        "disclaimers": [
            "Public DENTEX diagnosis/test film split; no proof model's training images are independent",
            "Models compared by matched boxes on 74 films, not diagnostic accuracy or AP",
            "Very few periapical lesions: large confidence intervals",
            "No clinical approval, no commercial model/dataset rights clearance",
            "No deployment or inclusion in installation media",
        ],
    })
except Exception as exc:
    report.update({
        "status": "FAILED_TO_EVALUATE",
        "error": str(exc),
        "traceback_tail": traceback.format_exc()[-3200:],
    })
finally:
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
if report["status"] != "COMPLETED_EXPLORATORY":
    raise SystemExit(1)
