#!/usr/bin/env python3
"""LOT05/J11A — Cross-partition JPEG fingerprint audit of academic AKUDENTAL.

This is a research-only data-leakage SCREEN, NOT proof of patient independence.
Runs in a disposable runner from a pinned academic Git checkout.
No image pixels, paths, IDs, hashes, pair examples, or image files in stdout.
No model training, clinical use, commercial clearance or app data migration.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

SPLITS = {"train": 266, "val": 33, "test": 34}
THRESHOLDS = (0, 2, 4, 6)
MAX_BYTES = 25_000_000
SCHEMA = "digital-crown-lot05-j11a-image-split-fingerprint-screen-v1"


class AuditError(ValueError):
    pass


@dataclass(frozen=True)
class Fingerprint:
    split: str
    # No patient or source filename fields; only in-memory hashes.
    jpeg_sha256: str
    pixels_sha256: str
    dhash64: int
    mirror_dhash64: int


def _reject(message: str) -> None:
    raise AuditError(message)


def _dhash(rgb, mirrored: bool = False) -> int:
    from PIL import Image, ImageOps

    if mirrored:
        rgb = ImageOps.mirror(rgb)
    thumb = rgb.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    values = list(thumb.getdata())
    result = 0
    for y in range(8):
        for x in range(8):
            result = (result << 1) | (values[y * 9 + x] > values[y * 9 + x + 1])
    return result


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint_jpeg(path: Path, split: str) -> Fingerprint:
    from PIL import Image, ImageOps, UnidentifiedImageError
    if split not in SPLITS:
        _reject("unapproved_split")
    if path.suffix.lower() != ".jpg" or path.is_symlink() or not path.is_file():
        _reject("unsafe_or_missing_jpeg")
    size = path.stat().st_size
    if size < 100 or size > MAX_BYTES:
        _reject("invalid_jpeg_size")
    file_digest = _file_hash(path)
    try:
        with Image.open(path) as original:
            if original.format != "JPEG":
                _reject("file_format_not_jpeg")
            w, h = original.size
            if not (64 <= w <= 8000 and 64 <= h <= 8000 and w * h <= 40_000_000):
                _reject("unsafe_image_dimensions")
            # Decoding occurs only in-memory in the temporary research runner.
            oriented = ImageOps.exif_transpose(original)
            rgb = oriented.convert("RGB")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        _reject("invalid_image_decode")
    try:
        width, height = rgb.size
        digest = hashlib.sha256()
        digest.update(width.to_bytes(4, "big"))
        digest.update(height.to_bytes(4, "big"))
        digest.update(rgb.tobytes())
        dhash = _dhash(rgb)
        mirror = _dhash(rgb, mirrored=True)
    finally:
        rgb.close()
    return Fingerprint(split, file_digest, digest.hexdigest(), dhash, mirror)


def compare_fingerprints(items: list[Fingerprint]) -> dict:
    buckets: dict[str, list[Fingerprint]] = {name: [] for name in SPLITS}
    for item in items:
        if item.split not in buckets:
            _reject("unexpected_split")
        buckets[item.split].append(item)
    result = {"schema": SCHEMA, "status": "RESEARCH_SCREEN_ONLY_NOT_PATIENT_INDEPENDENCE",
              "fingerprints_evaluated": len(items),
              "split_counts": {k: len(v) for k, v in buckets.items()},
              "cross_partition": {},
              "patient_level_independence_established": False,
              "source_level_independence_established": False,
              "commercial_rights_established": False,
              "expert_visual_adjudication_completed": False,
              "raw_ids_hashes_pixels_or_pair_details_emitted": False,
              "does_not_establish_patient_identity_or_consent": True}
    labels = list(SPLITS)
    for pos, first in enumerate(labels):
        for second in labels[pos + 1:]:
            total = 0
            byte_matches = 0
            pixel_matches = 0
            near = Counter()
            normal_near = Counter()
            mirror_near = Counter()
            min_dist = 64
            for a in buckets[first]:
                for b in buckets[second]:
                    total += 1
                    byte_matches += (a.jpeg_sha256 == b.jpeg_sha256)
                    pixel_matches += (a.pixels_sha256 == b.pixels_sha256)
                    d_normal = (a.dhash64 ^ b.dhash64).bit_count()
                    d_mirror = (a.dhash64 ^ b.mirror_dhash64).bit_count()
                    smallest = min(d_normal, d_mirror)
                    min_dist = min(min_dist, smallest)
                    for t in THRESHOLDS:
                        if smallest <= t:
                            near[t] += 1
                        if d_normal <= t:
                            normal_near[t] += 1
                        if d_mirror <= t:
                            mirror_near[t] += 1
            result["cross_partition"][first + "_vs_" + second] = {
                "pairs_compared": total,
                "identical_jpeg_file_pairs": byte_matches,
                "identical_decoded_pixel_pairs": pixel_matches,
                "min_hamming_distance_64bit_dhash_or_mirror": min_dist if total else None,
                "candidate_pairs_by_dhash_threshold": {
                    str(k): near[k] for k in THRESHOLDS
                },
                "candidate_normal_pairs_by_threshold": {
                    str(k): normal_near[k] for k in THRESHOLDS
                },
                "candidate_mirror_pairs_by_threshold": {
                    str(k): mirror_near[k] for k in THRESHOLDS
                },
                "similarity_candidates_are_not_confirmed_duplicate_patients": True,
            }
    return result


def audit_source(image_root: Path, labels_root: Path) -> dict:
    if image_root.is_symlink() or labels_root.is_symlink():
        _reject("symlink_source_directory")
    if not image_root.is_dir() or not labels_root.is_dir():
        _reject("source_layout_missing")
    all_ids: set[str] = set()
    items: list[Fingerprint] = []
    for split, expected in SPLITS.items():
        source_split = labels_root / split
        if source_split.is_symlink() or not source_split.is_dir():
            _reject("split_labels_invalid")
        labels = sorted(source_split.glob("*.txt"))
        if len(labels) != expected:
            _reject("split_size_mismatch")
        for label in labels:
            if label.is_symlink() or not label.stem.isdecimal() or label.stat().st_size > 128_000:
                _reject("source_label_invalid")
            stem = label.stem
            if stem in all_ids:
                _reject("cross_split_filename_overlap")
            all_ids.add(stem)
            # Do not read annotation content; J10W and J10S already verified it.
            path = image_root / (stem + ".jpg")
            items.append(fingerprint_jpeg(path, split))
    if len(items) != 333:
        _reject("coverage_incomplete")
    return compare_fingerprints(items)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--labels-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit_source(args.images_dir, args.labels_dir)
    except (AuditError, OSError, ValueError):
        print(json.dumps({"schema": SCHEMA, "status": "FAIL_CLOSED"}))
        return 1
    print("J11A_AGGREGATE_ONLY=" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
