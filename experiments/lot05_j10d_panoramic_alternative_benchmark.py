#!/usr/bin/env python3
"""Research-only head-to-head alternative detection benchmark on the SAME 74 DENTEX films.

Commercial rights for the CC-BY-NC Liodon checkpoint are NOT granted.
No clinical decisions, no diagnosis, no patient images/weights in artifacts.
DENTEX may overlap the model's original training source. This benchmark is
exploratory and NOT external patient-independent model validation.
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
import time
import traceback
from pathlib import Path

import numpy as np
from datasets import load_dataset
from huggingface_hub import HfApi, hf_hub_download
from ultralytics import YOLO

MODEL_REPO = "liodon-ai/dental-panoramic-detector"
MODEL_FILENAME = "best.onnx"
OUTPUT = Path(os.getenv("LOT05_ALTERNATIVE_REPORT", "lot05-panoramic-alternative.json"))
MAX_CASES = 74
IOU_THRESHOLD = 0.50
PREDICT_IOU = 0.35
THRESHOLDS = (0.10, 0.25, 0.45)
# Public DENTEX diagnostic labels -> candidate's 3-class ontology:
# 0=Impacted -> 2, 1=Caries -> 0, 2=Periapical -> 1, 3=Deep caries -> 0.
CLASS_MAPPING = {0: 2, 1: 0, 2: 1, 3: 0}
CLASS_NAMES = ["caries(includes deep)", "periapical_lesion", "impacted_tooth"]
REPORT = {
    "mission": "LOT05/05.7-J10D",
    "stage": "experimental_alternative_comparison",
    "repo": MODEL_REPO,
    "license": "cc-by-nc-4.0 (commercial distribution NOT authorized)",
    "dataset": "tirandazdylan/dentex-panoramic",
    "split": "test",
    "max_images": MAX_CASES,
    "iou_matching": IOU_THRESHOLD,
    "predict_nms_iou": PREDICT_IOU,
    "thresholds": THRESHOLDS,
    "ontology": CLASS_MAPPING,
    "clinical_acceptance": False,
    "installable_certified": False,
    "no_patient_independent_guarantee": True,
    "status": "PENDING",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for buf in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()


def iou(a, b):
    iw = max(0., min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0., min(a[3], b[3]) - max(a[1], b[1]))
    intersection = iw * ih
    aa = max(0., a[2] - a[0]) * max(0., a[3] - a[1])
    bb = max(0., b[2] - b[0]) * max(0., b[3] - b[1])
    return intersection / max(aa + bb - intersection, 1e-9)


def gt_boxes(row):
    objects = row["objects"]
    if isinstance(objects, dict):
        boxes, labels = objects["bbox"], objects["diagnosis"]
    elif isinstance(objects, list):
        boxes = [v["bbox"] for v in objects]
        labels = [v["diagnosis"] for v in objects]
    else:
        raise ValueError(f"Unexpected DENTEX object format {type(objects)}")
    gt = []
    for box, label in zip(boxes, labels):
        label = int(label)
        if label not in CLASS_MAPPING:
            raise ValueError(f"Unexpected disease label: {label}")
        x, y, w, h = [float(z) for z in box]
        gt.append((CLASS_MAPPING[label], [x, y, x+w, y+h]))
    return gt


def calculate(gt, predictions, threshold):
    metrics = [{"tp": 0, "fp": 0, "fn": 0, "gt": 0} for _ in range(3)]
    for k, _ in gt:
        metrics[k]["gt"] += 1
    used = set()
    for pred_class, confidence, bbox in predictions:
        if confidence < threshold:
            continue
        eligible = [(idx, iou(bbox, box)) for idx, (k, box) in enumerate(gt)
                    if k == pred_class and idx not in used]
        if eligible:
            idx, overlap = max(eligible, key=lambda z: z[1])
            if overlap >= IOU_THRESHOLD:
                metrics[pred_class]["tp"] += 1
                used.add(idx)
                continue
        metrics[pred_class]["fp"] += 1
    for idx, (k, box) in enumerate(gt):
        if idx not in used:
            metrics[k]["fn"] += 1
    return metrics


try:
    repo_meta = HfApi().model_info(MODEL_REPO)
    model_commit = str(repo_meta.sha)
    if len(model_commit) != 40:
        raise RuntimeError("Expected immutable model commit SHA")
    model_path = Path(hf_hub_download(MODEL_REPO, MODEL_FILENAME, revision=model_commit))
    REPORT["source_commit"] = model_commit
    REPORT["onnx_sha256"] = sha256(model_path)
    REPORT["onnx_size"] = model_path.stat().st_size
    if not 8_000_000 <= REPORT["onnx_size"] <= 14_000_000:
        raise ValueError("Unexpected ONNX weight size")
    model = YOLO(str(model_path), task="detect")
    first = None
    runs = {str(t): [{"tp": 0, "fp": 0, "fn": 0, "gt": 0} for _ in range(3)] for t in THRESHOLDS}
    latency = []
    images = 0
    for row in load_dataset(
        "tirandazdylan/dentex-panoramic", "diagnosis", split="test", streaming=True
    ):
        image = row["image"]
        if not hasattr(image, "convert"):
            raise ValueError("DENTEX row has no decoded image")
        image = image.convert("RGB")
        gt = gt_boxes(row)
        start = time.perf_counter()
        result = model.predict(source=image, imgsz=640, conf=0.10, iou=PREDICT_IOU,
                               device="cpu", verbose=False)[0]
        latency.append(time.perf_counter() - start)
        if first is None:
            actual = [result.names[i] for i in sorted(result.names)]
            REPORT["model_classes"] = actual
            if actual != ["caries", "periapical_lesion", "impacted_tooth"]:
                raise ValueError("Unexpected class mapping: " + repr(actual))
            first = True
        boxes = result.boxes
        detections = sorted(
            ((int(k), float(p), [float(v) for v in xyxy])
             for k, p, xyxy in zip(boxes.cls.tolist(), boxes.conf.tolist(), boxes.xyxy.tolist())),
            key=lambda x: x[1], reverse=True,
        )
        for threshold in THRESHOLDS:
            counts = calculate(gt, detections, threshold)
            for j, item in enumerate(counts):
                for metric in item:
                    runs[str(threshold)][j][metric] += item[metric]
        images += 1
        if images >= MAX_CASES:
            break
    if images != MAX_CASES:
        raise RuntimeError(f"Wrong number of evaluation cases: {images}")
    table = {}
    for threshold, classes in runs.items():
        by_class = {}
        for name, item in zip(CLASS_NAMES, classes):
            tp, fp, fn = item["tp"], item["fp"], item["fn"]
            by_class[name] = {
                **item,
                "precision": tp/(tp+fp) if tp+fp else None,
                "recall": tp/(tp+fn) if tp+fn else None,
            }
        tp = sum(x["tp"] for x in classes)
        fp = sum(x["fp"] for x in classes)
        fn = sum(x["fn"] for x in classes)
        table[threshold] = {
            "per_class": by_class,
            "micro": {"tp": tp, "fp": fp, "fn": fn,
                      "precision": tp/(tp+fp) if tp+fp else None,
                      "recall": tp/(tp+fn) if tp+fn else None},
        }
    REPORT.update({
        "status": "COMPLETED_EXPLORATORY",
        "images": images,
        "mean_cpu_seconds": statistics.mean(latency),
        "median_cpu_seconds": statistics.median(latency),
        "comparison_to_noah_note": (
            "Noah baseline 4 separate classes, Liodon merges Deep Caries into Caries. "
            "Compare periapical and impacted directly only at the same IoU/confidence. "
            "This source test set could overlap one/both training sets."
        ),
        "results": table,
    })
except Exception as error:
    REPORT.update({"status": "FAILED_TO_EVALUATE", "error": str(error),
                   "traceback_tail": traceback.format_exc()[-3000:]})
finally:
    OUTPUT.write_text(json.dumps(REPORT, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(REPORT, indent=2, sort_keys=True))
if REPORT["status"] != "COMPLETED_EXPLORATORY":
    raise SystemExit(1)
