#!/usr/bin/env python3
"""J11C GitHub Actions: academic visual READINESS, never clinical adjudication.

All third-party JPEGs stay in a disposable runner. Only fixed-schema aggregates
are printed: no names, paths, coordinates, image pixels, hashes or galleries.
"""
from __future__ import annotations
import argparse
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).parent
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj

J10X = load("j11c_j10x", "lot05_j10x_local_private_fdi_visual_reviewer.py")
J11A = load("j11c_j11a", "lot05_j11a_akudental_cross_split_image_fingerprint.py")
J11B = load("j11c_j11b", "lot05_j11b_private_candidate_pair_roster.py")
SCHEMA = "digital-crown-j11c-visual-readiness-aggregate-v1"

class ReadinessError(ValueError):
    pass

def pixel_extent(size: tuple[int,int], box: tuple[float,float,float,float]) -> tuple[int,int]:
    width, height = size
    cx, cy, bw, bh = box
    if width < 64 or height < 64 or not all(math.isfinite(v) for v in box):
        raise ReadinessError("invalid_dimensions_or_box")
    if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < bw <= 1 and 0 < bh <= 1):
        raise ReadinessError("invalid_normalized_bbox")
    x0 = max(0, math.floor((cx - bw/2)*width))
    y0 = max(0, math.floor((cy - bh/2)*height))
    x1 = min(width, math.ceil((cx + bw/2)*width))
    y1 = min(height, math.ceil((cy + bh/2)*height))
    if x1 <= x0 or y1 <= y0:
        raise ReadinessError("empty_source_region")
    return x1-x0, y1-y0

def image_info(path: Path) -> tuple[int,int,int]:
    from PIL import Image, UnidentifiedImageError
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".jpg":
        raise ReadinessError("invalid_source_path")
    if not 100 <= path.stat().st_size <= 25_000_000:
        raise ReadinessError("invalid_source_bytes")
    try:
        with Image.open(path) as im:
            if im.format != "JPEG" or not (64 <= im.width <= 8000 and 64 <= im.height <= 8000):
                raise ReadinessError("unsupported_source_image")
            if im.width * im.height > 40_000_000:
                raise ReadinessError("too_many_pixels")
            orientation = int(im.getexif().get(274, 1))
            im.load()
            return im.width, im.height, orientation
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        raise ReadinessError("image_decode_failed") from None

def run(images_dir: Path, labels_dir: Path) -> dict:
    if (images_dir.is_symlink() or labels_dir.is_symlink() or
        not images_dir.is_dir() or not labels_dir.is_dir()):
        raise ReadinessError("source_roots_unavailable")
    flagged = J10X.flagged_cases(labels_dir)
    if len(flagged) != 28:
        raise ReadinessError("review_case_count_changed")
    region = Counter()
    smallest = None
    extras = 0
    for split, stem, repeated in flagged:
        width, height, orientation = image_info(images_dir/(stem+".jpg"))
        region["images_decoded"] += 1
        region["non_identity_exif"] += orientation != 1
        rows = J10X.J10W._rows((labels_dir/split/(stem+".txt")).read_text(encoding="utf-8"))
        for fdi, n in repeated.items():
            extras += n - 1
            boxes = [box for cid,box in rows if cid < 32 and J10X.J10W.FDA[cid] == fdi]
            if len(boxes) != n:
                raise ReadinessError("label_consistency_changed")
            for box in boxes:
                side = min(pixel_extent((width,height),box))
                smallest = side if smallest is None else min(smallest,side)
                region["source_regions_pixel_checked"] += 1
                region["regions_short_side_le_32px"] += side <= 32
    if extras != 31:
        raise ReadinessError("repeated_label_count_changed")
    # Reuse the established J11A/J11B fingerprint selection, never export it.
    records = []
    seen = set()
    for split, expected in J11A.SPLITS.items():
        directory = labels_dir/split
        if directory.is_symlink() or not directory.is_dir():
            raise ReadinessError("source_partition_invalid")
        labels = sorted(directory.glob("*.txt"))
        if len(labels) != expected:
            raise ReadinessError("partition_count_changed")
        for label in labels:
            stem = label.stem
            if label.is_symlink() or not stem.isdecimal() or stem in seen:
                raise ReadinessError("source_identity_changed")
            seen.add(stem)
            records.append((split,stem,J11A.fingerprint_jpeg(images_dir/(stem+".jpg"),split)))
    if len(records) != 333:
        raise ReadinessError("source_coverage_changed")
    pairs = J11B.candidates(records)
    if len(pairs) != 6:
        raise ReadinessError("pair_candidate_count_changed")
    pair_stats = Counter()
    for pair in pairs:
        a = image_info(images_dir/(pair["source_image_stem_a"]+".jpg"))
        b = image_info(images_dir/(pair["source_image_stem_b"]+".jpg"))
        pair_stats["sources_decoded"] += 1
        pair_stats["different_dimensions"] += a[:2] != b[:2]
        pair_stats["non_identity_exif"] += a[2] != 1 or b[2] != 1
        pair_stats["mirror_preferred"] += pair["dhash_hamming_mirrored"] < pair["dhash_hamming_normal"]
    return {
        "schema":SCHEMA,"status":"ACADEMIC_VISUAL_READINESS_ONLY_HUMAN_GATE_OPEN",
        "academic_source_images":len(records),
        "flagged_images_decoded":region["images_decoded"],
        "repeated_label_excess_instances":extras,
        "repeated_label_regions_pixel_checked":region["source_regions_pixel_checked"],
        "regions_short_side_le_32px":region["regions_short_side_le_32px"],
        "minimum_repeated_region_short_side_px":smallest,
        "flagged_images_non_identity_exif":region["non_identity_exif"],
        "candidate_pairs_source_decoded":pair_stats["sources_decoded"],
        "pairs_with_different_source_dimensions":pair_stats["different_dimensions"],
        "pairs_with_non_identity_exif":pair_stats["non_identity_exif"],
        "pairs_mirror_preferred":pair_stats["mirror_preferred"],
        "human_image_adjudications":0,"human_pair_adjudications":0,
        "patient_independence_proven":False,"annotations_modified":False,
        "commercial_rights_verified":False,"media_or_identifiers_exported":False,
        "gallery_or_artifact_created":False,
    }

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-dir",type=Path,required=True)
    parser.add_argument("--labels-dir",type=Path,required=True)
    args=parser.parse_args()
    try:
        summary=run(args.images_dir,args.labels_dir)
    except (ReadinessError,J10X.ReviewError,J10X.J10W.TriageError,
            J11A.AuditError,OSError,ValueError):
        print(json.dumps({"schema":SCHEMA,"status":"FAIL_CLOSED"}))
        return 1
    print("J11C_AGGREGATE_ONLY="+json.dumps(summary,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
