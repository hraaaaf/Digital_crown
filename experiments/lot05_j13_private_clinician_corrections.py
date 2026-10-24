#!/usr/bin/env python3
"""J13: public-safe aggregate preflight and OWNER-PRIVATE academic FDI staging.

Public CI NEVER consumes sample-level clinician manifests or saves corrected
annotations. Clinician manifest and output are OWNER PRIVATE ONLY. No pixels.
Successful Actions are not clinical, legal, patient-independence, or release proof.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "j13_j10w", HERE / "lot05_j10w_akudental_duplicate_fdi_root_cause.py")
assert SPEC and SPEC.loader
J10W = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = J10W
SPEC.loader.exec_module(J10W)

SCHEMA = "digital-crown-lot05-j13-private-clinician-staging-v1"
MANIFEST_SCHEMA = "digital-crown-lot05-j13-private-decision-map-v1"
PIN = "92e2cc3ae5eebc9de509311a3edefb7106fca7dd"
SPLITS = {"train": 266, "val": 33, "test": 34}
FDI = {f"{q}{p}": 8 * (q-1) + (p-1)
       for q in range(1, 5) for p in range(1, 9)}
TOL = 0.000001


class J13Error(ValueError):
    pass


def reject(code):
    raise J13Error(code)


def labels_inventory(root: Path):
    if not root.is_dir() or root.is_symlink():
        reject("invalid_source_root")
    result, seen = {}, set()
    for split, expected in SPLITS.items():
        d = root / split
        if not d.is_dir() or d.is_symlink():
            reject("missing_partition")
        paths = sorted(d.glob("*.txt"))
        if len(paths) != expected:
            reject("unexpected_partition_count")
        for p in paths:
            if (p.is_symlink() or not p.is_file() or
                    not p.stem.isdecimal() or p.stem in seen):
                reject("invalid_academic_label_identity")
            if not 0 < p.stat().st_size < 128000:
                reject("source_label_size_invalid")
            seen.add(p.stem)
            result[(split, p.stem)] = p
    if len(result) != 333:
        reject("source_coverage_mismatch")
    return result


def parse_text(text):
    rows = J10W._rows(text)
    lines = text.splitlines()
    indices = [i for i, s in enumerate(lines) if s.strip()]
    if len(rows) != len(indices):
        reject("source_line_count_mismatch")
    return lines, indices, rows


def inventory_preflight(root: Path):
    inventory = labels_inventory(root)
    flagged = groups = exact = 0
    split_totals = {}
    for split in SPLITS:
        split_flagged = split_groups = 0
        for (partition, stem), path in inventory.items():
            if partition != split:
                continue
            _, _, rows = parse_text(path.read_text(encoding="utf-8"))
            by_class = defaultdict(list)
            for cls, bbox in rows:
                if cls < 32:
                    by_class[cls].append(bbox)
            n = sum(max(0, len(boxes)-1) for boxes in by_class.values())
            if n:
                flagged += 1
                groups += n
                split_flagged += 1
                split_groups += n
            for boxes in by_class.values():
                for a in range(len(boxes)):
                    for b in range(a + 1, len(boxes)):
                        if boxes[a] == boxes[b]:
                            exact += 1
        split_totals[split] = {
            "label_files": SPLITS[split],
            "flagged_images": split_flagged,
            "extra_same_fdi_labels": split_groups}
    if (flagged, groups, exact) != (28, 31, 1):
        reject("pinned_academic_duplicate_census_changed")
    return {
        "schema": SCHEMA,
        "status": "PINNED_ACADEMIC_TEXT_ONLY_PREFLIGHT_PASS",
        "source_label_files": 333,
        "flagged_images": flagged,
        "extra_same_fdi_labels": groups,
        "exact_duplicate_pairs": exact,
        "by_split": split_totals,
        "jpeg_pixels_read": False,
        "source_modified": False,
        "patient_independence_proven": False,
        "commercial_rights_cleared": False,
        "case_ids_or_coordinates_logged": False}


def validate_manifest(data):
    if (not isinstance(data, dict) or data.get("schema") != MANIFEST_SCHEMA
            or data.get("source_commit") != PIN
            or data.get("reviewed_cases") != 28
            or data.get("reviewed_pairs") != 6):
        reject("private_manifest_schema_or_pin_mismatch")
    changes = data.get("relabels")
    unresolved = data.get("unresolved")
    drops = data.get("exact_duplicate_deletions")
    if (not isinstance(changes, list) or len(changes) != 21
            or not isinstance(unresolved, list) or len(unresolved) != 10
            or not isinstance(drops, list) or len(drops) != 1):
        reject("private_manifest_decision_census_mismatch")
    if len({r.get("case") for r in changes if isinstance(r, dict)}) != 17:
        reject("private_manifest_relabel_case_count_mismatch")
    if len({r.get("case") for r in unresolved if isinstance(r, dict)}) != 10:
        reject("private_manifest_unresolved_case_count_mismatch")
    signatures = set()
    for r in changes:
        if not isinstance(r, dict) or r.get("case") not in range(1, 29):
            reject("invalid_private_relabel")
        if (r.get("split") not in SPLITS or
                not isinstance(r.get("stem"), str) or
                not r["stem"].isdecimal()):
            reject("invalid_relabel_source")
        if (r.get("from_fdi") not in FDI or
                r.get("to_fdi") not in FDI or
                r["from_fdi"] == r["to_fdi"]):
            reject("invalid_relabel_class")
        bbox = r.get("expected_bbox")
        if (not isinstance(bbox, list) or len(bbox) != 4
                or any(type(x) not in (float, int) or not 0 < x <= 1
                       for x in bbox)):
            reject("invalid_relabel_geometry")
        key = (r["split"], r["stem"], r["from_fdi"], tuple(bbox))
        if key in signatures:
            reject("duplicate_private_relabel_target")
        signatures.add(key)
    d = drops[0]
    if (not isinstance(d, dict) or d.get("fdi") not in FDI
            or d.get("split") not in SPLITS
            or not isinstance(d.get("stem"), str)
            or not d["stem"].isdecimal()):
        reject("invalid_exact_dedupe_instruction")
    if not isinstance(d.get("expected_bbox"), list) or len(d["expected_bbox"]) != 4:
        reject("invalid_exact_dedupe_bbox")
    if any(not isinstance(r, dict) or
           r.get("reason") not in ("class_unknown", "multi_box_choice_unresolved")
           for r in unresolved):
        reject("invalid_unresolved_instruction")


def closebox(a, b):
    return all(abs(float(x)-float(y)) <= TOL for x, y in zip(a, b))


def locate_once(rows, fdi, bbox):
    matches = [i for i, (cls, box) in enumerate(rows)
               if cls == FDI[fdi] and closebox(box, bbox)]
    if len(matches) != 1:
        reject("relabel_box_not_uniquely_identified")
    return matches[0]


def evaluate_private(root: Path, manifest: dict):
    validate_manifest(manifest)
    inventory = labels_inventory(root)
    groups = defaultdict(list)
    for r in manifest["relabels"]:
        key = r["split"], r["stem"]
        if key not in inventory:
            reject("clinical_label_source_missing")
        groups[key].append(r)
    drop = manifest["exact_duplicate_deletions"][0]
    drop_key = drop["split"], drop["stem"]
    if drop_key not in inventory or drop_key in groups:
        reject("conflicting_deduplication_source")
    replacements = {}
    colliding = 0
    edited = 0
    for key, records in groups.items():
        text = inventory[key].read_text(encoding="utf8")
        lines, indices, rows = parse_text(text)
        planned = [cls for cls, _ in rows]
        visited = set()
        for rec in records:
            index = locate_once(rows, rec["from_fdi"], rec["expected_bbox"])
            if index in visited:
                reject("repeated_clinician_box")
            visited.add(index)
            planned[index] = FDI[rec["to_fdi"]]
        totals = Counter(planned)
        # Each tooth class ought to label at most one box in this image after
        # replacement. Do NOT silently overwrite/duplicate an existing class.
        if any(totals[FDI[r["to_fdi"]]] > 1 for r in records):
            colliding += 1
            continue
        for rec in records:
            idx = locate_once(rows, rec["from_fdi"], rec["expected_bbox"])
            line_idx = indices[idx]
            tokens = lines[line_idx].split()
            tokens[0] = str(FDI[rec["to_fdi"]])
            lines[line_idx] = " ".join(tokens)
            edited += 1
        replacements[key] = "\n".join(lines) + "\n"
    raw = inventory[drop_key].read_text(encoding="utf8")
    lines, indices, rows = parse_text(raw)
    duplicates = [i for i, (cls, bbox) in enumerate(rows)
                  if cls == FDI[drop["fdi"]] and closebox(bbox, drop["expected_bbox"])]
    if len(duplicates) != 2 or rows[duplicates[0]][1] != rows[duplicates[1]][1]:
        reject("exact_duplicate_witness_changed")
    del lines[indices[duplicates[1]]]
    replacements[drop_key] = "\n".join(lines) + "\n"
    return {
        "schema": SCHEMA,
        "status": "PRIVATE_CLINICIAN_STAGING_PRECHECK",
        "source_label_files": 333,
        "clinician_relabels_requested": 21,
        "clinician_relabels_safe": edited,
        "clinician_relabels_blocked_by_existing_target_class": 21-edited,
        "case_files_with_target_collision": colliding,
        "exact_duplicate_entries_safe_to_remove": 1,
        "unresolved_clinician_cases": 10,
        "original_files_changed": False,
        "source_image_ids_logged": False,
        "ready_for_clinical_training": False,
        "commercial_rights_cleared": False,
        "patient_independence_proven": False}, replacements


def stage_private(root: Path, output: Path, replacements: dict):
    inventory = labels_inventory(root)
    if output.exists() or output.is_symlink():
        reject("private_output_must_not_exist")
    if (output.resolve().is_relative_to(root.resolve()) or
            root.resolve().is_relative_to(output.resolve())):
        reject("unsafe_private_output_location")
    for ancestor in (output.resolve(), *output.resolve().parents):
        if (ancestor / ".git").exists():
            reject("staging_in_git_repository_forbidden")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        output.mkdir(mode=0o700)
        for split in SPLITS:
            (output / split).mkdir(mode=0o700)
        for (split, stem), path in inventory.items():
            text = replacements.get((split, stem))
            if text is None:
                text = path.read_text(encoding="utf8")
            new = output / split / (stem + ".txt")
            with new.open("x", encoding="utf8") as f:
                f.write(text)
            new.chmod(0o600)
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--labels-dir", type=Path, required=True)
    p.add_argument("--private-manifest", type=Path)
    p.add_argument("--stage-private", type=Path)
    args = p.parse_args()
    try:
        if (os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
                and (args.private_manifest is not None or args.stage_private is not None)):
            reject("private_clinician_manifest_forbidden_on_public_ci")
        preflight = inventory_preflight(args.labels_dir)
        if args.private_manifest is None:
            if args.stage_private is not None:
                reject("private_manifest_required_for_staging")
            print("J13_AGGREGATE_PREFLIGHT_ONLY=" + json.dumps(preflight, sort_keys=True))
            return 0
        manifest_path = args.private_manifest
        if (manifest_path.is_symlink() or not manifest_path.is_file()
                or manifest_path.stat().st_size > 200000):
            reject("unsafe_private_manifest_input")
        manifest = json.loads(manifest_path.read_text(encoding="utf8"))
        report, replacements = evaluate_private(args.labels_dir, manifest)
        if args.stage_private is not None:
            if report["clinician_relabels_blocked_by_existing_target_class"]:
                reject("private_staging_blocked_on_relabel_conflicts")
            stage_private(args.labels_dir, args.stage_private, replacements)
            report["status"] = "PRIVATE_VERSIONED_STAGING_CREATED_NOT_CLINICAL_RELEASE"
            report["private_corrected_text_files"] = 333
        print("J13_AGGREGATE_PRIVATE_QA_ONLY=" + json.dumps(report, sort_keys=True))
        return 0
    except (J13Error, J10W.TriageError, J10W.J10Q.LabelAuditError,
            UnicodeError, OSError, ValueError, TypeError, KeyError):
        print(json.dumps({
            "schema": SCHEMA, "status": "FAIL_CLOSED_NO_MEDIA_OR_IDENTIFIERS"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
