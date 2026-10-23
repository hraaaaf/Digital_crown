#!/usr/bin/env python3
"""J11B: local-only candidate pair manifest for expert cross-split visual review.

J11A's PUBLIC CI logs expose only aggregate counts. This companion runs ONLY
on an owner-approved private machine and writes the academic source filenames
to a local private JSON file (mode 0600) to make flagged pairs inspectable.
Never use this script in GitHub Actions or upload its output to cloud apps.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("j11a_local_for_j11b",
    HERE / "lot05_j11a_akudental_cross_split_image_fingerprint.py")
assert SPEC and SPEC.loader
J11A = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = J11A
SPEC.loader.exec_module(J11A)

SCHEMA = "digital-crown-j11b-private-cross-split-candidate-roster-v1"
MAX_HAMMING = 4


class LocalReviewError(ValueError):
    pass


def candidates(records: list[tuple[str, str, J11A.Fingerprint]]) -> list[dict]:
    """Generate PRIVATE reviewer pairs only; callers MUST NEVER log them."""
    result = []
    for i, (split_a, stem_a, a) in enumerate(records):
        for split_b, stem_b, b in records[i + 1:]:
            if split_a == split_b:
                continue
            normal = (a.dhash64 ^ b.dhash64).bit_count()
            mirrored = (a.dhash64 ^ b.mirror_dhash64).bit_count()
            if min(normal, mirrored) <= MAX_HAMMING or a.pixels_sha256 == b.pixels_sha256:
                result.append({
                    "source_split_a": split_a, "source_image_stem_a": stem_a,
                    "source_split_b": split_b, "source_image_stem_b": stem_b,
                    "dhash_hamming_normal": normal,
                    "dhash_hamming_mirrored": mirrored,
                    "exact_bytes": a.jpeg_sha256 == b.jpeg_sha256,
                    "exact_decoded_pixels": a.pixels_sha256 == b.pixels_sha256,
                    "expert_decision": "UNREVIEWED",
                    "same_patient_or_exam_proven": False,
                })
    return result


def _safe_output(destination: Path, sources: tuple[Path, Path]) -> Path:
    if destination.suffix != ".json" or destination.exists() or destination.is_symlink():
        raise LocalReviewError("private_output_must_be_new_json")
    resolved = destination.resolve(strict=False)
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise LocalReviewError("unsafe_private_output_parent")
    for ancestor in (resolved.parent, *resolved.parent.parents):
        if (ancestor / ".git").exists():
            raise LocalReviewError("review_data_in_git_checkout_refused")
    for raw in sources:
        root = raw.resolve()
        if resolved == root or root in resolved.parents or resolved in root.parents:
            raise LocalReviewError("review_data_overlaps_source_refused")
    return resolved


def run(images_dir: Path, labels_dir: Path, destination: Path) -> dict:
    dest = _safe_output(destination, (images_dir, labels_dir))
    if images_dir.is_symlink() or labels_dir.is_symlink() or not images_dir.is_dir():
        raise LocalReviewError("invalid_local_source")
    records = []
    all_stems = set()
    for split, expected in J11A.SPLITS.items():
        folder = labels_dir / split
        if folder.is_symlink() or not folder.is_dir():
            raise LocalReviewError("source_split_dir_missing")
        labels = sorted(folder.glob("*.txt"))
        if len(labels) != expected:
            raise LocalReviewError("unexpected_partition_count")
        for label in labels:
            if label.is_symlink() or not label.stem.isdecimal() or label.stem in all_stems:
                raise LocalReviewError("source_identity_not_trustworthy")
            all_stems.add(label.stem)
            path = images_dir / (label.stem + ".jpg")
            fingerprint = J11A.fingerprint_jpeg(path, split)
            records.append((split, label.stem, fingerprint))
    if len(records) != 333:
        raise LocalReviewError("source_coverage_mismatch")
    private = candidates(records)
    payload = {
        "schema": SCHEMA,
        "status": "PRIVATE_HUMAN_REVIEW_PENDING",
        "candidate_threshold_dhash64": MAX_HAMMING,
        "candidates": private,
        "not_a_patient_identity_or_provenance_check": True,
        "clinical_or_legal_clearance": False,
    }
    # Create atomically with restrictive mode; never overwrite a preexisting file.
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
    except Exception:
        try:
            dest.unlink()
        except OSError:
            pass
        raise
    return {
        "schema": SCHEMA,
        "status": "LOCAL_ROSTER_READY_NOT_ADJUDICATED",
        "candidate_pairs_count": len(private),
        "human_review_completed": False,
        "filenames_or_hashes_in_stdout": False,
        "source_commercial_rights_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--labels-dir", type=Path, required=True)
    parser.add_argument("--private-output-json", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.images_dir, args.labels_dir, args.private_output_json)
    except (LocalReviewError, J11A.AuditError, OSError, ValueError):
        print(json.dumps({"schema": SCHEMA, "status": "FAIL_CLOSED"}))
        return 1
    print("J11B_LOCAL_SUMMARY_ONLY="+json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
