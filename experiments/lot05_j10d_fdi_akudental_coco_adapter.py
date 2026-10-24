#!/usr/bin/env python3
"""LOT05/05.7-J10D: Convert author-supplied AKUDENTAL-style COCO to local FDI eval manifest.

Research-only. ALL inputs/outputs stay on the authorized local workstation.
Run only on a lawfully acquired, independently sourced labelled collection.
No patient images, IDs, file names or manifests may enter GitHub/CI/cloud.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re

from lot05_j10d_fdi_local_benchmark import BenchmarkError
from lot05_j10d_fdi_tooth_model_probe import CLASS_ORDER

FDI = frozenset(CLASS_ORDER)
# Exact categories described by the author's AKUDENTAL/dataset.yaml, not pathologic findings.
EXTRA_CATEGORIES = frozenset({"bridge", "filling - crown", "filling-crown", "implant"})
FDI_NAME = re.compile(r"^\s*(1[1-8]|2[1-8]|3[1-8]|4[1-8])(?:\s*[-_:]\s*.*)?\s*$")


def category_map(categories: list[dict]) -> dict[int, str | None]:
    if not isinstance(categories, list) or len(categories) != 35:
        raise BenchmarkError("akudental_expected_32_fdi_plus_3_non_tooth_categories")
    output, teeth, extras = {}, set(), set()
    for item in categories:
        if not isinstance(item, dict) or not isinstance(item.get("id"), int) or isinstance(item["id"], bool):
            raise BenchmarkError("invalid_coco_category_id")
        identifier = item["id"]
        if identifier in output:
            raise BenchmarkError("duplicate_coco_category_id")
        name = item.get("name")
        if not isinstance(name, str):
            raise BenchmarkError("missing_coco_category_name")
        found = FDI_NAME.fullmatch(name)
        if found:
            code = found.group(1)
            if code in teeth:
                raise BenchmarkError("duplicate_fdi_category_name")
            teeth.add(code)
            output[identifier] = code
        else:
            canon = re.sub(r"\s+", " ", name).strip().lower()
            if canon not in EXTRA_CATEGORIES or canon in extras:
                raise BenchmarkError("unknown_or_repeated_coco_category")
            extras.add(canon)
            output[identifier] = None
    if teeth != FDI or len(extras) != 3:
        raise BenchmarkError("incomplete_32_fdi_category_mapping")
    return output


def _real_image_file(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise BenchmarkError("bad_image_filename")
    if any(p in {".", ".."} for p in Path(relative).parts):
        raise BenchmarkError("image_filename_traversal")
    if Path(relative).suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}:
        raise BenchmarkError("unsupported_image_suffix")
    root = base.resolve(strict=True)
    candidate = base / relative
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file() or candidate.is_symlink():
        raise BenchmarkError("image_path_outside_authorized_root")
    return resolved


def coco_to_manifest(coco: dict, *, images_root: Path, site_group: int | None = None,
                     device_group: int | None = None, max_images: int | None = None) -> tuple[dict, dict]:
    if not isinstance(coco, dict):
        raise BenchmarkError("bad_coco_document")
    categories = category_map(coco.get("categories"))
    images = coco.get("images")
    annotations = coco.get("annotations")
    if not isinstance(images, list) or not images or not isinstance(annotations, list):
        raise BenchmarkError("missing_coco_images_or_annotations")
    if len(images) > 20000 or len(annotations) > 1000000:
        raise BenchmarkError("dataset_above_safety_limit")
    if site_group is not None and not 1 <= site_group <= 50:
        raise BenchmarkError("invalid_site_group")
    if device_group is not None and not 1 <= device_group <= 50:
        raise BenchmarkError("invalid_device_group")
    if max_images is not None and max_images < 1:
        raise BenchmarkError("invalid_max_images")
    image_lookup, names = {}, set()
    for info in images:
        if not isinstance(info, dict):
            raise BenchmarkError("invalid_coco_image")
        image_id = info.get("id")
        name = info.get("file_name")
        h, w = info.get("height"), info.get("width")
        if (not isinstance(image_id, int) or isinstance(image_id, bool) or image_id in image_lookup
            or not isinstance(h, int) or isinstance(h, bool) or not isinstance(w, int)
            or isinstance(w, bool) or not 0 < h <= 10000 or not 0 < w <= 10000
            or not isinstance(name, str) or name in names):
            raise BenchmarkError("duplicate_or_invalid_coco_image")
        image_lookup[image_id] = {"name": name, "height": h, "width": w}
        names.add(name)

    gt_by_image = defaultdict(list)
    skipped_non_tooth = Counter()
    annotation_ids = set()
    duplicates_fdi_gt = Counter()
    for item in annotations:
        if not isinstance(item, dict):
            raise BenchmarkError("invalid_coco_annotation")
        ai, image_id, category_id = item.get("id"), item.get("image_id"), item.get("category_id")
        if not isinstance(ai, int) or isinstance(ai, bool) or ai in annotation_ids:
            raise BenchmarkError("duplicate_or_invalid_annotation_id")
        annotation_ids.add(ai)
        if image_id not in image_lookup or category_id not in categories:
            raise BenchmarkError("unknown_image_or_category_in_annotation")
        fdi = categories[category_id]
        if fdi is None:
            skipped_non_tooth["non_tooth_ignored"] += 1
            continue
        if item.get("iscrowd", 0) not in (0, False):
            raise BenchmarkError("crowd_fdi_gt_not_supported")
        bbox = item.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise BenchmarkError("invalid_coco_xywh_bbox")
        if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in bbox):
            raise BenchmarkError("nonfinite_coco_bbox")
        x, y, bw, bh = map(float, bbox)
        hi = image_lookup[image_id]["height"]
        wi = image_lookup[image_id]["width"]
        eps = 1e-6
        if x < -eps or y < -eps or bw <= 0 or bh <= 0 or x + bw > wi + eps or y + bh > hi + eps:
            raise BenchmarkError("coco_bbox_outside_image")
        normalized = {"fdi": fdi, "bbox": [max(0.0, x), max(0.0, y), min(float(wi), x + bw), min(float(hi), y + bh)]}
        gt_by_image[image_id].append(normalized)

    # Deterministic fixed prefix, not selected after seeing model predictions.
    selected = sorted(image_lookup)[:max_images] if max_images is not None else sorted(image_lookup)
    manifest = {"schema": "digital-crown-fdi-eval-v1", "cases": []}
    seen_image_files = set()
    for img_id in selected:
        meta = image_lookup[img_id]
        image_path = _real_image_file(images_root, meta["name"])
        relative = image_path.relative_to(images_root.resolve(strict=True))
        if relative in seen_image_files:
            raise BenchmarkError("duplicate_image_file")
        seen_image_files.add(relative)
        gt = gt_by_image[img_id]
        counts = Counter(x["fdi"] for x in gt)
        duplicates_fdi_gt.update(k for k, v in counts.items() if v > 1)
        case = {"case_id": f"source-{img_id}", "image": relative.as_posix(),
                "height": meta["height"], "width": meta["width"],
                "dentition": "unknown", "gt": gt}
        if site_group is not None:
            case["site_group"] = site_group
        if device_group is not None:
            case["device_group"] = device_group
        manifest["cases"].append(case)

    audit = {
        "status": "LOCAL_COCO_FDI_MANIFEST_CREATED_NOT_CLINICALLY_VALIDATED",
        "dataset_label": "AKUDENTAL-style COCO, source must be verified",
        "images_total_in_coco": len(images),
        "images_selected": len(selected),
        "ground_truth_teeth_selected": sum(len(c["gt"]) for c in manifest["cases"]),
        "image_with_no_fdi_annotation": sum(not c["gt"] for c in manifest["cases"]),
        "ignored_non_tooth_annotations_total": skipped_non_tooth["non_tooth_ignored"],
        "selected_images_with_duplicate_gt_fdi": sum(
            len(set(a["fdi"] for a in c["gt"])) != len(c["gt"]) for c in manifest["cases"]),
        "patient_and_DENTEX_overlap_checked": False,
        "clinical_fdi_labels_adjudicated_by_this_project": False,
        "image_bytes_or_ids_in_audit_report": False,
        "notes": "All image paths and case IDs remain in the protected local manifest only.",
    }
    return manifest, audit


def main():
    parser = argparse.ArgumentParser(description="AKUDENTAL 35-class COCO to 32-FDI offline evaluation manifest; research only")
    parser.add_argument("--coco", type=Path, required=True)
    parser.add_argument("--images-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit-report", type=Path, required=True)
    parser.add_argument("--site-group", type=int)
    parser.add_argument("--device-group", type=int)
    parser.add_argument("--max-images", type=int)
    parser.add_argument("--authorized-local-conversion", action="store_true", required=True)
    args = parser.parse_args()
    if args.manifest == args.audit_report:
        raise BenchmarkError("manifest_and_audit_must_be_separate")
    data = json.loads(args.coco.read_text(encoding="utf-8"))
    manifest, audit = coco_to_manifest(data, images_root=args.images_root,
             site_group=args.site_group, device_group=args.device_group, max_images=args.max_images)
    # Restrict local outputs to current user where supported; never write to repository/CI.
    try:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.audit_report.parent.mkdir(parents=True, exist_ok=True)
        import os
        os.umask(0o077)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        args.audit_report.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    finally:
        pass
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
