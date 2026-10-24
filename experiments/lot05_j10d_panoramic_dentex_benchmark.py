#!/usr/bin/env python3
"""Exploratory per-class DENTEX pathology evaluation on public panoramic X-rays.

Research only: dataset is a reformatted public training-source split; it may
overlap the candidate's original training set and cannot substantiate external
or patient-independent clinical generalization. Never publish actual images.
"""
from __future__ import annotations

import json
import os
import statistics
import time
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np
from datasets import load_dataset
from ultralytics import YOLO

MODEL_PATH = Path(os.environ.get("GITHUB_WORKSPACE", ".")) / ".lot05-panoramic-probe" / "noah_dentex_4class.pt"
OUTPUT = Path(os.environ.get("LOT05_DENTEX_REPORT", "lot05-dentex-exploratory.json"))
# Dataset: 0 impacted, 1 caries, 2 periapical lesion, 3 deep caries
# Model : 0 caries, 1 deep caries, 2 impacted, 3 periapical lesion
GROUND_TRUTH_TO_MODEL = {0: 2, 1: 0, 2: 3, 3: 1}
NAMES = ["Caries", "Deep Caries", "Impacted", "Periapical Lesion"]
CONFIDENCE = 0.25
IOU_THRESHOLD = 0.50
MAX_CASES = 74
report = {
    "mission": "LOT05 / 05.7-J10D",
    "dataset": "tirandazdylan/dentex-panoramic",
    "config": "diagnosis",
    "split": "test",
    "model_source": "NoahOksuz/DentalXrayAI a44a456cb76071f1776a7636204e8c48748a696d",
    "evaluation": "exploratory-no-independent-patient-overlap-guarantee",
    "model_threshold": CONFIDENCE,
    "match_iou": IOU_THRESHOLD,
    "model_input": 1280,
    "clinical_acceptance": False,
    "status": "PENDING",
}


def iou(a, b):
    inter_w = max(0., min(a[2], b[2]) - max(a[0], b[0]))
    inter_h = max(0., min(a[3], b[3]) - max(a[1], b[1]))
    inter = inter_w * inter_h
    area_a = max(0., a[2] - a[0]) * max(0., a[3] - a[1])
    area_b = max(0., b[2] - b[0]) * max(0., b[3] - b[1])
    return inter / max(area_a + area_b - inter, 1e-8)


def ground_truth(row):
    obj = row["objects"]
    if isinstance(obj, dict):
        rectangles = obj["bbox"]
        labels = obj["diagnosis"]
    elif isinstance(obj, list):
        rectangles = [x["bbox"] for x in obj]
        labels = [x["diagnosis"] for x in obj]
    else:
        raise ValueError(f"Unexpected object schema: {type(obj)}")
    ground = []
    for box, label in zip(rectangles, labels):
        k = int(label)
        if k not in GROUND_TRUTH_TO_MODEL:
            raise ValueError(f"Unexpected diagnosis class {k}")
        x, y, width, height = [float(z) for z in box]
        ground.append((GROUND_TRUTH_TO_MODEL[k], [x, y, x + width, y + height]))
    return ground


try:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Pinned smoke model missing: {MODEL_PATH}")
    model = YOLO(str(MODEL_PATH), task="detect")
    actual_names = [model.names[i] for i in sorted(model.names)]
    if actual_names != NAMES:
        raise RuntimeError(f"Model class mismatch: {actual_names}")

    data = load_dataset("tirandazdylan/dentex-panoramic", "diagnosis", split="test", streaming=True)
    totals = {i: {"tp": 0, "fp": 0, "fn": 0, "ground_truth": 0} for i in range(len(NAMES))}
    runtimes = []
    processed = 0
    for row in data:
        image = row["image"]
        if hasattr(image, "convert"):
            image = image.convert("RGB")
        else:
            raise ValueError(f"Image did not decode into PIL: {type(image)}")
        truth = ground_truth(row)
        for k, _ in truth:
            totals[k]["ground_truth"] += 1
        started = time.perf_counter()
        results = model.predict(source=image, imgsz=1280, conf=CONFIDENCE, iou=0.5, device="cpu", verbose=False)
        runtimes.append(time.perf_counter() - started)
        pred_boxes = results[0].boxes
        detections = sorted(
            (
                (int(cls), float(conf), [float(v) for v in box])
                for cls, conf, box in zip(pred_boxes.cls.tolist(), pred_boxes.conf.tolist(), pred_boxes.xyxy.tolist())
            ),
            key=lambda pred: pred[1],
            reverse=True,
        )
        used = set()
        for pred_cls, confidence, box in detections:
            matches = [(j, iou(box, target)) for j, (gt_cls, target) in enumerate(truth)
                       if gt_cls == pred_cls and j not in used]
            if matches:
                match_idx, overlap = max(matches, key=lambda pair: pair[1])
                if overlap >= IOU_THRESHOLD:
                    totals[pred_cls]["tp"] += 1
                    used.add(match_idx)
                    continue
            totals[pred_cls]["fp"] += 1
        for index, (gt_cls, _) in enumerate(truth):
            if index not in used:
                totals[gt_cls]["fn"] += 1
        processed += 1
        if processed >= MAX_CASES:
            break

    if processed < 10:
        raise RuntimeError("Not enough public annotated cases in split")
    per_class = {}
    for i, name in enumerate(NAMES):
        m = totals[i]
        precision = m["tp"] / (m["tp"] + m["fp"]) if m["tp"] + m["fp"] else None
        recall = m["tp"] / (m["tp"] + m["fn"]) if m["tp"] + m["fn"] else None
        per_class[name] = {**m, "precision_at_025_iou_050": precision, "recall_at_025_iou_050": recall}
    report.update({
        "status": "COMPLETED_EXPLORATORY",
        "images": processed,
        "classes": per_class,
        "mean_cpu_seconds": round(statistics.mean(runtimes), 4),
        "median_cpu_seconds": round(statistics.median(runtimes), 4),
        "total_gt": sum(x["ground_truth"] for x in totals.values()),
        "total_predictions": sum(x["tp"] + x["fp"] for x in totals.values()),
        "limitations": [
            "DENTEX reformatted source split; candidate was trained on DENTEX and original train/test overlap is unknown",
            "Dataset official license statements conflict; for research-only evaluation, not redistribution",
            "Per-class precision/recall at one confidence and IoU, NOT average precision or diagnostic sensitivity in clinic",
            "No patient-independent data, external center, calibration or clinician review",
            "No production deployment and no automatic diagnostic recommendation",
        ],
    })
except Exception as error:
    report["status"] = "FAILED_TO_EVALUATE"
    report["error"] = str(error)
    report["traceback_tail"] = traceback.format_exc()[-2800:]
finally:
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
if report["status"] != "COMPLETED_EXPLORATORY":
    raise SystemExit(1)
