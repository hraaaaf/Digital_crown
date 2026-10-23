#!/usr/bin/env python3
"""J10Y: pre-registered validation-only resolution ablation (320 versus 640).

Academic AKUDENTAL CC BY-NC-SA research only; commercial rights not acquired.
Never use the repeatedly examined internal 34-image test set for tuning.
No patient- or case-level output, weights, images, or prediction artifacts.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

ROOT = Path(__file__).parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


T = _load("j10t_for_j10y", "lot05_j10t_akudental_torchvision_pilot.py")
V = _load("j10v_for_j10y", "lot05_j10v_akudental_fdi_holdout_eval.py")

SCHEMA = "digital-crown-j10y-predeclared-320-vs-640-val-only-v1"
FOCUS = ("31", "32", "41", "42", "24", "25", "23", "33")


def _small_report(docs: list[tuple[dict, dict]], *, resolution: int,
                  loss: float, train_images: int, val_images: int) -> dict:
    full = V._summary(docs, "validation")
    fdi = full["fdi32"]
    restorative = full["restorations3"]
    spatial = full["tooth_spatial_confusion"]
    matrix = spatial["matrix_32x32"]
    keys = spatial["labels_fdi"]
    focus = {}
    for tooth in FOCUS:
        row = matrix[keys.index(tooth)]
        item = fdi["class_metrics"][tooth]
        focus[tooth] = {
            "tp": item["tp"], "fp": item["fp"], "fn": item["fn"],
            "gt": item["tp"] + item["fn"],
            "spatial_localizations": sum(row),
            "correct_spatial_fdi": row[keys.index(tooth)],
            "ap50_truncated": item["ap50_truncated"],
        }
    return {
        "input_min_size": resolution, "input_max_size": resolution * 2,
        "train_images": train_images, "validation_images": val_images,
        "training_epochs": 3,
        "avg_training_loss": round(loss, 5),
        "fdi32": {
            k: fdi[k] for k in ("tp", "fp", "fn", "gt_instances", "precision",
                                "recall", "macro_ap50_101pt_truncated_predictions")
        },
        "restorations3": {
            k: restorative[k] for k in ("tp", "fp", "fn", "precision", "recall")
        },
        "spatially_localized_tooth_boxes": spatial["matched_tooth_locations_regardless_of_fdi"],
        "correct_spatial_fdi_numbers": spatial["correct_fdi_with_spatial_match"],
        "wrong_spatial_fdi_numbers": spatial["wrong_fdi_with_spatial_match"],
        "focus_teeth": focus,
    }


def fit_and_validate(workspace: Path, resolution: int,
                     train_ids: list[str], val_ids: list[str]) -> dict:
    import torch
    from torchvision.models.detection import (
        FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
        fasterrcnn_mobilenet_v3_large_320_fpn,
    )
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    if resolution not in (320, 640):
        raise ValueError("unregistered_resolution")
    # Reset all initializations identically. Same train split and fixed threshold.
    torch.manual_seed(T.SEED)
    model = fasterrcnn_mobilenet_v3_large_320_fpn(
        weights=FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT,
        min_size=resolution, max_size=2 * resolution,
        rpn_pre_nms_top_n_train=300, rpn_post_nms_top_n_train=150,
        box_detections_per_img=100,
    )
    for p in model.parameters():
        p.requires_grad_(False)
    hidden = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(hidden, T.NUM_CLASSES_WITH_BG)
    for module in (model.rpn.head, model.roi_heads.box_head, model.roi_heads.box_predictor):
        for p in module.parameters():
            p.requires_grad_(True)
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=0.0004, weight_decay=0.0001)
    loss_total = 0.0
    iterations = 0
    train_order = list(train_ids)
    for epoch in range(3):
        random.Random(T.SEED + epoch).shuffle(train_order)
        model.train()
        for image_id in train_order:
            pixels, truth = T._read_item(workspace, "train", image_id)
            optimizer.zero_grad(set_to_none=True)
            loss_parts = model([pixels], [truth])
            loss = sum(loss_parts.values())
            if not torch.isfinite(loss):
                raise ValueError("nonfinite_training_loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 10.0)
            optimizer.step()
            loss_total += float(loss.detach())
            iterations += 1
            del pixels, truth, loss_parts, loss
    model.eval()
    docs = []
    with torch.inference_mode():
        for image_id in val_ids:
            pixels, truth = T._read_item(workspace, "val", image_id)
            prediction = model([pixels])[0]
            docs.append((V._clean_prediction(prediction), V._clean_target(truth)))
            del pixels, truth, prediction
    report = _small_report(docs, resolution=resolution,
                           loss=loss_total/iterations,
                           train_images=len(train_ids), val_images=len(val_ids))
    del model, optimizer, docs
    return report


def run(workspace: Path) -> dict:
    import torch
    torch.set_num_threads(2)
    if torch.cuda.is_available():
        raise ValueError("unexpected_gpu")
    train = T._choose(T._ids(workspace, "train"), 96)
    val = T._choose(T._ids(workspace, "val"), 33)
    test_names = T._ids(workspace, "test")  # filenames only, no test image read
    if not set(train).isdisjoint(val) or not set(train).isdisjoint(test_names):
        raise ValueError("filename_split_overlap")
    result_320 = fit_and_validate(workspace, 320, train, val)
    result_640 = fit_and_validate(workspace, 640, train, val)
    return {
        "schema": SCHEMA,
        "status": "PAIRED_ACADEMIC_VALIDATION_ABLATION_ONLY",
        "protocol_fixed_before_run": True,
        "train_count": 96, "validation_count": 33,
        "train_epochs_each": 3,
        "comparisons": {"320": result_320, "640": result_640},
        "fdi_recall_delta_640_minus_320": round(
            result_640["fdi32"]["recall"] - result_320["fdi32"]["recall"], 5),
        "fdi_precision_delta_640_minus_320": round(
            result_640["fdi32"]["precision"] - result_320["fdi32"]["precision"], 5),
        "test_images_or_labels_used_for_selection": False,
        "test_filenames_checked_only": len(test_names),
        "test_set_previously_analyzed_in_J10V": True,
        "patient_independence_proven": False,
        "model_weights_exported": False,
        "commercial_rights_verified": False,
        "clinical_release_authorized": False,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.workspace)
    except (OSError, ValueError, RuntimeError):
        print(json.dumps({"schema": SCHEMA, "status": "FAIL_CLOSED"}))
        raise SystemExit(1)
    print("J10Y_AGGREGATE_VAL_ONLY="+json.dumps(report, sort_keys=True, separators=(",", ":")))
