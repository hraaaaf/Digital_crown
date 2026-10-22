#!/usr/bin/env python3
"""J10U: independent disposable research head/RPN fine-tuning on public AKUDENTAL.

Uses J10T parsing/matching helpers. No weights/model/data artifacts or clinical use.
Research only; no dataset commercial rights implied or asserted.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

base = Path(__file__).with_name("lot05_j10t_akudental_torchvision_pilot.py")
spec = importlib.util.spec_from_file_location("j10t_source", base)
assert spec and spec.loader
j10t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j10t)

SCHEMA = "digital-crown-lot05-j10u-adaptive-research-smoke-v1"


def _measure(model, workspace: Path, val_ids: list[str], score_min: float) -> dict:
    import torch

    model.eval()
    tp = fp = fn = raw_detections = 0
    with torch.inference_mode():
        for stem in val_ids:
            tensor, gt = j10t._read_item(workspace, "val", stem)
            result = model([tensor])[0]
            # Predictions below 0.05 are not retained by default detector pipeline.
            scores = result["scores"].detach().cpu().tolist()
            boxes = result["boxes"].detach().cpu().tolist()
            labels = result["labels"].detach().cpu().tolist()
            gtb = gt["boxes"].detach().cpu().tolist()
            gtl = gt["labels"].detach().cpu().tolist()
            ranked = sorted((i for i, s in enumerate(scores) if s >= score_min),
                            key=lambda i: -scores[i])
            raw_detections += len(ranked)
            used: set[int] = set()
            matches = 0
            for k in ranked:
                match_id = -1
                max_iou = 0.5
                for idx, truth in enumerate(gtb):
                    if idx in used or labels[k] != gtl[idx]:
                        continue
                    iou = j10t._bbox_iou(boxes[k], truth)
                    if iou >= max_iou:
                        max_iou = iou
                        match_id = idx
                if match_id >= 0:
                    matches += 1
                    used.add(match_id)
            tp += matches
            fp += len(ranked) - matches
            fn += len(gtb) - matches
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "predictions_above_threshold": raw_detections,
        "precision": round(tp / (tp + fp), 5) if tp + fp else 0.0,
        "recall": round(tp / (tp + fn), 5) if tp + fn else 0.0,
    }


def run(workspace: Path) -> dict:
    import torch
    from torchvision.models.detection import (
        FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
        fasterrcnn_mobilenet_v3_large_320_fpn,
    )
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    torch.manual_seed(j10t.SEED)
    torch.set_num_threads(2)
    if torch.cuda.is_available():
        raise ValueError("unapproved_gpu")
    train_ids = j10t._choose(j10t._ids(workspace, "train"), 96)
    val_ids = j10t._choose(j10t._ids(workspace, "val"), 33)
    j10t._ids(workspace, "test")  # verify only; no test image read.

    model = fasterrcnn_mobilenet_v3_large_320_fpn(
        weights=FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT,
        min_size=320, max_size=640,
        rpn_pre_nms_top_n_train=300,
        rpn_post_nms_top_n_train=150,
        box_detections_per_img=100,
    )
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    width = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(width, j10t.NUM_CLASSES_WITH_BG)
    for block in (model.rpn.head, model.roi_heads.box_head, model.roi_heads.box_predictor):
        for parameter in block.parameters():
            parameter.requires_grad_(True)

    before005 = _measure(model, workspace, val_ids, .05)
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=0.0004, weight_decay=0.0001)
    epochs, loss_total, step_count = 3, 0.0, 0
    for epoch in range(epochs):
        random.Random(j10t.SEED + epoch).shuffle(train_ids)
        model.train()
        for stem in train_ids:
            image, truth = j10t._read_item(workspace, "train", stem)
            optimizer.zero_grad(set_to_none=True)
            parts = model([image], [truth])
            loss = sum(parts.values())
            if not torch.isfinite(loss):
                raise ValueError("nonfinite_training_loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable, max_norm=10.0)
            optimizer.step()
            loss_total += float(loss.detach())
            step_count += 1
            del image, truth, parts, loss

    after005 = _measure(model, workspace, val_ids, .05)
    after025 = _measure(model, workspace, val_ids, .25)
    return {
        "schema": SCHEMA,
        "status": "RESEARCH_TRAINED_NOT_CLINICALLY_QUALIFIED",
        "source_dataset": "AKUDENTAL",
        "model": "torchvision_fasterrcnn_mobilenetv3_320_coCo_backbone_frozen",
        "train_unique_images": len(train_ids),
        "validation_unique_images": len(val_ids),
        "epochs": epochs,
        "train_image_presentations": step_count,
        "avg_loss": round(loss_total / step_count, 5),
        "before_at_score_005": before005,
        "after_at_score_005": after005,
        "after_at_score_025": after025,
        "metrics_are_class_exact_iou50_not_map": True,
        "test_images_read": 0,
        "dataset_commercial_license_verified": False,
        "clinical_performance_claim_allowed": False,
        "training_weights_persisted": False,
        "images_or_predictions_published": False,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        metrics = run(args.workspace)
    except (ValueError, OSError, RuntimeError):
        print(json.dumps({"schema": SCHEMA, "status": "RESEARCH_PILOT_FAILURE"}))
        raise SystemExit(1)
    print("RESEARCH_METRICS_ONLY=" + json.dumps(metrics, sort_keys=True))
