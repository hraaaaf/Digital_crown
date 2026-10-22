#!/usr/bin/env python3
"""LOT05 / 05.7-J10D. Local-only FDI tooth numbering evaluation.

Two modes:
  * --predictions FILE: measure synthetic or existing offline prediction manifests
  * --checkpoint FILE --authorized-local-evaluation: infer authorized local films

NEVER uploads an image. The JSON report has aggregates only, not case IDs, pixels,
paths or model outputs. Dataset independence cannot be proved from this runner.
No clinical approval or release gate is inferred from benchmark performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from lot05_j10d_fdi_tooth_model_probe import (
    CLASS_ORDER, MODEL_WEIGHTS_SHA256, verify_names,
)

VALID_FDI = frozenset(CLASS_ORDER)
MIN_SUBGROUP_IMAGES = 5


class BenchmarkError(ValueError):
    pass


def _bbox(obj, height: int, width: int):
    bbox = obj.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        raise BenchmarkError("invalid_bbox")
    if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in bbox):
        raise BenchmarkError("nonfinite_bbox")
    x1, y1, x2, y2 = map(float, bbox)
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise BenchmarkError("out_of_frame_bbox")
    return (x1, y1, x2, y2)


def _fdi(obj):
    label = obj.get("fdi")
    if not isinstance(label, str) or label not in VALID_FDI:
        raise BenchmarkError("invalid_fdi_label")
    return label


def _iou(a, b):
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = w * h
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    return inter / max(1e-12, area_a + area_b - inter)


def _case_metrics(truth, guesses, *, height, width, iou_threshold):
    if not isinstance(truth, list) or not isinstance(guesses, list):
        raise BenchmarkError("invalid_case_labels")
    if len(truth) > 52 or len(guesses) > 300:
        raise BenchmarkError("unreasonable_annotations")
    gt = [(_fdi(v), _bbox(v, height, width)) for v in truth]
    pr = []
    for v in guesses:
        label, bbox = _fdi(v), _bbox(v, height, width)
        conf = v.get("confidence")
        if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not math.isfinite(conf) or not 0 <= conf <= 1:
            raise BenchmarkError("invalid_prediction_confidence")
        pr.append((label, bbox, float(conf)))

    pairs = []
    for gi, (_, gb) in enumerate(gt):
        for pi, (_, pb, _) in enumerate(pr):
            iou = _iou(gb, pb)
            if iou >= iou_threshold:
                # Localize FIRST regardless of FDI; then classify matched pairs.
                pairs.append((-iou, gi, pi))
    pairs.sort()
    used_gt, used_pr = set(), set()
    matched = []
    for _, gi, pi in pairs:
        if gi in used_gt or pi in used_pr:
            continue
        used_gt.add(gi)
        used_pr.add(pi)
        matched.append((gi, pi))
    correct = sum(gt[gi][0] == pr[pi][0] for gi, pi in matched)
    wrong = [(gt[gi][0], pr[pi][0]) for gi, pi in matched if gt[gi][0] != pr[pi][0]]
    neighbor = sum(a[0] == b[0] and abs(int(a[1]) - int(b[1])) == 1 for a, b in wrong)
    dup = sum(v > 1 for v in Counter(p[0] for p in pr).values())
    return {
        "gt": len(gt), "predicted": len(pr), "localized": len(matched),
        "correct_fdi": correct, "wrong_fdi": len(wrong),
        "neighbor_swaps": neighbor, "other_swaps": len(wrong) - neighbor,
        "missed_teeth": len(gt) - len(matched),
        "unmatched_predictions": len(pr) - len(matched),
        "duplicate_fdi_labels": dup,
        "fully_correct_film": int(len(gt) == len(pr) == correct and dup == 0),
        "film_has_fdi_error": int(correct != len(gt) or len(pr) != len(gt) or dup > 0),
    }


def _ratio(num, den):
    return round(num / den, 6) if den else None


def _aggregate(rows):
    s = Counter()
    for r in rows:
        s.update(r)
    n = len(rows)
    return {
        "films": n,
        "ground_truth_teeth": s["gt"],
        "predicted_boxes": s["predicted"],
        "correct_localization_count": s["localized"],
        "correct_number_and_localization_count": s["correct_fdi"],
        "wrong_number_on_localized_tooth": s["wrong_fdi"],
        "adjacent_fdi_swaps": s["neighbor_swaps"],
        "other_fdi_swaps": s["other_swaps"],
        "missed_teeth": s["missed_teeth"],
        "unmatched_proposals": s["unmatched_predictions"],
        "duplicate_fdi_labels": s["duplicate_fdi_labels"],
        "films_with_any_error": s["film_has_fdi_error"],
        "fully_correct_films": s["fully_correct_film"],
        "localization_recall": _ratio(s["localized"], s["gt"]),
        "fdi_correct_recall": _ratio(s["correct_fdi"], s["gt"]),
        "fdi_accuracy_given_localized": _ratio(s["correct_fdi"], s["localized"]),
        "proposal_precision_correct_fdi": _ratio(s["correct_fdi"], s["predicted"]),
        "exact_film_fraction": _ratio(s["fully_correct_film"], n),
        "mean_false_proposals_per_film": _ratio(s["unmatched_predictions"], n),
    }


def _bootstrap(rows, n=250, seed=20261022):
    if not rows:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        picked = [rows[rng.randrange(len(rows))] for _ in rows]
        recall = _aggregate(picked)["fdi_correct_recall"]
        if recall is not None:
            vals.append(recall)
    if not vals:
        return None
    vals.sort()
    return [vals[int((len(vals) - 1) * .025)], vals[int((len(vals) - 1) * .975)]]


def _get_manifest(file: Path):
    obj = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("schema") != "digital-crown-fdi-eval-v1":
        raise BenchmarkError("wrong_manifest_schema")
    cases = obj.get("cases")
    if not isinstance(cases, list) or not cases or len(cases) > 10000:
        raise BenchmarkError("invalid_case_count")
    opaque_ids = []
    for case in cases:
        if not isinstance(case, dict):
            raise BenchmarkError("invalid_case")
        ref = case.get("case_id")
        if not isinstance(ref, str) or not ref or len(ref) > 128:
            raise BenchmarkError("invalid_case_id")
        opaque_ids.append(ref)
        if case.get("dentition") not in {"permanent", "mixed", "primary", "unknown"}:
            raise BenchmarkError("invalid_dentition")
        if not isinstance(case.get("height"), int) or not isinstance(case.get("width"), int) or min(case["height"], case["width"]) <= 0:
            raise BenchmarkError("invalid_image_dimensions")
        for key in ("site_group", "device_group"):
            group = case.get(key)
            if group is not None and (isinstance(group, bool) or not isinstance(group, int) or not 1 <= group <= 50):
                raise BenchmarkError("invalid_anonymous_group")
    if len(set(opaque_ids)) != len(opaque_ids):
        raise BenchmarkError("duplicate_case_ids")
    return cases


def _read_predictions(file: Path, case_ids):
    obj = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("schema") != "digital-crown-fdi-predictions-v1":
        raise BenchmarkError("wrong_predictions_schema")
    pred = obj.get("predictions")
    if not isinstance(pred, dict) or set(pred) != case_ids:
        raise BenchmarkError("missing_or_extra_prediction_cases")
    return pred


def _trusted_image_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise BenchmarkError("image_path_must_be_relative")
    candidate = root / relative
    actual = candidate.resolve(strict=True)
    if not actual.is_relative_to(root.resolve(strict=True)) or not actual.is_file() or actual.is_symlink():
        raise BenchmarkError("untrusted_image_path")
    if actual.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
        raise BenchmarkError("invalid_image_type")
    return actual


def _run_local_model(cases, root: Path, checkpoint: Path, conf=0.25):
    import cv2
    from ultralytics import YOLO
    expected_hash = MODEL_WEIGHTS_SHA256
    if not checkpoint.is_file() or checkpoint.is_symlink():
        raise BenchmarkError("checkpoint_missing")
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    if digest != expected_hash:
        raise BenchmarkError("checkpoint_sha256_mismatch")
    model = YOLO(str(checkpoint), task="detect")
    verify_names(model.names)
    output = {}
    for case in cases:
        # This is intentionally local, explicit and never called in public CI.
        source = _trusted_image_path(root, case.get("image"))
        bgr = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if bgr is None or bgr.shape[:2] != (case["height"], case["width"]):
            raise BenchmarkError("invalid_local_image_or_metadata")
        res = model.predict(source=bgr, imgsz=1024, conf=conf, iou=0.50, device="cpu", verbose=False)[0]
        classes = res.boxes.cls.cpu().numpy().tolist()
        boxes = res.boxes.xyxy.cpu().numpy().tolist()
        confidence = res.boxes.conf.cpu().numpy().tolist()
        output[case["case_id"]] = [
            {"fdi": CLASS_ORDER[int(cls)], "bbox": [float(x) for x in box], "confidence": float(score)}
            for cls, box, score in zip(classes, boxes, confidence)
        ]
    return output


def evaluate(cases, predictions, iou_threshold=0.5, *, independence_audited=False):
    if not 0 < iou_threshold <= 1:
        raise BenchmarkError("invalid_iou_threshold")
    rows = []
    strata = defaultdict(list)
    site_rows = defaultdict(list)
    device_rows = defaultdict(list)
    for case in cases:
        row = _case_metrics(case.get("gt"), predictions[case["case_id"]],
            height=case["height"], width=case["width"], iou_threshold=iou_threshold)
        rows.append(row)
        strata[case["dentition"]].append(row)
        if case.get("site_group") is not None:
            site_rows[case["site_group"]].append(row)
        if case.get("device_group") is not None:
            device_rows[case["device_group"]].append(row)
    def safe_groups(mapping, expected_total):
        if sum(len(group) for group in mapping.values()) != expected_total:
            return {"status": "NOT_PROVIDED_FOR_ALL_FILMS"}
        return {f"group_{k}": _aggregate(v) if len(v) >= MIN_SUBGROUP_IMAGES
            else {"films": len(v), "status": "SUPPRESSED_SMALL_SUBGROUP"}
            for k, v in sorted(mapping.items())}
    result = {
        "mode": "OFFLINE_EVALUATION_RESEARCH_ONLY",
        "clinical_approval": False,
        "generalization_validated": False,
        "independence_audited": bool(independence_audited),
        "independence_proven_by_runner": False,
        "iou_threshold": iou_threshold,
        "overall": _aggregate(rows),
        "bootstrap_95_percent_ci_fdi_recall_by_film": _bootstrap(rows),
        "by_dentition": {
            k: _aggregate(v) if len(v) >= MIN_SUBGROUP_IMAGES
            else {"films": len(v), "status": "SUPPRESSED_SMALL_SUBGROUP"}
            for k, v in sorted(strata.items())
        },
        "by_site_group": safe_groups(site_rows, len(rows)),
        "by_device_group": safe_groups(device_rows, len(rows)),
        "patient_data_logged": False,
        "report_contains_images_or_case_ids": False,
        "note": "Localization IoU >= threshold; FDI errors scored separately. Bootstrap samples films, not individual teeth. Human review and independent split audit still required.",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Offline panoramic FDI numbering evaluation; aggregate JSON only")
    parser.add_argument("--manifest", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--predictions", type=Path, help="Precomputed local or synthetic JSON")
    mode.add_argument("--checkpoint", type=Path, help="Pinned local best.pt; patient films never go to GitHub CI")
    parser.add_argument("--images-root", type=Path)
    parser.add_argument("--authorized-local-evaluation", action="store_true")
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    cases = _get_manifest(args.manifest)
    if args.checkpoint:
        if not args.authorized_local_evaluation or args.images_root is None:
            raise BenchmarkError("local_image_access_requires_explicit_authorization_and_root")
        if not 0 < args.confidence < 1:
            raise BenchmarkError("invalid_model_confidence")
        predictions = _run_local_model(cases, args.images_root, args.checkpoint, args.confidence)
    else:
        predictions = _read_predictions(args.predictions, {c["case_id"] for c in cases})
    # User confirmation does NOT establish train/test independence. Always false.
    report = evaluate(cases, predictions, args.iou, independence_audited=False)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "AGGREGATE_REPORT_WRITTEN",
        "films": report["overall"]["films"],
        "clinical_approval": False,
        "generalization_validated": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
