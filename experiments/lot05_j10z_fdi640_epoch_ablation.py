#!/usr/bin/env python3
"""J10Z: bounded 640px learning-duration ablation on validation ONLY.

Published third-party academic AKUDENTAL research; no rights for commercial
Digital Crown are asserted. Never reads test radiograph/label content. Test
partition previously analyzed in J10V MUST NOT be used for model selection.
No patient identifiers, images, model weights or predictions are persisted.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

BASE = Path(__file__).parent
def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, BASE / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

T = _load("j10t_for_j10z", "lot05_j10t_akudental_torchvision_pilot.py")
Y = _load("j10y_for_j10z", "lot05_j10y_akudental_resolution_ablation.py")
V = _load("j10v_for_j10z", "lot05_j10v_akudental_fdi_holdout_eval.py")

SCHEMA = "digital-crown-j10z-fdi640-three-vs-six-epoch-validation-only-v1"
CHECKPOINTS = (3, 6)
RESOLUTION = 640
TRAIN_N = 96
VALID_N = 33


def _compare(a: dict, b: dict) -> dict:
    """Research-only deltas; selected focal teeth don't replace aggregate metrics."""
    af, bf = a["fdi32"], b["fdi32"]
    return {
        "precision_6_minus_3": round(bf["precision"] - af["precision"], 5),
        "recall_6_minus_3": round(bf["recall"] - af["recall"], 5),
        "false_positives_6_minus_3": bf["fp"] - af["fp"],
        "true_positives_6_minus_3": bf["tp"] - af["tp"],
        "fdi31_tp_6_minus_3": b["focus_teeth"]["31"]["tp"] - a["focus_teeth"]["31"]["tp"],
        "fdi32_tp_6_minus_3": b["focus_teeth"]["32"]["tp"] - a["focus_teeth"]["32"]["tp"],
        "fdi24_tp_6_minus_3": b["focus_teeth"]["24"]["tp"] - a["focus_teeth"]["24"]["tp"],
    }


def run(workspace: Path) -> dict:
    import torch
    from torchvision.models.detection import (
        FasterRCNN_MobileNet_V3_Large_320_FPN_Weights,
        fasterrcnn_mobilenet_v3_large_320_fpn,
    )
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    torch.set_num_threads(2)
    if torch.cuda.is_available():
        raise ValueError("unapproved_gpu")
    train_ids = T._choose(T._ids(workspace, "train"), TRAIN_N)
    val_ids = T._choose(T._ids(workspace, "val"), VALID_N)
    test_ids = T._ids(workspace, "test")  # names only, never images/labels
    if not (set(train_ids).isdisjoint(val_ids) and
            set(train_ids).isdisjoint(test_ids) and
            set(val_ids).isdisjoint(test_ids)):
        raise ValueError("source_filename_split_not_disjoint")

    torch.manual_seed(T.SEED)
    model = fasterrcnn_mobilenet_v3_large_320_fpn(
        weights=FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT,
        min_size=RESOLUTION, max_size=2 * RESOLUTION,
        rpn_pre_nms_top_n_train=300, rpn_post_nms_top_n_train=150,
        box_detections_per_img=100)
    for p in model.parameters():
        p.requires_grad_(False)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(
        in_features, T.NUM_CLASSES_WITH_BG)
    for block in (model.rpn.head, model.roi_heads.box_head,
                  model.roi_heads.box_predictor):
        for p in block.parameters():
            p.requires_grad_(True)
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=.0004, weight_decay=.0001)

    order = list(train_ids)
    checkpoints = {}
    losses = []
    for epoch in range(1, CHECKPOINTS[-1] + 1):
        # Precisely matches the J10Y in-place shuffle policy for first 3 epochs.
        random.Random(T.SEED + epoch - 1).shuffle(order)
        model.train()
        epoch_loss = 0.
        for stem in order:
            pixels, target = T._read_item(workspace, "train", stem)
            optimizer.zero_grad(set_to_none=True)
            components = model([pixels], [target])
            loss = sum(components.values())
            if not torch.isfinite(loss):
                raise ValueError("non_finite_train_loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 10.)
            optimizer.step()
            epoch_loss += float(loss.detach())
            del pixels, target, components, loss
        losses.append(round(epoch_loss / TRAIN_N, 5))
        if epoch not in CHECKPOINTS:
            continue

        model.eval()
        docs = []
        with torch.inference_mode():
            for stem in val_ids:
                pixels, target = T._read_item(workspace, "val", stem)
                pred = model([pixels])[0]
                docs.append((V._clean_prediction(pred), V._clean_target(target)))
                del pixels, target, pred
        summary = Y._small_report(
            docs, resolution=RESOLUTION,
            loss=sum(losses)/len(losses),
            train_images=TRAIN_N, val_images=VALID_N)
        summary["training_epochs"] = epoch
        summary["avg_epoch_losses_to_checkpoint"] = list(losses)
        checkpoints[str(epoch)] = summary
        del docs
    return {
        "schema": SCHEMA,
        "status": "ACADEMIC_VALIDATION_ABLATION_COMPLETE_NONCLINICAL",
        "source_commit_required": "92e2cc3ae5eebc9de509311a3edefb7106fca7dd",
        "identical_model_weights_at_epoch3_to_j10y_not_asserted": True,
        "protocol_comparison_epochs": list(CHECKPOINTS),
        "only_training_duration_changed": True,
        "unique_train_images": TRAIN_N,
        "validation_images": VALID_N,
        "test_image_pixels_or_annotations_read": False,
        "test_filenames_verified_only": len(test_ids),
        "previous_internal_test_already_examined": True,
        "checkpoints": checkpoints,
        "delta": _compare(checkpoints["3"], checkpoints["6"]),
        "commercial_rights_verified": False,
        "clinical_release_authorized": False,
        "patient_independence_verified": False,
        "model_weights_saved": False,
        "radiographs_or_predictions_exported": False,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.workspace)
    except (OSError, ValueError, RuntimeError):
        print(json.dumps({"schema": SCHEMA, "status": "FAIL_CLOSED"}))
        return 1
    print("J10Z_AGGREGATE_VALIDATION_ONLY="+json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
