#!/usr/bin/env python3
"""J10Q — AKUDENTAL text-only YOLO FDI-32 structural intake.

For independent academic research screening only; source licence
CC BY-NC-SA 4.0 is NOT commercial or clinical training clearance.
Reads text-only YOLO labels. Never opens images or LabelMe JSON:
some upstream LabelMe JSON entries contain embedded imageData pixels.
Does not use network, inference, training or any clinic data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re

MAX_LABEL_BYTES = 128_000
MAX_ROWS = 1024
FDI = tuple(f"{quadrant}{tooth}" for quadrant in (1, 2, 3, 4)
            for tooth in range(1, 9))
RESTORATIONS = ("bridge", "filling_crown", "implant")
SCHEMA = "digital-crown-j10q-akudental-fdi32-yolo-text-only-v1"


class LabelAuditError(ValueError):
    pass


def _fail(reason: str) -> None:
    raise LabelAuditError(reason)


def audit_label_text(text: str) -> dict:
    """Aggregate a YOLO 35-class object-detection label without retaining coordinates."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_LABEL_BYTES:
        _fail("invalid_text_or_size")
    rows = [row.strip() for row in text.splitlines() if row.strip()]
    if len(rows) > MAX_ROWS:
        _fail("too_many_rows")
    classes: Counter[int] = Counter()
    seen_fdi: set[int] = set()
    duplicate_fdi = 0
    for row in rows:
        fields = re.split(r"\s+", row)
        if len(fields) != 5:
            _fail("not_five_yolo_columns")
        if not re.fullmatch(r"(?:0|[1-9][0-9]*)", fields[0]):
            _fail("invalid_class_id")
        cid = int(fields[0])
        if not 0 <= cid < len(FDI) + len(RESTORATIONS):
            _fail("unexpected_class_id")
        try:
            cx, cy, width, height = (float(x) for x in fields[1:])
        except ValueError:
            _fail("non_numeric_geometry")
        if not all(math.isfinite(v) for v in (cx, cy, width, height)):
            _fail("non_finite_geometry")
        if not (0 <= cx <= 1 and 0 <= cy <= 1 and
                0 < width <= 1 and 0 < height <= 1):
            _fail("geometry_outside_unit_range")
        tolerance = 0.000002
        if (cx - width / 2 < -tolerance or cx + width / 2 > 1 + tolerance
                or cy - height / 2 < -tolerance or cy + height / 2 > 1 + tolerance):
            _fail("bbox_outside_image_frame")
        if cid < 32:
            if cid in seen_fdi:
                duplicate_fdi += 1
            seen_fdi.add(cid)
        classes[cid] += 1

    return {
        "status": "TEXT_ANNOTATION_STRUCTURE_PASS_NOT_RIGHTS_CLEARED",
        "tooth_instances": sum(n for cid, n in classes.items() if cid < 32),
        "distinct_tooth_positions": len(seen_fdi),
        "extra_restoration_instances": {
            RESTORATIONS[cid - 32]: classes[cid] for cid in range(32, 35)
        },
        "duplicate_fdi_instances": duplicate_fdi,
        "instance_count": len(rows),
        "fdi32_ontology_complete": len(FDI) == 32,
        "missing_teeth_may_be_normal": True,
        "commercial_training_authorized": False,
        "clinical_use_authorized": False,
        "pixels_read": False,
    }


def inspect_files(paths: list[Path]) -> dict:
    if not paths or len(paths) > 333:
        _fail("invalid_file_count")
    aggregate = {
        "schema": SCHEMA,
        "status": "TEXT_ONLY_RESEARCH_QA_NOT_LICENSE_CLEARED",
        "files_checked": 0,
        "instances": 0,
        "tooth_instances": 0,
        "duplicate_fdi_instances": 0,
        "classes_present": [],
        "restoration_instances": {name: 0 for name in RESTORATIONS},
        "uses_real_image_pixels": False,
        "commercial_training_authorized": False,
        "clinical_use_authorized": False,
        "patient_level_independence_proven": False,
    }
    # Private identifiers, image names and coordinates are never placed in the report.
    observed: set[str] = set()
    seen_paths: set[Path] = set()
    for path in paths:
        if path in seen_paths or path.is_symlink() or path.suffix.lower() != ".txt" or not path.is_file():
            _fail("unsafe_or_missing_label_file")
        seen_paths.add(path)
        if path.stat().st_size > MAX_LABEL_BYTES:
            _fail("label_file_too_large")
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            _fail("invalid_label_text_encoding")
        current = audit_label_text(raw)
        aggregate["files_checked"] += 1
        aggregate["instances"] += current["instance_count"]
        aggregate["tooth_instances"] += current["tooth_instances"]
        aggregate["duplicate_fdi_instances"] += current["duplicate_fdi_instances"]
        for name, n in current["extra_restoration_instances"].items():
            aggregate["restoration_instances"][name] += n
        for line in raw.splitlines():
            if line.strip():
                observed.add(FDI[int(line.split()[0])] if int(line.split()[0]) < 32 else
                             RESTORATIONS[int(line.split()[0]) - 32])
    aggregate["classes_present"] = sorted(observed)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label_files", type=Path, nargs="+", help="YOLO label .txt files only")
    parser.add_argument("--output-json", type=Path, help="Optional local aggregate output")
    args = parser.parse_args()
    try:
        report = inspect_files(args.label_files)
    except (LabelAuditError, OSError) as exc:
        code = 1
        report = {"schema": SCHEMA, "status": "FAIL_CLOSED",
                  "reason": str(exc) if isinstance(exc, LabelAuditError) else "local_io_failure",
                  "commercial_training_authorized": False,
                  "clinical_use_authorized": False}
    else:
        code = 0
    serialized = json.dumps(report, sort_keys=True)
    if args.output_json:
        args.output_json.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
