#!/usr/bin/env python3
"""J10X private visual-review overlays for AKUDENTAL's duplicate-FDI alerts.

Must be run by an authorized human on a LOCAL PRIVATE computer only.
Outputs patient-image-derived annotated PNGs: NEVER use in GitHub Actions,
upload to Notion/GitHub/ChatGPT, or serve over a public URL.
No automatic decisions about any duplicate tooth annotation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import importlib.util
import json
import os

P = Path(__file__).with_name("lot05_j10w_akudental_duplicate_fdi_root_cause.py")
SPEC = importlib.util.spec_from_file_location("j10w_reviewer", P)
assert SPEC and SPEC.loader
J10W = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(J10W)

SCHEMA = "digital-crown-j10x-local-private-fdi-review-v1"


class ReviewError(ValueError):
    pass


def flagged_cases(labels_dir: Path) -> list[tuple[str, str, dict[str, int]]]:
    """Return PRIVATE file stems for human review. Never log this list."""
    if labels_dir.is_symlink() or not labels_dir.is_dir():
        raise ReviewError("labels_dir_invalid")
    found = []
    for split, count in J10W.SPLITS.items():
        root = labels_dir / split
        if root.is_symlink() or not root.is_dir():
            raise ReviewError("split_dir_invalid")
        files = sorted(root.glob("*.txt"))
        if len(files) != count:
            raise ReviewError("source_split_count_mismatch")
        for path in files:
            if not path.stem.isdecimal() or path.is_symlink():
                raise ReviewError("unsafe_file")
            rows = J10W._rows(path.read_text(encoding="utf-8"))
            n = Counter(J10W.FDA[c] for c, _ in rows if c < 32)
            dup = {k: v for k, v in n.items() if v > 1}
            if dup:
                found.append((split, path.stem, dup))
    return found


def private_review(images_dir: Path, labels_dir: Path, output_dir: Path,
                   *, max_dimension: int = 1800) -> dict:
    """Draw bbox overlays ONLY into user-approved private directory."""
    if not 480 <= max_dimension <= 2400:
        raise ReviewError("invalid_render_limit")
    if output_dir.exists() or output_dir.is_symlink():
        raise ReviewError("output_already_exists")
    if output_dir.parent.is_symlink() or not output_dir.parent.is_dir():
        raise ReviewError("output_parent_invalid")
    if images_dir.is_symlink() or not images_dir.is_dir():
        raise ReviewError("images_dir_invalid")
    # Validate 333 original TXT files BEFORE any image read or output write.
    J10W.audit_labels(labels_dir)
    review = flagged_cases(labels_dir)
    if len(review) != 28:
        raise ReviewError("expected_28_flagged_cases")
    # PIL is imported at runtime only; CI synthetic tests never open images.
    from PIL import Image, ImageDraw
    import math
    os.mkdir(output_dir, mode=0o700)
    annotated = 0
    for split, stem, classes in review:
        source = images_dir / f"{stem}.jpg"
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 25_000_000:
            raise ReviewError("source_image_not_safe")
        outdir = output_dir / split
        outdir.mkdir(exist_ok=True, mode=0o700)
        with Image.open(source) as orig:
            if orig.format != "JPEG" or orig.width > 6000 or orig.height > 5000:
                raise ReviewError("source_image_invalid")
            image = orig.convert("RGB")
        width, height = image.size
        factor = min(1.0, max_dimension / max(width, height))
        if factor < 1:
            image = image.resize((round(width * factor), round(height * factor)))
        iw, ih = image.size
        draw = ImageDraw.Draw(image)
        labeled = J10W._rows((labels_dir / split / (stem + ".txt")).read_text(encoding="utf-8"))
        for cid, (cx, cy, bw, bh) in labeled:
            if cid >= 32:
                continue
            fdi = J10W.FDA[cid]
            if fdi not in classes:
                continue
            x1, y1, x2, y2 = (cx-bw/2)*iw, (cy-bh/2)*ih, (cx+bw/2)*iw, (cy+bh/2)*ih
            draw.rectangle((x1, y1, x2, y2), outline=(255, 100, 30), width=4)
            draw.text((max(0, x1), max(0, y1-16)), "FDI "+fdi, fill=(255, 100, 30))
        outfile = outdir / (stem + "_private_overlay.png")
        image.save(outfile, format="PNG")
        try:
            outfile.chmod(0o600)
        except OSError:
            pass
        annotated += 1
        image.close()
    manifest = {
        "schema": SCHEMA, "status": "PRIVATE_OVERLAYS_PREPARED_HUMAN_REVIEW_PENDING",
        "images_rendered": annotated, "expert_review_completed": False,
        "annotations_modified": False, "can_publish_overlays": False,
        "source_commercial_rights_verified": False,
        "instructions": "On a private authorized station, review each PNG with source image; never submit images or case IDs to public systems.",
    }
    (output_dir / "README_REVIEW_PRIVATE.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images-dir", type=Path, required=True,
                        help="PRIVATE upstream AKUDENTAL/images directory")
    parser.add_argument("--labels-dir", type=Path, required=True,
                        help="PRIVATE upstream AKUDENTAL/folds/fold_0/labels directory")
    parser.add_argument("--private-output-dir", type=Path, required=True,
                        help="Nonexistent PRIVATE output folder, never in a Git repository")
    args = parser.parse_args()
    try:
        report = private_review(args.images_dir, args.labels_dir, args.private_output_dir)
    except (ReviewError, J10W.TriageError, J10W.J10Q.LabelAuditError, OSError):
        print(json.dumps({"schema": SCHEMA, "status": "FAIL_CLOSED"}))
        return 1
    print("J10X_PRIVATE_REVIEW_STATUS="+json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
