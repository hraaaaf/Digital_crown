#!/usr/bin/env python3
"""J10P: local-only COCO annotation intake for the Roboflow FDI-32 v1 export.

No network, patient pixels, model inference, training, cloud transfer or publication.
Never output image names, coordinates, source IDs or private annotation contents.
A structural PASS does NOT prove provenance, patient-level split independence,
clinical validity or training/commercial rights.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re

FDI = frozenset(str(q * 10 + i) for q in (1, 2, 3, 4) for i in range(1, 9))
SPLITS = {"train": 3032, "valid": 315, "test": 156}
LIMIT_BYTES = 64_000_000
MAX_IMAGES = 10_000
MAX_ANNOTATIONS = 400_000
SCHEMA = "digital-crown-j10p-roboflow-fdi32-coco-offline-intake-v1"


class IntakeError(ValueError):
    pass


def reject(code: str) -> None:
    raise IntakeError(code)


def _int(value: object) -> bool:
    return type(value) is int and value >= 0


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _json_only(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        reject("annotation_json_missing_or_symlink")
    size = path.stat().st_size
    if size <= 0 or size > LIMIT_BYTES:
        reject("annotation_json_invalid_size")
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError):
        reject("annotation_json_invalid_encoding_or_structure")
    if not isinstance(content, dict):
        reject("annotation_json_not_object")
    return content


def _safe_image_name(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        reject("unsafe_or_missing_image_name")
    if ("/" in value or "\\" in value or ":" in value
            or value.startswith(".") or "\x00" in value):
        reject("unsafe_image_name")
    if Path(value).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        reject("unsupported_image_extension")
    return value


def _origin_hint(name: str) -> str:
    # Best-effort publisher filename pattern, NOT a patient/source identifier.
    # Absence of collision is not evidence of a leakage-free split.
    stem = Path(name).stem.casefold()
    return re.sub(r"\.rf\.[a-f0-9]{6,64}$", "", stem)


def _split(root: Path, split: str) -> tuple[dict, set[str]]:
    folder = root / split
    if folder.is_symlink() or not folder.is_dir():
        reject(split + "_directory_missing_or_symlink")
    doc = _json_only(folder / "_annotations.coco.json")
    images = doc.get("images")
    categories = doc.get("categories")
    annotations = doc.get("annotations")
    if not isinstance(images, list) or len(images) > MAX_IMAGES:
        reject(split + "_images_invalid")
    if not isinstance(categories, list) or not isinstance(annotations, list):
        reject(split + "_coco_collections_missing")
    if len(annotations) > MAX_ANNOTATIONS:
        reject(split + "_too_many_annotations")
    if len(images) != SPLITS[split]:
        reject(split + "_published_version_one_count_mismatch")

    category_ids: dict[int, str] = {}
    labels: set[str] = set()
    for category in categories:
        if not isinstance(category, dict):
            reject(split + "_invalid_category")
        cid, label = category.get("id"), category.get("name")
        if not _int(cid) or not isinstance(label, str):
            reject(split + "_invalid_category_id_or_label")
        if cid in category_ids or label in labels:
            reject(split + "_duplicate_category")
        category_ids[cid] = label
        labels.add(label)
    if labels != FDI or len(category_ids) != 32:
        reject(split + "_fdi32_class_map_mismatch")

    image_sizes: dict[int, tuple[int, int]] = {}
    origin_hints: set[str] = set()
    filenames: set[str] = set()
    for image in images:
        if not isinstance(image, dict):
            reject(split + "_invalid_image_record")
        iid, width, height = image.get("id"), image.get("width"), image.get("height")
        if not _int(iid) or not _int(width) or not _int(height):
            reject(split + "_invalid_image_dimensions_or_id")
        if not 0 < width <= 20_000 or not 0 < height <= 20_000:
            reject(split + "_implausible_image_dimensions")
        if iid in image_sizes:
            reject(split + "_duplicate_image_id")
        filename = _safe_image_name(image.get("file_name"))
        if filename.casefold() in filenames:
            reject(split + "_duplicate_filename")
        filenames.add(filename.casefold())
        path = folder / filename
        if path.is_symlink() or not path.is_file():
            reject(split + "_image_missing_or_symlink")
        image_sizes[iid] = (width, height)
        origin_hints.add(_origin_hint(filename))

    annotation_ids: set[int] = set()
    per_image_label: Counter[tuple[int, str]] = Counter()
    label_counts: Counter[str] = Counter()
    for ann in annotations:
        if not isinstance(ann, dict):
            reject(split + "_invalid_annotation_record")
        aid, iid, cid = ann.get("id"), ann.get("image_id"), ann.get("category_id")
        if not _int(aid) or not _int(iid) or not _int(cid):
            reject(split + "_invalid_annotation_reference")
        if aid in annotation_ids:
            reject(split + "_duplicate_annotation_id")
        annotation_ids.add(aid)
        if iid not in image_sizes or cid not in category_ids:
            reject(split + "_dangling_annotation_reference")
        box = ann.get("bbox")
        if not isinstance(box, list) or len(box) != 4 or not all(_number(v) for v in box):
            reject(split + "_invalid_bbox")
        x, y, w, h = box
        width, height = image_sizes[iid]
        # COCO xywh pixel coordinates. Small rounding tolerance only.
        if (x < -0.001 or y < -0.001 or w <= 0 or h <= 0
                or x + w > width + 0.001 or y + h > height + 0.001):
            reject(split + "_bbox_out_of_image_bounds")
        label = category_ids[cid]
        label_counts[label] += 1
        per_image_label[(iid, label)] += 1

    result = {
        "image_count": len(images),
        "annotation_count": len(annotations),
        "fdi_class_count": len(category_ids),
        "distinct_fdi_labels_with_boxes": len(label_counts),
        "fdi_labels_without_boxes": sorted(FDI - set(label_counts)),
        "image_fdi_duplicate_label_pairs": sum(n > 1 for n in per_image_label.values()),
        "images_without_boxes": len(images) - len({iid for iid, _ in per_image_label}),
    }
    return result, origin_hints


def inspect(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir():
        reject("export_directory_missing_or_symlink")
    results = {}
    hints = {}
    for split in SPLITS:
        results[split], hints[split] = _split(root, split)
    overlaps = {}
    for first, second in (("train", "valid"), ("train", "test"), ("valid", "test")):
        overlaps[first + "_" + second] = len(hints[first] & hints[second])
    return {
        "schema": SCHEMA,
        "status": "ANNOTATION_STRUCTURE_PASS_NOT_CLINICALLY_CLEARED",
        "export_assumed": "Roboflow Panoramic-Dental-Xray-FDI v1, COCO JSON",
        "splits": results,
        "images_total": sum(part["image_count"] for part in results.values()),
        "annotations_total": sum(part["annotation_count"] for part in results.values()),
        "possible_cross_split_source_stem_collisions": overlaps,
        "origin_hint_collision_is_proof_of_patient_overlap": False,
        "patient_level_split_independence_proven": False,
        "all_images_are_independent_originals_proven": False,
        "source_patient_rights_verified": False,
        "commercial_training_authorized": False,
        "clinical_fdi_accuracy_measured": False,
        "clinical_use_authorized": False,
        "image_pixels_read_or_uploaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, help="Optional aggregate-only local JSON")
    args = parser.parse_args()
    try:
        report = inspect(args.dataset_dir)
    except (IntakeError, OSError) as exc:
        message = str(exc) if isinstance(exc, IntakeError) else "local_file_unavailable"
        report = {"schema": SCHEMA, "status": "ANNOTATION_INTAKE_FAIL_CLOSED",
                  "reason": message, "clinical_use_authorized": False,
                  "commercial_training_authorized": False}
        code = 1
    else:
        code = 0
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
