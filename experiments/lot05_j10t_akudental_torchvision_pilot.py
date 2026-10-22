#!/usr/bin/env python3
"""J10T: isolated, disposable academic AKUDENTAL pilot on CPU.

Never integrate into Digital Crown app, publish weights, store pixels or train
on clinic data. Provenance and commercial rights UNVERIFIED. Research smoke only.
Runs a small capped sample; reported metrics MUST NOT be used as clinical claims.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random

SEED = 20261022
NUM_CLASSES_WITH_BG = 36  # 32 FDI positions + 3 restorations + background
EXPECTED_SPLITS = {"train": 266, "val": 33, "test": 34}
SCHEMA = "digital-crown-lot05-j10t-akudental-fasterrcnn-cpu-smoke-v1"


def _ids(path: Path, split: str) -> list[str]:
    labels = path / "labels" / split
    images = path / "images" / split
    if not labels.is_dir() or not images.is_dir():
        raise ValueError("missing_split_directory")
    ids = sorted(p.stem for p in labels.glob("*.txt"))
    if len(ids) != EXPECTED_SPLITS[split] or len(set(ids)) != len(ids):
        raise ValueError("unexpected_partition_size")
    if any(not name.isdecimal() or not (images / (name + ".jpg")).is_file()
           for name in ids):
        raise ValueError("incomplete_source_image_linkage")
    return ids


def _choose(ids: list[str], limit: int) -> list[str]:
    rng = random.Random(SEED + len(ids))
    return sorted(rng.sample(ids, min(limit, len(ids))), key=int)


def _bbox_iou(a, b) -> float:
    xx1, yy1 = max(a[0], b[0]), max(a[1], b[1])
    xx2, yy2 = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(xx2 - xx1, 0) * max(yy2 - yy1, 0)
    size_a = max(a[2] - a[0], 0) * max(a[3] - a[1], 0)
    size_b = max(b[2] - b[0], 0) * max(b[3] - b[1], 0)
    union = size_a + size_b - intersection
    return intersection / union if union > 0 else 0.0


def _match(prediction: dict, target: dict, threshold: float = 0.5) -> tuple[int, int, int]:
    # Class-exact, greedy score-sorted IoU50 P/R. Not a COCO mAP calculation.
    import torch
    pb = prediction["boxes"].detach().cpu().tolist()
    pl = prediction["labels"].detach().cpu().tolist()
    ps = prediction["scores"].detach().cpu().tolist()
    gb = target["boxes"].detach().cpu().tolist()
    gl = target["labels"].detach().cpu().tolist()
    candidates = sorted((i for i, score in enumerate(ps) if score >= 0.25),
                        key=lambda i: -ps[i])
    matched: set[int] = set()
    tp = 0
    for i in candidates:
        best, best_iou = None, threshold
        for j, ground in enumerate(gb):
            if j in matched or pl[i] != gl[j]:
                continue
            overlap = _bbox_iou(pb[i], ground)
            if overlap >= best_iou:
                best, best_iou = j, overlap
        if best is not None:
            matched.add(best)
            tp += 1
    return tp, len(candidates) - tp, len(gb) - tp


def _read_item(workspace: Path, split: str, stem: str):
    import torch
    from PIL import Image
    from torchvision.transforms.functional import to_tensor
    # Byte reads occur only inside temporary research runner; no upload or logs.
    with Image.open(workspace / "images" / split / (stem + ".jpg")) as image:
        rgb = image.convert("RGB")
        w, h = rgb.size
        data = to_tensor(rgb)
    boxes, labels = [], []
    lines = (workspace / "labels" / split / (stem + ".txt")).read_text(encoding="utf-8")
    for row in lines.splitlines():
        if not row.strip():
            continue
        cls, cx, cy, bw, bh = row.split()
        label = int(cls)
        x, y, ww, hh = map(float, (cx, cy, bw, bh))
        xyxy = [(x - ww / 2) * w, (y - hh / 2) * h,
                (x + ww / 2) * w, (y + hh / 2) * h]
        xyxy[0] = max(0.0, xyxy[0])
        xyxy[1] = max(0.0, xyxy[1])
        xyxy[2] = min(float(w), xyxy[2])
        xyxy[3] = min(float(h), xyxy[3])
        if xyxy[2] <= xyxy[0] or xyxy[3] <= xyxy[1] or not 0 <= label < 35:
            raise ValueError("source_geometry_refused")
        boxes.append(xyxy)
        labels.append(label + 1)
    target = {"boxes": torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
              "labels": torch.tensor(labels, dtype=torch.int64)}
    return data, target


def run(workspace: Path, max_train: int, max_val: int) -> dict:
    import torch
    from torchvision.models.detection import (
        FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
        fasterrcnn_mobilenet_v3_large_320_fpn,
    )
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    torch.manual_seed(SEED)
    torch.set_num_threads(2)
    if torch.cuda.is_available():
        # GPU was NOT provisioned or paid for this smoke.
        raise ValueError("unexpected_gpu_environment")
    train_ids = _choose(_ids(workspace, "train"), max_train)
    val_ids = _choose(_ids(workspace, "val"), max_val)
    _ids(workspace, "test")  # enforce sealed untouched test split

    weights = FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT
    model = fasterrcnn_mobilenet_v3_large_320_fpn(
        weights=weights, min_size=320, max_size=640,
        rpn_pre_nms_top_n_train=300, rpn_post_nms_top_n_train=150,
        box_detections_per_img=100,
    )
    for param in model.parameters():
        param.requires_grad_(False)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, NUM_CLASSES_WITH_BG)
    # Only train the newly initialized detection head, not pretrained backbone.
    model.train()
    optimizer = torch.optim.AdamW(model.roi_heads.box_predictor.parameters(), lr=0.001)
    sum_loss = 0.0
    sample_count = 0
    for stem in train_ids:
        pixels, target = _read_item(workspace, "train", stem)
        optimizer.zero_grad(set_to_none=True)
        losses = model([pixels], [target])
        loss = sum(losses.values())
        if not torch.isfinite(loss):
            raise ValueError("non_finite_training_loss")
        loss.backward()
        optimizer.step()
        sum_loss += float(loss.detach())
        sample_count += 1
        del pixels, target, losses, loss

    model.eval()
    tp, fp, fn = 0, 0, 0
    with torch.inference_mode():
        for stem in val_ids:
            pixels, truth = _read_item(workspace, "val", stem)
            guess = model([pixels])[0]
            x, y, z = _match(guess, truth)
            tp += x
            fp += y
            fn += z
            del pixels, truth, guess
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "schema": SCHEMA,
        "status": "ACADEMIC_CPU_SMOKE_FINISHED_NOT_CLINICALLY_VALIDATED",
        "detector": "torchvision_fasterrcnn_mobilenet_v3_large_320_fpn",
        "pretraining": "generic_COCO_default",
        "class_count_including_background": NUM_CLASSES_WITH_BG,
        "train_images": sample_count,
        "validation_images": len(val_ids),
        "training_epochs": 1,
        "avg_training_loss": round(sum_loss / sample_count, 5),
        "validation_iou50_class_exact_score_025_precision": round(precision, 5),
        "validation_iou50_class_exact_score_025_recall": round(recall, 5),
        "validation_true_positive": tp,
        "validation_false_positive": fp,
        "validation_false_negative": fn,
        "test_images_touched": 0,
        "model_weights_exported": False,
        "images_or_predictions_uploaded": False,
        "clinical_accuracy_established": False,
        "commercial_rights_verified": False,
        "patient_level_independence_verified": False,
        "mAP_computed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--train-limit", type=int, default=24)
    parser.add_argument("--val-limit", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.train_limit <= 48 or not 1 <= args.val_limit <= 12:
        raise SystemExit("fixed_resource_caps_exceeded")
    if not args.workspace.is_dir():
        raise SystemExit("workspace_absent")
    try:
        report = run(args.workspace, args.train_limit, args.val_limit)
    except (ValueError, OSError, RuntimeError):
        # Do not leak paths, patient metadata or images via third-party exceptions.
        print(json.dumps({"schema": SCHEMA, "status": "TRAINING_SMOKE_FAIL_CLOSED"}))
        return 1
    print("RESEARCH_AGGREGATE_ONLY=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
