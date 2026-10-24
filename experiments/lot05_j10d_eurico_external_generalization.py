#!/usr/bin/env python3
"""Research-only out-of-training-source DENTEX probe of OralXrays-9 YOLO26m.

Only two near-comparable categories are evaluated: Decay -> Caries/Deep Caries
combined, Apical Periodontitis -> Periapical Lesion. Wisdom Tooth is NOT
equivalent to Impacted Tooth. Never use as diagnostic or commercial evidence.
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

REPO = "EuricoGVP/YOLO26_Dental_Detection"
OUT = Path(os.environ.get("LOT05_EURICO_REPORT", "lot05-eurico-external-generalization.json"))
MAX_CASES = 74
THRESHOLDS = (0.10, 0.25, 0.348, 0.45)
IOU = 0.5
RESOLUTION = 1280
NORMALIZE = lambda s: "".join(c for c in str(s).lower() if c.isalnum())
TARGET_CLASSES = {"decay": "caries_and_deep_caries", "apicalperiodontitis": "periapical_lesion"}
GROUND_TRUTH_MAP = {1: "caries_and_deep_caries", 2: "periapical_lesion", 3: "caries_and_deep_caries"}
report = {
    "mission": "LOT05 / 05.7-J10D",
    "model": REPO,
    "source_training_data": "OralXrays-9 (NOT DENTEX)",
    "cross_source_test_dataset": "tirandazdylan/dentex-panoramic diagnosis/test",
    "model_license": "AGPL-3.0",
    "clinical_acceptance": False,
    "commercial_use_approved": False,
    "input_resolution": RESOLUTION,
    "input_categories_compared": ["Decay", "Apical Periodontitis"],
    "excluded_category": "Wisdom Tooth is not equivalent to DENTEX impacted teeth",
    "evaluation": "object-level one-to-one IoU>=0.50 at four confidence thresholds, NOT mAP50",
    "status": "PENDING",
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def gt(row):
    items = row["objects"]
    if isinstance(items, dict):
        boxes, labels = items["bbox"], items["diagnosis"]
    else:
        boxes = [item["bbox"] for item in items]
        labels = [item["diagnosis"] for item in items]
    truth = []
    for box, index in zip(boxes, labels):
        index = int(index)
        if index not in GROUND_TRUTH_MAP:
            continue
        x, y, w, h = map(float, box)
        truth.append((GROUND_TRUTH_MAP[index], [x, y, x + w, y + h]))
    return truth


def iou(b1, b2):
    w = max(0.0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
    h = max(0.0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
    inter = w * h
    a1 = max(0.0, b1[2] - b1[0]) * max(0.0, b1[3] - b1[1])
    a2 = max(0.0, b2[2] - b2[0]) * max(0.0, b2[3] - b2[1])
    return inter / max(a1 + a2 - inter, 1e-9)


def matched(gt_entries, detections, confidence):
    totals = {
        k: {"tp": 0, "fp": 0, "fn": 0, "gt": 0} for k in TARGET_CLASSES.values()
    }
    for category, _ in gt_entries:
        totals[category]["gt"] += 1
    taken = set()
    for cls, conf, box in detections:
        if conf < confidence:
            continue
        available = [(i, iou(box, expected)) for i, (label, expected) in enumerate(gt_entries)
                     if label == cls and i not in taken]
        if available:
            index, score = max(available, key=lambda z: z[1])
            if score >= IOU:
                totals[cls]["tp"] += 1
                taken.add(index)
                continue
        totals[cls]["fp"] += 1
    for i, (cls, _) in enumerate(gt_entries):
        if i not in taken:
            totals[cls]["fn"] += 1
    return totals


try:
    info = HfApi().model_info(REPO)
    source = str(info.sha)
    if len(source) != 40:
        raise ValueError("Refusing unpinned model revision")
    checkpoint = Path(hf_hub_download(REPO, "best.pt", revision=source))
    if not 25_000_000 < checkpoint.stat().st_size < 100_000_000:
        raise ValueError("Unexpected checkpoint size")
    model = YOLO(str(checkpoint), task="detect")
    names = {int(i): str(value) for i, value in model.names.items()}
    ids = {index: TARGET_CLASSES[NORMALIZE(label)]
           for index, label in names.items() if NORMALIZE(label) in TARGET_CLASSES}
    if set(ids.values()) != set(TARGET_CLASSES.values()):
        raise RuntimeError(f"Required OralXrays-9 pathology classes absent: {names}")
    report.update({
        "model_revision": source,
        "checkpoint_sha256": sha256(checkpoint),
        "checkpoint_bytes": checkpoint.stat().st_size,
        "all_source_classes": names,
        "compared_classes": ids,
    })
    scores = {
        str(t): {k: {"tp": 0, "fp": 0, "fn": 0, "gt": 0} for k in TARGET_CLASSES.values()}
        for t in THRESHOLDS
    }
    runtime = []
    processed = 0
    for row in load_dataset(
        "tirandazdylan/dentex-panoramic", "diagnosis", split="test", streaming=True
    ):
        image = row["image"].convert("RGB")
        truths = gt(row)
        begin = time.perf_counter()
        result = model.predict(
            image, imgsz=RESOLUTION, conf=min(THRESHOLDS), iou=0.5,
            device="cpu", verbose=False,
        )[0]
        runtime.append(time.perf_counter() - begin)
        detections = sorted(
            (
                (ids[int(cls)], float(conf), [float(v) for v in box])
                for cls, conf, box in zip(
                    result.boxes.cls.tolist(),
                    result.boxes.conf.tolist(),
                    result.boxes.xyxy.tolist(),
                )
                if int(cls) in ids
            ),
            key=lambda item: item[1], reverse=True,
        )
        for t in THRESHOLDS:
            res = matched(truths, detections, t)
            for cls, metrics in res.items():
                for key, value in metrics.items():
                    scores[str(t)][cls][key] += value
        processed += 1
        if processed >= MAX_CASES:
            break
    if processed != MAX_CASES:
        raise RuntimeError(f"Expected {MAX_CASES} DENTEX films, got {processed}")
    for threshold, classes in scores.items():
        for cls, metrics in classes.items():
            tp, fp, fn = metrics["tp"], metrics["fp"], metrics["fn"]
            metrics["precision"] = tp / (tp + fp) if tp + fp else None
            metrics["recall"] = tp / (tp + fn) if tp + fn else None
        totals = {
            key: sum(x[key] for x in classes.values()) for key in ["tp", "fp", "fn", "gt"]
        }
        classes["micro"] = {
            **totals,
            "precision": totals["tp"] / (totals["tp"] + totals["fp"]) if totals["tp"] + totals["fp"] else None,
            "recall": totals["tp"] / (totals["tp"] + totals["fn"]) if totals["tp"] + totals["fn"] else None,
        }
    report.update({
        "status": "COMPLETED_EXPLORATORY",
        "images_evaluated": processed,
        "results": scores,
        "cpu_median_seconds": statistics.median(runtime),
        "data_reuse_disclaimer": (
            "Different named training corpus than DENTEX; cannot prove no shared images "
            "or patient overlap and cannot infer clinical generalization from 74 films."
        ),
    })
except Exception as e:
    report.update({
        "status": "FAILED_TO_EVALUATE",
        "error": str(e),
        "traceback_tail": traceback.format_exc()[-3000:],
    })
finally:
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
if report["status"] != "COMPLETED_EXPLORATORY":
    raise SystemExit(1)
