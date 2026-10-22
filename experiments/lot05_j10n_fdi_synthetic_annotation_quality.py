#!/usr/bin/env python3
"""LOT05/J10N: FDI annotation QA on synthetic METADATA, NEVER clinical images.

No image files, names, DICOM headers, patients or URLs are accepted or read.
A passing report demonstrates annotation/split/dual-review controls only,
and is NEVER permission to train/transfer a real clinical dataset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from lot05_j10l_fdi_training_readiness import (
    AUDIT, FDI_32, FDITrainingBlock, audit_dataset_manifest,
    check_research_only_mode,
)

SCHEMA = "digital-crown-fdi-j10n-annotation-review-synthetic-v1"
REPORT_SCHEMA = "digital-crown-fdi-j10n-quality-gate-v1"
ALLOWED_SPLITS = {"train", "val", "test_external"}
DATASET_KEYS = {"schema", "mode", "rights", "fdi_labels", "records"}
RIGHTS_KEYS = {
    "real_data_training_approved", "cloud_image_processing_approved",
    "commercial_release_approved", "patient_data_present",
}
RECORD_KEYS = {
    "record_id", "subject_group", "near_duplicate_group", "source_site",
    "split", "image_sha256", "orientation_verified_synthetic",
    "edentulous_confirmed", "review_a", "review_b", "adjudication",
}
REVIEW_KEYS = {"reviewer_id", "teeth"}
TOOTH_KEYS = {"fdi", "bbox_cxcywh"}
ADJ_KEYS = {"reviewer_id", "teeth"}


class SyntheticAnnotationError(ValueError):
    pass


def _ensure(condition: bool, reason: str) -> None:
    if not condition:
        raise SyntheticAnnotationError(reason)


def _keys(obj: object, required: set[str], error: str) -> None:
    _ensure(type(obj) is dict and set(obj) == required, error)


def _matches(value: object, pattern: str) -> bool:
    return type(value) is str and re.fullmatch(pattern, value) is not None


def _teeth(teeth: object, record_id: str) -> dict[int, tuple[float, float, float, float]]:
    _ensure(type(teeth) is list and len(teeth) <= 32, "invalid_tooth_count:" + record_id)
    seen: dict[int, tuple[float, float, float, float]] = {}
    for tooth in teeth:
        _keys(tooth, TOOTH_KEYS, "invalid_tooth_annotation_keys")
        fdi = tooth["fdi"]
        _ensure(type(fdi) is int and fdi in FDI_32, "invalid_fdi_id:" + record_id)
        _ensure(fdi not in seen, "duplicate_tooth_id:" + record_id)
        bbox = tooth["bbox_cxcywh"]
        _ensure(type(bbox) is list and len(bbox) == 4, "invalid_box")
        _ensure(
            all(type(v) in (int, float) and math.isfinite(v) for v in bbox),
            "nonfinite_or_nonnumeric_bbox",
        )
        cx, cy, w, h = bbox
        _ensure(
            0 < w <= 1 and 0 < h <= 1
            and w / 2 <= cx <= 1 - w / 2
            and h / 2 <= cy <= 1 - h / 2,
            "out_of_bounds_bbox",
        )
        seen[fdi] = (float(cx), float(cy), float(w), float(h))
    return seen


def _iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    ax0, ay0, aw, ah = a
    bx0, by0, bw, bh = b
    left = max(ax0 - aw / 2, bx0 - bw / 2)
    right = min(ax0 + aw / 2, bx0 + bw / 2)
    top = max(ay0 - ah / 2, by0 - bh / 2)
    bottom = min(ay0 + ah / 2, by0 + bh / 2)
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0


def _review(value: object, record_id: str) -> tuple[str, dict]:
    _keys(value, REVIEW_KEYS, "reviewer_fields_invalid")
    reviewer_id = value["reviewer_id"]
    _ensure(_matches(reviewer_id, r"SYN-REV-[1-9][0-9]?"), "reviewer_identity_must_be_synthetic")
    return reviewer_id, _teeth(value["teeth"], record_id)


def _agreement(a: dict, b: dict) -> bool:
    return set(a) == set(b) and all(_iou(a[fdi], b[fdi]) >= 0.70 for fdi in a)


def _synth_tooth(fdi: int, i: int) -> dict:
    return {
        "fdi": fdi,
        "bbox_cxcywh": [round(0.10 + 0.15 * i, 3), 0.36, 0.08, 0.18],
    }


def synthetic_registry() -> dict:
    """Build 5 tiny synthetic review records. ZERO images or patient records."""
    specs = [
        (1, "SYN-G001", "SYN-D001", "SYN-SITE-A", "train", [11, 12, 13, 14]),
        (2, "SYN-G001", "SYN-D001", "SYN-SITE-A", "train", [11, 12, 14]),
        (3, "SYN-G002", "SYN-D002", "SYN-SITE-A", "train", [21, 22, 23, 24]),
        (4, "SYN-G003", "SYN-D003", "SYN-SITE-A", "val", []),
        (5, "SYN-G004", "SYN-D004", "SYN-SITE-B", "test_external", [31, 32, 33, 34]),
    ]
    records = []
    for i, group, duplicate, site, split, fdis in specs:
        teeth = [_synth_tooth(fdi, index) for index, fdi in enumerate(fdis)]
        alternative = [dict(t) for t in teeth]
        # Intentionally disagree on one FDI label, then require independent
        # adjudication; no reviewer decisions are silently overwritten.
        if i == 3:
            alternative.pop()
        records.append({
            "record_id": f"SYN-R{i:03d}",
            "subject_group": group,
            "near_duplicate_group": duplicate,
            "source_site": site,
            "split": split,
            "image_sha256": hashlib.sha256(
                f"NON_IMAGE_GEOMETRY_J10N_{i}".encode()
            ).hexdigest(),
            "orientation_verified_synthetic": True,
            "edentulous_confirmed": not fdis,
            "review_a": {"reviewer_id": "SYN-REV-1", "teeth": teeth},
            "review_b": {"reviewer_id": "SYN-REV-2", "teeth": alternative},
            "adjudication": (
                {"reviewer_id": "SYN-REV-3", "teeth": teeth}
                if i == 3 else None
            ),
        })
    return {
        "schema": SCHEMA,
        "mode": "synthetic_only",
        "rights": {
            "real_data_training_approved": False,
            "cloud_image_processing_approved": False,
            "commercial_release_approved": False,
            "patient_data_present": False,
        },
        "fdi_labels": list(FDI_32),
        "records": records,
    }


def validate_synthetic_registry(data: object) -> dict:
    _keys(data, DATASET_KEYS, "invalid_top_level_schema")
    _ensure(data["schema"] == SCHEMA and data["mode"] == "synthetic_only",
            "clinical_dataset_mode_not_authorized")
    _keys(data["rights"], RIGHTS_KEYS, "rights_schema_invalid")
    _ensure(all(data["rights"][x] is False for x in RIGHTS_KEYS),
            "real_data_rights_cannot_be_self_declared")
    _ensure(data["fdi_labels"] == list(FDI_32) and type(data["fdi_labels"]) is list,
            "FDI_32_map_invalid")
    records = data["records"]
    _ensure(type(records) is list and 4 <= len(records) <= 100,
            "invalid_synthetic_record_count")
    groups: dict[str, tuple[str, str]] = {}
    duplicate_splits: dict[str, str] = {}
    image_hashes: set[str] = set()
    record_ids: set[str] = set()
    split_counts = {split: 0 for split in ("train", "val", "test_external")}
    non_external_sites: set[str] = set()
    external_sites: set[str] = set()
    accepted_teeth = 0
    adjudicated_cases = 0
    toothless = 0
    for record in records:
        _keys(record, RECORD_KEYS, "record_keys_invalid_or_potential_patient_metadata")
        rid = record["record_id"]
        _ensure(_matches(rid, r"SYN-R[0-9]{3}") and rid not in record_ids,
                "record_id_invalid_or_duplicate")
        record_ids.add(rid)
        group = record["subject_group"]
        duplicate_group = record["near_duplicate_group"]
        site = record["source_site"]
        split = record["split"]
        _ensure(_matches(group, r"SYN-G[0-9]{3}"), "real_patient_group_not_permitted")
        _ensure(_matches(duplicate_group, r"SYN-D[0-9]{3}"), "duplicate_group_invalid")
        _ensure(_matches(site, r"SYN-SITE-[A-Z]"), "source_site_not_synthetic")
        _ensure(type(split) is str and split in ALLOWED_SPLITS, "invalid_split")
        _ensure(
            group not in groups or groups[group] == (split, site),
            "same_subject_in_multiple_splits_or_sites",
        )
        groups[group] = (split, site)
        _ensure(
            duplicate_group not in duplicate_splits or duplicate_splits[duplicate_group] == split,
            "near_duplicate_leaked_across_splits",
        )
        duplicate_splits[duplicate_group] = split
        digest = record["image_sha256"]
        _ensure(_matches(digest, r"[0-9a-f]{64}") and digest not in image_hashes,
                "duplicate_file_hash_or_invalid_hash")
        image_hashes.add(digest)
        _ensure(record["orientation_verified_synthetic"] is True,
                "orientation_not_reviewed")
        _ensure(type(record["edentulous_confirmed"]) is bool,
                "missing_toothless_scope")
        ra, aa = _review(record["review_a"], rid)
        rb, bb = _review(record["review_b"], rid)
        _ensure(ra != rb, "same_person_double_review")
        _ensure(record["edentulous_confirmed"] == (not aa and not bb),
                "edentulous_must_be_explicit_and_reviewed_twice")
        if record["edentulous_confirmed"]:
            toothless += 1
        independent_agreement = _agreement(aa, bb)
        adjudication = record["adjudication"]
        if independent_agreement:
            _ensure(adjudication is None, "unnecessary_adjudication")
            final = aa
        else:
            _keys(adjudication, ADJ_KEYS, "disagreement_requires_adjudication")
            arbiter = adjudication["reviewer_id"]
            _ensure(
                _matches(arbiter, r"SYN-REV-[1-9][0-9]?")
                and arbiter not in {ra, rb},
                "adjudicator_must_be_independent",
            )
            final = _teeth(adjudication["teeth"], rid)
            _ensure(bool(final) and not record["edentulous_confirmed"],
                    "disagreement_cannot_be_dropped_without_review")
            adjudicated_cases += 1
        accepted_teeth += len(final)
        split_counts[split] += 1
        (external_sites if split == "test_external" else non_external_sites).add(site)
    _ensure(all(split_counts.values()), "missing_train_val_or_external_test")
    _ensure(not non_external_sites.intersection(external_sites),
            "external_test_site_leaks_into_training")
    return {
        "schema": REPORT_SCHEMA,
        "status": "SYNTHETIC_ANNOTATION_QA_PASS_REAL_DATA_BLOCKED",
        "synthetic_record_count": len(records),
        "synthetic_subject_groups": len(groups),
        "synthetic_near_duplicate_groups": len(duplicate_splits),
        "split_counts": split_counts,
        "accepted_synthetic_tooth_boxes": accepted_teeth,
        "adjudicated_synthetic_cases": adjudicated_cases,
        "synthetic_edentulous_cases": toothless,
        "fdi_classes_supported": len(FDI_32),
        "external_test_site_isolated": True,
        "clinical_radiographs_processed": 0,
        "real_dataset_training_approved": False,
        "commercial_model_release_approved": False,
        "clinical_use_approved": False,
        "gh_actions_patient_transfer_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["synthetic_only"])
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    try:
        check_research_only_mode("synthetic_geometry", "")
        status = audit_dataset_manifest(json.loads(AUDIT.read_text(encoding="utf-8")))
        _ensure(status["cloud_image_processing_go"] is False,
                "unexpected_cloud_rights_authorization")
        result = validate_synthetic_registry(synthetic_registry())
    except (OSError, FDITrainingBlock, SyntheticAnnotationError, ValueError) as exc:
        result = {
            "schema": REPORT_SCHEMA,
            "status": "FAIL_CLOSED",
            "reason": str(exc)[:200],
            "real_dataset_training_approved": False,
            "clinical_use_approved": False,
        }
        args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))
        return 1
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
