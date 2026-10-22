#!/usr/bin/env python3
"""J10V: one-time internal holdout evaluation of a DISPOSABLE academic FDI detector.

AKUDENTAL is CC BY-NC-SA 4.0 per publisher: no commercial license established.
Do not export images, patient IDs, prediction coordinates or model weights.
The publisher's 34-file test partition is not proven patient/source-independent.
This script does not provide clinical validation or product performance claims.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import random

P = Path(__file__).with_name("lot05_j10t_akudental_torchvision_pilot.py")
SPEC = importlib.util.spec_from_file_location("j10t_eval", P)
assert SPEC and SPEC.loader
j10t = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(j10t)

SCHEMA = "digital-crown-lot05-j10v-internal-fdi-evaluation-v1"
GROUPS = {"fdi32": range(1, 33), "restorations3": range(33, 36)}
FDI = tuple(f"{q}{i}" for q in (1, 2, 3, 4) for i in range(1, 9))


def _clean_prediction(raw: dict) -> dict:
    return {key: raw[key].detach().cpu().tolist() for key in ("boxes", "labels", "scores")}


def _clean_target(raw: dict) -> dict:
    return {key: raw[key].detach().cpu().tolist() for key in ("boxes", "labels")}


def _exact(docs: list[tuple[dict, dict]], class_ids: range, threshold: float = .25) -> dict:
    """Class-exact score-sorted greedy IoU50 detection; no image IDs in report."""
    classes = set(class_ids)
    tp = fp = fn = 0
    per = {c: [0, 0, 0] for c in class_ids}
    for pred, gt in docs:
        ranked = sorted((i for i, lab in enumerate(pred["labels"])
                         if lab in classes and pred["scores"][i] >= threshold),
                        key=lambda i: -pred["scores"][i])
        used = set()
        for idx in ranked:
            c = pred["labels"][idx]
            best, best_iou = None, .5
            for j, gt_c in enumerate(gt["labels"]):
                if j in used or gt_c != c:
                    continue
                iou = j10t._bbox_iou(pred["boxes"][idx], gt["boxes"][j])
                if iou >= best_iou:
                    best_iou, best = iou, j
            if best is None:
                fp += 1
                per[c][1] += 1
            else:
                used.add(best)
                tp += 1
                per[c][0] += 1
        for j, gt_c in enumerate(gt["labels"]):
            if gt_c in classes and j not in used:
                fn += 1
                per[gt_c][2] += 1
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(tp / (tp + fp), 5) if tp + fp else 0.0,
        "recall": round(tp / (tp + fn), 5) if tp + fn else 0.0,
        "per_class": per,
    }


def _ap50_per_class(docs: list[tuple[dict, dict]], class_ids: range) -> dict:
    """101-point interpolated per-class AP@IoU=.50 on available predictions.

    Predictions are truncated by the detector at score>=.05 and 100 boxes/image.
    Therefore this is an indicative *truncated* AP50, NOT official COCO mAP.
    """
    outputs = {}
    for cls in class_ids:
        targets_by_image = {}
        candidates = []
        for i, (pred, gt) in enumerate(docs):
            target_indices = [j for j, c in enumerate(gt["labels"]) if c == cls]
            targets_by_image[i] = target_indices
            for k, label in enumerate(pred["labels"]):
                if label == cls and pred["scores"][k] >= .05:
                    candidates.append((pred["scores"][k], i, pred["boxes"][k]))
        count = sum(len(v) for v in targets_by_image.values())
        if count == 0:
            outputs[cls] = None
            continue
        candidates.sort(key=lambda r: -r[0])
        claimed = defaultdict(set)
        tp = 0
        precisions = []
        recalls = []
        for _, i, box in candidates:
            ground = docs[i][1]
            best, best_iou = None, .5
            for j in targets_by_image[i]:
                if j in claimed[i]:
                    continue
                iou = j10t._bbox_iou(box, ground["boxes"][j])
                if iou >= best_iou:
                    best, best_iou = j, iou
            if best is not None:
                claimed[i].add(best)
                tp += 1
            precisions.append(tp / len(precisions + [0]))
            recalls.append(tp / count)
        ap = 0.0
        for n in range(101):
            required_recall = n / 100
            ap += max((p for p, r in zip(precisions, recalls)
                       if r >= required_recall), default=0.0) / 101
        outputs[cls] = round(ap, 5)
    return outputs


def _spatial_confusion(docs: list[tuple[dict, dict]], score_min: float = .25) -> dict:
    """Tooth-to-tooth 32x32 confusion conditioned on spatial IoU50 match.

    Rows: actual tooth. Columns: predicted tooth. Unlocalized teeth are
    tracked separately, not mislabeled as another FDI class.
    """
    matrix = [[0] * 32 for _ in range(32)]
    missed = Counter()
    extraneous_tooth_predictions = 0
    matched = 0
    for pred, gt in docs:
        chosen = sorted((i for i, c in enumerate(pred["labels"])
                         if 1 <= c <= 32 and pred["scores"][i] >= score_min),
                        key=lambda i: -pred["scores"][i])
        used = set()
        for i in chosen:
            best, best_iou = None, .5
            for j, cls in enumerate(gt["labels"]):
                if j in used or not 1 <= cls <= 32:
                    continue
                iou = j10t._bbox_iou(pred["boxes"][i], gt["boxes"][j])
                if iou >= best_iou:
                    best, best_iou = j, iou
            if best is None:
                extraneous_tooth_predictions += 1
            else:
                used.add(best)
                matched += 1
                matrix[gt["labels"][best] - 1][pred["labels"][i] - 1] += 1
        for j, cls in enumerate(gt["labels"]):
            if 1 <= cls <= 32 and j not in used:
                missed[cls] += 1
    offdiag = [
        {"truth_fdi": FDI[i], "pred_fdi": FDI[j], "n": n}
        for i, row in enumerate(matrix) for j, n in enumerate(row)
        if i != j and n
    ]
    offdiag.sort(key=lambda x: (-x["n"], x["truth_fdi"], x["pred_fdi"]))
    return {
        "matrix_32x32": matrix,
        "labels_fdi": list(FDI),
        "matched_tooth_locations_regardless_of_fdi": matched,
        "correct_fdi_with_spatial_match": sum(matrix[i][i] for i in range(32)),
        "wrong_fdi_with_spatial_match": sum(sum(row) - row[i] for i, row in enumerate(matrix)),
        "unlocalized_gt_teeth": sum(missed.values()),
        "unmatched_tooth_predictions": extraneous_tooth_predictions,
        "top_10_fdi_confusions": offdiag[:10],
        "unlocalized_by_fdi": {FDI[k - 1]: missed[k] for k in range(1, 33)},
    }


def _duplicates(workspace: Path) -> dict:
    """Aggregate nonclinical QA for duplicate tooth class labels in source."""
    result = {}
    for split in ("train", "val", "test"):
        files_with_duplicates = repeated_label_instances = 0
        duplicates_by_fdi = Counter()
        for text_path in sorted((workspace / "labels" / split).glob("*.txt")):
            counter = Counter()
            for row in text_path.read_text(encoding="utf-8").splitlines():
                if row.strip():
                    c = int(row.split()[0])
                    if c < 32:
                        counter[c] += 1
            extras = {c: n - 1 for c, n in counter.items() if n > 1}
            if extras:
                files_with_duplicates += 1
            repeated_label_instances += sum(extras.values())
            for c, n in extras.items():
                duplicates_by_fdi[FDI[c]] += n
        result[split] = {
            "files_flagged": files_with_duplicates,
            "extra_duplicate_fdi_instances": repeated_label_instances,
            "duplicates_by_fdi": dict(sorted(duplicates_by_fdi.items())),
        }
    return result


def _summary(docs: list[tuple[dict, dict]], subset: str) -> dict:
    result = {"images_evaluated": len(docs), "fixed_score_threshold": .25,
              "iou_threshold": .5}
    for name, classes in GROUPS.items():
        exact = _exact(docs, classes)
        per = exact.pop("per_class")
        aps = _ap50_per_class(docs, classes)
        valid_ap = [n for n in aps.values() if n is not None]
        result[name] = {
            **exact,
            "gt_instances": exact["tp"] + exact["fn"],
            "macro_ap50_101pt_truncated_predictions": round(sum(valid_ap) / len(valid_ap), 5)
            if valid_ap else None,
            "ap50_classes_with_gt": len(valid_ap),
            "class_metrics": {
                (FDI[cls - 1] if cls <= 32 else ("bridge", "filling_crown", "implant")[cls - 33]):
                {"tp": per[cls][0], "fp": per[cls][1], "fn": per[cls][2],
                 "ap50_truncated": aps[cls]}
                for cls in classes
            },
        }
    result["tooth_spatial_confusion"] = _spatial_confusion(docs)
    return result


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
        raise ValueError("unexpected_gpu")
    train_ids = j10t._choose(j10t._ids(workspace, "train"), 96)
    val_ids = j10t._choose(j10t._ids(workspace, "val"), 33)
    test_ids = j10t._ids(workspace, "test")
    if not set(train_ids).isdisjoint(val_ids) or not set(train_ids).isdisjoint(test_ids) or not set(val_ids).isdisjoint(test_ids):
        raise ValueError("filename_split_overlap")
    model = fasterrcnn_mobilenet_v3_large_320_fpn(
        weights=FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT,
        min_size=320, max_size=640, rpn_pre_nms_top_n_train=300,
        rpn_post_nms_top_n_train=150, box_detections_per_img=100)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    width = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(width, j10t.NUM_CLASSES_WITH_BG)
    for block in (model.rpn.head, model.roi_heads.box_head, model.roi_heads.box_predictor):
        for parameter in block.parameters():
            parameter.requires_grad_(True)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=.0004, weight_decay=.0001)
    for epoch in range(3):
        random.Random(j10t.SEED + epoch).shuffle(train_ids)
        model.train()
        for stem in train_ids:
            pixels, truth = j10t._read_item(workspace, "train", stem)
            optimizer.zero_grad(set_to_none=True)
            losses = model([pixels], [truth])
            loss = sum(losses.values())
            if not torch.isfinite(loss):
                raise ValueError("non_finite_training_loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], 10.0)
            optimizer.step()
            del pixels, truth, losses, loss

    def evaluate(split: str, ids: list[str]) -> list[tuple[dict, dict]]:
        docs = []
        model.eval()
        with torch.inference_mode():
            for stem in ids:
                pixels, truth = j10t._read_item(workspace, split, stem)
                prediction = model([pixels])[0]
                docs.append((_clean_prediction(prediction), _clean_target(truth)))
                del pixels, truth, prediction
        return docs

    # Hyperparameters are frozen before evaluating the test partition.
    val = evaluate("val", val_ids)
    test = evaluate("test", test_ids)
    report = {
        "schema": SCHEMA,
        "status": "INTERNAL_HOLDOUT_ACADEMIC_RESEARCH_ONLY",
        "source_dataset_revision": "92e2cc3ae5eebc9de509311a3edefb7106fca7dd",
        "train_samples": 96, "train_epochs": 3, "val_samples": 33,
        "test_samples": 34, "split_filename_disjoint": True,
        "patient_level_disjointness_verified": False,
        "validation": _summary(val, "val"),
        "internal_test": _summary(test, "test"),
        "duplicate_label_qa": _duplicates(workspace),
        "test_set_is_a_verified_independent_patient_cohort": False,
        "mAP_COCO_050_095_computed": False,
        "clinical_release_authorized": False,
        "commercial_training_rights_verified": False,
        "model_weights_saved": False,
        "image_pixels_saved_as_artifacts": False,
        "source_annotation_corrections_performed": False,
        "expert_review_of_duplicate_labels_performed": False,
    }
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.workspace)
    except (RuntimeError, ValueError, OSError):
        print(json.dumps({"schema": SCHEMA, "status": "EVALUATION_FAIL_CLOSED"}))
        return 1
    print("J10V_AGGREGATE_REPORT=" + json.dumps(report, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
