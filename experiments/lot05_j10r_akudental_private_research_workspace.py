#!/usr/bin/env python3
"""J10R: stage a PRIVATE research-only YOLO detection workspace for AKUDENTAL.

Consumes an existing, lawfully obtained local AKUDENTAL checkout. Never downloads,
decodes, copies or uploads radiographs; staged image paths are local symlinks.
Only source YOLO TXT annotations are copied; no LabelMe JSON/imageData.
Scientific pilot only: no assertion of commercial license or clinical validity.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

_MODULE = Path(__file__).with_name("lot05_j10q_akudental_fdi_yolo_text_only.py")
_SPEC = importlib.util.spec_from_file_location("akudental_j10q", _MODULE)
assert _SPEC and _SPEC.loader
_J10Q = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_J10Q)

EXPECTED = {"fold_0": (266, 33, 34), "fold_1": (266, 33, 34),
            "fold_2": (266, 33, 34), "fold_3": (267, 33, 33),
            "fold_4": (267, 33, 33)}
SPLITS = ("train", "val", "test")
SCHEMA = "digital-crown-j10r-akudental-private-yolo35-pilot-v1"


class StageError(ValueError):
    pass


def _abort(reason: str) -> None:
    raise StageError(reason)


def stage(source_root: Path, fold: str, output_dir: Path) -> dict:
    """Create a YOLOv11-compatible workspace after fail-closed label QA."""
    if fold not in EXPECTED:
        _abort("unsupported_fold")
    source_root = source_root.expanduser().resolve(strict=True)
    output_dir = output_dir.expanduser().absolute()
    if not (source_root / "AKUDENTAL").is_dir():
        _abort("source_layout_mismatch")
    data_root = source_root / "AKUDENTAL"
    image_root = data_root / "images"
    labels_root = data_root / "folds" / fold / "labels"
    if not image_root.is_dir() or not labels_root.is_dir():
        _abort("dataset_directories_missing")
    if output_dir.exists() or output_dir.is_symlink():
        _abort("output_must_not_exist")
    # Never generate a working tree inside the original dataset or vice versa.
    if source_root == output_dir or source_root in output_dir.parents or output_dir in source_root.parents:
        _abort("output_overlap_with_source")
    if output_dir.parent.is_symlink():
        _abort("output_parent_symlink_not_allowed")

    parts: dict[str, list[tuple[Path, Path]]] = {}
    paths: list[Path] = []
    all_ids: set[str] = set()
    for split, expected in zip(SPLITS, EXPECTED[fold]):
        folder = labels_root / split
        if not folder.is_dir() or folder.is_symlink():
            _abort("invalid_split_directory")
        items = sorted(folder.glob("*.txt"))
        if len(items) != expected:
            _abort("source_partition_size_mismatch")
        part = []
        for label_path in items:
            if label_path.is_symlink() or not label_path.stem.isdecimal():
                _abort("unsafe_source_label_file")
            if label_path.stem in all_ids:
                _abort("cross_partition_same_image_id")
            all_ids.add(label_path.stem)
            source_image = image_root / (label_path.stem + ".jpg")
            if source_image.is_symlink() or not source_image.is_file():
                _abort("source_image_missing_or_symlink")
            if not 0 < source_image.stat().st_size <= 25_000_000:
                _abort("source_image_size_invalid")
            part.append((label_path, source_image))
            paths.append(label_path)
        parts[split] = part
    if len(all_ids) != 333:
        _abort("dataset_identity_count_mismatch")

    # Validates every text label before ANY workspace write.
    checked = _J10Q.inspect_files(paths)
    if checked["files_checked"] != 333:
        _abort("annotation_coverage_incomplete")

    # Only images are symlinked; source radiograph pixels are never read.
    output_dir.mkdir(parents=True)
    for split in SPLITS:
        dst_i, dst_l = output_dir / "images" / split, output_dir / "labels" / split
        dst_i.mkdir(parents=True)
        dst_l.mkdir(parents=True)
        for label_path, source_image in parts[split]:
            os.symlink(source_image.resolve(strict=True), dst_i / source_image.name)
            (dst_l / label_path.name).write_text(label_path.read_text(encoding="utf-8"),
                                                  encoding="utf-8")

    labels = _J10Q.FDI + tuple("Bridge Filling-Crown Implant".split())
    # Keep the 32 tooth indices AND all three extra restoration classes intact.
    names = "\n".join(f"  {i}: '{name}'" for i, name in enumerate(labels))
    yaml_content = (
        f"path: '{output_dir.as_posix()}'\n"
        "train: images/train\nval: images/val\ntest: images/test\n"
        f"nc: {len(labels)}\nnames:\n{names}\n"
    )
    (output_dir / "data.yaml").write_text(yaml_content, encoding="utf-8")
    return {
        "schema": SCHEMA,
        "status": "PILOT_WORKSPACE_STAGED_NO_TRAINING",
        "fold": fold,
        "source_dataset_revision_required": "92e2cc3ae5eebc9de509311a3edefb7106fca7dd",
        "split_counts": {split: len(parts[split]) for split in SPLITS},
        "image_symlinks": 333,
        "annotations_qa": {
            "files_checked": checked["files_checked"],
            "tooth_instances": checked["tooth_instances"],
            "other_restoration_instances": checked["restoration_instances"],
            "duplicate_fdi_instances_to_review": checked["duplicate_fdi_instances"],
        },
        "commercial_rights_verified": False,
        "clinical_validation": False,
        "training_performed": False,
        "radiograph_pixels_copied_or_read_by_this_script": False,
        "workspace_must_remain_private": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--fold", choices=sorted(EXPECTED), default="fold_0")
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = stage(args.source_repo, args.fold, args.workspace)
    except (_J10Q.LabelAuditError, StageError, OSError) as exc:
        status = {"schema": SCHEMA, "status": "FAIL_CLOSED",
                  "reason": str(exc) if isinstance(exc, (StageError, _J10Q.LabelAuditError))
                  else "filesystem_failure"}
        print(json.dumps(status, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
