#!/usr/bin/env python3
"""J11D: autonomous, source-pinned academic FDI annotation pre-triage.

This is a structural/anatomic-location SCREEN only, never dental diagnosis.
Reads academic YOLO TXT only, does not read image pixels, and emits ONLY
fixed-schema aggregate counts. Source IDs, filenames and bounding box values
are never printed, saved or sent as workflow artifacts.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location(
    "j11d_j10w", HERE / "lot05_j10w_akudental_duplicate_fdi_root_cause.py")
assert SPEC and SPEC.loader
J10W = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = J10W
SPEC.loader.exec_module(J10W)

SCHEMA = "digital-crown-lot05-j11d-aggregate-annotation-pretriage-v1"
SPLITS = {"train": 266, "val": 33, "test": 34}
TOLERANCE = 0.000002


class PretriageError(ValueError):
    pass


def medians(by_class: dict[int, list[tuple]]) -> tuple[float, float]:
    upper = [b[1] for cid, boxes in by_class.items() if cid < 16 for b in boxes]
    lower = [b[1] for cid, boxes in by_class.items() if 16 <= cid < 32 for b in boxes]
    if not upper or not lower:
        raise PretriageError("missing_arch_context")
    u, l = statistics.median(upper), statistics.median(lower)
    if l - u < 0.085:
        raise PretriageError("arch_geometry_not_resolved")
    return u, l


def arch(box: tuple, mids: tuple[float, float]) -> str:
    u, l = mids
    du, dl = abs(box[1] - u), abs(box[1] - l)
    if abs(du - dl) < .035:
        return "uncertain"
    return "upper" if du < dl else "lower"


def kind(boxes: list[tuple], mids: tuple[float, float]) -> str:
    if len(boxes) != 2:
        raise PretriageError("unexpected_duplicate_multiplicity")
    a, b = boxes
    if all(abs(x-y) <= TOLERANCE for x,y in zip(a,b)):
        return "exact_same_coordinates"
    if J10W._iou(a,b) >= .70:
        return "strongly_overlapping_boxes"
    a_arch, b_arch = arch(a,mids), arch(b,mids)
    if a_arch != b_arch and "uncertain" not in (a_arch,b_arch):
        return "cross_arch_suspected"
    if abs(a[0]-b[0]) >= .22:
        return "widely_separated_lateral"
    if abs(a[0]-b[0]) <= .085 and abs(a[1]-b[1]) <= .095:
        return "nearby_distinct_boxes"
    return "other_separated_boxes"


def analyze(by_class: dict[int,list[tuple]]) -> list[dict]:
    # Skip arch inference entirely on files with no duplicate label groups.
    if not any(cid < 32 and len(boxes) > 1 for cid, boxes in by_class.items()):
        return []
    mids = medians(by_class)
    duplicated = []
    for cid, boxes in by_class.items():
        if cid >= 32 or len(boxes) == 1:
            continue
        if len(boxes) != 2:
            raise PretriageError("duplicate_multiplicity_unexpected")
        category = kind(boxes,mids)
        expected = "upper" if cid < 16 else "lower"
        wrong = sum(arch(box,mids) != expected and arch(box,mids) != "uncertain"
                    for box in boxes)
        near_existing_other_class = 0
        for box in boxes:
            if any(J10W._iou(box, other) >= .45
                   for other_id, others in by_class.items()
                   if other_id != cid and other_id < 32 for other in others):
                near_existing_other_class += 1
        duplicated.append({
            "kind": category,
            "wrong_arch_boxes_candidate": wrong,
            "overlaps_other_existing_class_boxes": near_existing_other_class,
            # Only internal aggregate code observes this class ID.
            "fdi_class": J10W.FDA[cid],
        })
    return duplicated


def triage(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir():
        raise PretriageError("invalid_source")
    seen = set()
    classes = Counter()
    categories = Counter()
    by_split = {}
    wrong_arch_candidates = 0
    conflicts_with_other_boxes = 0
    flagged_images = 0
    duplicates = 0
    files_seen = 0
    for split, expected in SPLITS.items():
        directory = root / split
        if directory.is_symlink() or not directory.is_dir():
            raise PretriageError("source_partition_missing")
        labels = sorted(directory.glob("*.txt"))
        if len(labels) != expected:
            raise PretriageError("split_count_changed")
        image_anomalies = 0
        duplicate_groups = 0
        for path in labels:
            if (path.is_symlink() or not path.stem.isdecimal() or path.stem in seen
                    or not 0 < path.stat().st_size <= 128000):
                raise PretriageError("unsafe_label")
            seen.add(path.stem)
            rows = J10W._rows(path.read_text(encoding="utf8"))
            by_class = defaultdict(list)
            for cid, bbox in rows:
                if cid < 32:
                    by_class[cid].append(bbox)
            found = analyze(by_class)
            files_seen += 1
            if found:
                flagged_images += 1
                image_anomalies += 1
            for record in found:
                categories[record["kind"]] += 1
                classes[record["fdi_class"]] += 1
                wrong_arch_candidates += record["wrong_arch_boxes_candidate"]
                conflicts_with_other_boxes += record["overlaps_other_existing_class_boxes"]
                duplicate_groups += 1
                duplicates += 1
        by_split[split] = {"source_images": expected, "images_flagged": image_anomalies,
                           "duplicate_label_groups": duplicate_groups}
    if (files_seen != 333 or len(seen) != 333 or flagged_images != 28
            or duplicates != 31):
        raise PretriageError("pinned_source_expectations_changed")
    return {
        "schema":SCHEMA,
        "status":"ACADEMIC_FDI_STRUCTURAL_PRETRIAGE_NOT_CLINICAL_REVIEW",
        "source_images":files_seen,
        "flagged_images":flagged_images,
        "same_fdi_duplicate_groups":duplicates,
        "split_totals":by_split,
        "anomaly_categories":dict(sorted(categories.items())),
        "duplicate_classes_aggregate":dict(sorted(classes.items())),
        "wrong_arch_box_candidates_geometry_only":wrong_arch_candidates,
        "duplicated_boxes_overlapping_other_fdi_boxes_iou_ge_045":conflicts_with_other_boxes,
        "pixel_images_read":False,
        "case_ids_or_coordinates_emitted":False,
        "clinical_adjudications_by_runner":0,
        "patient_independence_established":False,
        "commercial_rights_verified":False,
        "source_annotations_changed":False,
        "automatic_label_corrections_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels-dir",type=Path,required=True)
    args=parser.parse_args()
    try:
        report=triage(args.labels_dir)
    except (PretriageError,J10W.TriageError,J10W.J10Q.LabelAuditError,
            OSError,UnicodeError,ValueError) as exc:
        # Only static, non-identifier error codes from this module may be logged.
        code = str(exc) if isinstance(exc,PretriageError) else "validation_or_io_failure"
        print(json.dumps({"schema":SCHEMA,"status":"FAIL_CLOSED","reason_code":code}))
        return 1
    print("J11D_AGGREGATE_ONLY="+json.dumps(report,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
