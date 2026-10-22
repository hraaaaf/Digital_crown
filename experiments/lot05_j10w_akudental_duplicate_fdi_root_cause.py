#!/usr/bin/env python3
"""J10W: privacy-minimal research triage of public AKUDENTAL FDI labels.

Runs on a pinned source's YOLO text only; never opens image pixels or LabelMe
JSON, retains no per-image identifiers in ordinary CI output, never changes
annotation truth, and never claims clinical or commercial authorization.

Optionally emits a review manifest to an OWNER-APPROVED LOCAL PRIVATE path,
not for GitHub Actions, Notion, logs, or public artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import statistics

MODULE = Path(__file__).with_name("lot05_j10q_akudental_fdi_yolo_text_only.py")
SPEC = importlib.util.spec_from_file_location("j10q_for_j10w", MODULE)
assert SPEC and SPEC.loader
J10Q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(J10Q)

SCHEMA = "digital-crown-lot05-j10w-akudental-anomaly-triage-v1"
SPLITS = {"train": 266, "val": 33, "test": 34}
FOCUS_FDI = ("11", "12", "21", "22", "31", "32", "33", "41", "42", "43", "24", "25")
FDA = J10Q.FDI


class TriageError(ValueError):
    pass


def _reject(reason: str) -> None:
    raise TriageError(reason)


def _box(rec: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    cx, cy, w, h = rec
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2


def _iou(first, second) -> float:
    a, b = _box(first), _box(second)
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - w * h
    return (w * h / union) if union else 0.0


def _percentile_median(values: list[float]) -> float | None:
    return round(statistics.median(values), 7) if values else None


def _rows(text: str) -> list[tuple[int, tuple[float, float, float, float]]]:
    # Reuse full five-column COCO/YOLO semantic and bound checking J10Q.
    J10Q.audit_label_text(text)
    result = []
    for line in text.splitlines():
        if line.strip():
            parts = line.strip().split()
            result.append((int(parts[0]), tuple(float(v) for v in parts[1:])))
    return result


def audit_labels(label_root: Path, *, private_manifest: Path | None = None) -> dict:
    if private_manifest is not None and private_manifest.exists():
        _reject("private_manifest_output_must_not_exist")
    if label_root.is_symlink() or not label_root.is_dir():
        _reject("invalid_source_label_root")
    result = {
        "schema": SCHEMA,
        "status": "ACADEMIC_ANNOTATION_TRIAGE_NOT_CLINICAL_REVIEW",
        "source_labels_examined": 0,
        "split": {},
        "per_fdi": {},
        "duplicate_qa": {
            "images_flagged_total": 0,
            "extra_same_fdi_records_total": 0,
            "pairs_examined": 0,
            "pairs_iou_gt_070": 0,
            "pairs_iou_030_to_070": 0,
            "pairs_iou_lt_030": 0,
            "different_location_pairs_by_iou_only_unproven": True,
        },
        "source_modified": False,
        "images_read": False,
        "patients_identified": False,
        "expert_visual_review_performed": False,
        "source_rights_commercial_verified": False,
        "patient_independent_split_proven": False,
        "clinical_release_authorized": False,
    }
    selected = {fdi: {"area": [], "w": [], "h": [], "center_x": [],
                      "center_y": [], "count": 0, "images_present": 0}
                for fdi in FOCUS_FDI}
    review_manifest = []
    every_id: set[str] = set()
    counts = {split: Counter() for split in SPLITS}
    flagged_by_split = Counter()
    extra_by_split = Counter()
    repeated_fdi = Counter()
    duplicate_pair_iou = []
    image_class_counts = {split: defaultdict(int) for split in SPLITS}
    for split, expected in SPLITS.items():
        folder = label_root / split
        if folder.is_symlink() or not folder.is_dir():
            _reject("source_split_missing")
        files = sorted(folder.glob("*.txt"))
        if len(files) != expected:
            _reject("source_split_file_count_mismatch")
        for label_file in files:
            if not label_file.stem.isdecimal() or label_file.is_symlink():
                _reject("untrusted_source_label_file")
            if label_file.stem in every_id:
                _reject("split_identity_overlap")
            every_id.add(label_file.stem)
            if not 0 < label_file.stat().st_size <= J10Q.MAX_LABEL_BYTES:
                _reject("empty_or_oversized_label")
            try:
                labels = _rows(label_file.read_text(encoding="utf-8"))
            except (UnicodeError, OSError):
                _reject("invalid_annotation_file")
            result["source_labels_examined"] += 1
            by_class = defaultdict(list)
            for cls, box in labels:
                if cls < 32:
                    counts[split][FDA[cls]] += 1
                    by_class[cls].append(box)
            for cls, boxes in by_class.items():
                fdi = FDA[cls]
                image_class_counts[split][fdi] += 1
                if fdi in selected:
                    agg = selected[fdi]
                    for cx, cy, w, h in boxes:
                        agg["area"].append(w * h)
                        agg["w"].append(w)
                        agg["h"].append(h)
                        agg["center_x"].append(cx)
                        agg["center_y"].append(cy)
                        agg["count"] += 1
                    agg["images_present"] += 1
            collisions = {FDA[cls]: len(boxes) for cls, boxes in by_class.items()
                          if len(boxes) > 1}
            if collisions:
                flagged_by_split[split] += 1
                extras = sum(n - 1 for n in collisions.values())
                extra_by_split[split] += extras
                result["duplicate_qa"]["images_flagged_total"] += 1
                result["duplicate_qa"]["extra_same_fdi_records_total"] += extras
                # Pairwise IoU is a triage signal, not a clinical adjudication.
                for cls, boxes in by_class.items():
                    if len(boxes) > 1:
                        repeated_fdi[FDA[cls]] += len(boxes) - 1
                        for i in range(len(boxes)):
                            for j in range(i + 1, len(boxes)):
                                duplicate_pair_iou.append(_iou(boxes[i], boxes[j]))
                if private_manifest is not None:
                    review_manifest.append({
                        "split": split, "source_image_basename": label_file.stem,
                        "duplicate_fdi_labels_with_counts": collisions,
                        "review_status": "NOT_CLINICALLY_REVIEWED",
                    })
        result["split"][split] = {
            "images": expected,
            "teeth_total": sum(counts[split].values()),
            "flagged_images": flagged_by_split[split],
            "extra_same_fdi_records": extra_by_split[split],
            "fdi31_annotated_images": image_class_counts[split]["31"],
            "fdi32_annotated_images": image_class_counts[split]["32"],
            "fdi24_annotated_images": image_class_counts[split]["24"],
            "fdi25_annotated_images": image_class_counts[split]["25"],
        }

    if len(every_id) != 333:
        _reject("incomplete_unique_image_ids")
    result["duplicate_qa"].update({
        "pairs_examined": len(duplicate_pair_iou),
        "pairs_iou_gt_070": sum(x >= .7 for x in duplicate_pair_iou),
        "pairs_iou_030_to_070": sum(.3 <= x < .7 for x in duplicate_pair_iou),
        "pairs_iou_lt_030": sum(x < .3 for x in duplicate_pair_iou),
        "duplicates_by_fdi": dict(sorted(repeated_fdi.items())),
        "median_pair_iou": _percentile_median(duplicate_pair_iou),
    })
    for fdi in FOCUS_FDI:
        agg = selected[fdi]
        per_split = {
            split: {"instances": counts[split][fdi],
                    "images_present": image_class_counts[split][fdi]}
            for split in SPLITS
        }
        result["per_fdi"][fdi] = {
            "by_split": per_split,
            "total_instances": agg["count"],
            "median_normalized_bbox_area": _percentile_median(agg["area"]),
            "median_normalized_bbox_width": _percentile_median(agg["w"]),
            "median_normalized_bbox_height": _percentile_median(agg["h"]),
            "median_normalized_center_x": _percentile_median(agg["center_x"]),
            "median_normalized_center_y": _percentile_median(agg["center_y"]),
        }
    if private_manifest is not None:
        if private_manifest.suffix.lower() != ".json" or private_manifest.is_symlink():
            _reject("unsafe_private_manifest_output")
        if not private_manifest.parent.is_dir():
            _reject("private_manifest_parent_missing")
        private_manifest.write_text(json.dumps({
            "schema": SCHEMA, "source_image_ids_for_human_review": review_manifest,
            "note": "KEEP PRIVATE; no automatic diagnosis or label rewriting",
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        try:
            private_manifest.chmod(0o600)
        except OSError:
            pass
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels-dir", type=Path, required=True,
                        help="Source .../AKUDENTAL/folds/fold_0/labels")
    parser.add_argument("--private-review-manifest", type=Path,
                        help="LOCAL PRIVATE ONLY, never CI/Notion/GitHub; IDs for dentist review")
    args = parser.parse_args()
    try:
        report = audit_labels(args.labels_dir, private_manifest=args.private_review_manifest)
    except (TriageError, J10Q.LabelAuditError, OSError):
        print(json.dumps({"schema": SCHEMA, "status": "FAIL_CLOSED"}))
        return 1
    print("J10W_AGGREGATE_ONLY=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
