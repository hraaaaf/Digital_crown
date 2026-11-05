#!/usr/bin/env python3
"""Full-uncropped review of genuine 38-point authenticated Cephalo UI imports.

Nonclinical research visualization. This draws the EXACT persisted pixel-space
coordinates over the unchanged, byte-verified public JPEG. No inferred landmark,
scale, normative range, diagnostic conclusion, or FACAD parity is invented.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

EXPECTED_MODEL = "a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb"
EXPECTED_SOURCES = {
    "anug": ("anug.jpg", "ede247cdc573719cd25c928110543978f962f43e296adb1f875cdd45b3fc7ee6", "ANUG", "Cephalometric radiograph.JPG"),
    "challiyan": ("challiyan.jpg", "98c6384dd9cc392ac54bf365173e522a4860ce55a64b8b15e87485dbcc30371b", "Challiyan", "A lateral cephalogram without true vertical.jpg"),
}

def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()

def draw_one(case: dict, meta: dict, source_dir: Path, output_dir: Path, head: str) -> dict:
    film = case.get("radio")
    if film not in EXPECTED_SOURCES:
        raise ValueError("Unexpected source radio")
    filename, sha_expected, author, source_title = EXPECTED_SOURCES[film]
    raw = (source_dir / filename).read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != sha_expected or case.get("source_image_sha256") != actual_sha:
        raise ValueError(f"Original public source does not match pinned SHA256: {film}")
    if case.get("source_name") != filename or case.get("inference_mode") != "SOTA_ONNX_38":
        raise ValueError(f"Analysis bridge provenance mismatch: {film}")
    if case.get("is_calibrated") is not False or case.get("mm_per_pixel") is not None:
        raise ValueError(f"Cannot assert verified scale: {film}")
    points = case.get("landmarks")
    if not isinstance(points, list) or len(points) != 38:
        raise ValueError(f"Expected 38 real points: {film}")
    if len({p.get("id") for p in points}) != 38:
        raise ValueError(f"Duplicate landmark identifier: {film}")
    with Image.open(source_dir / filename) as im:
        if im.format != "JPEG":
            raise ValueError("Image was not a JPEG")
        image = im.convert("RGB")
    iw, ih = image.size
    if iw != case.get("source_width") or ih != case.get("source_height"):
        raise ValueError(f"Source pixel dimensions mismatch: {film}")
    for p in points:
        if not (isinstance(p.get("id"), str) and p["id"] and isinstance(p.get("x"), (int, float))
                and isinstance(p.get("y"), (int, float)) and math.isfinite(p["x"]) and math.isfinite(p["y"])):
            raise ValueError(f"Unverifiable landmark: {film}")
        if not (0 <= p["x"] < iw and 0 <= p["y"] < ih):
            raise ValueError(f"Out-of-film ONNX point: {film}: {p['id']}")
    # Native source pixels occupy their ORIGINAL 1:1 geometry. No resampling.
    panel = 780 if iw > 1400 else 570
    work_height = max(ih, 1420)
    top = 152
    footer = 155
    left = 24
    right_start = left + iw + 30
    canvas = Image.new("RGB", (right_start + panel + 20, top + work_height + footer), "#101a29")
    canvas.paste(image, (left, top))
    dr = ImageDraw.Draw(canvas)
    dr.rectangle((left - 1, top - 1, left + iw, top + ih), outline="#c8d8eb", width=2)
    large = font(42 if iw > 1400 else 33)
    medium = font(25 if iw > 1400 else 22)
    small = font(21 if iw > 1400 else 17)
    dr.text((left, 20), f"TELECRANE {film.upper()}  |  38 REPERES ONNX", font=large, fill="#f4f7fc")
    dr.text((left, 77), f"Source: {author} / Wikimedia Commons  |  CC BY-SA 4.0  |  original {iw} x {ih} px",
            font=medium, fill="#adbacd")
    dr.text((left, 117), "POINTS AUTOMATIQUES - NON EXPERTISES, PAS DE MESURES MM",
            font=small, fill="#ffd38a")
    dr.text((right_start + 16, top + 12), "Repere  |  pixels image originale", font=medium, fill="#f4f7fc")
    label_size = 25 if iw > 1400 else 19
    fnum = font(label_size)
    r = 18 if iw > 1400 else 15
    collisions = []
    for idx, pt in enumerate(points, 1):
        px, py = left + pt["x"], top + pt["y"]
        # The small central dot always stays on the exact ONNX coordinate.
        dr.ellipse((px - 4, py - 4, px + 4, py + 4), fill="#ffcc44", outline="#14212e", width=1)
        # Find a nearby location to place the index without hiding the true point.
        candidates = [(0, -40), (42, -12), (-42, -12), (0, 41), (38, 35),
                      (-38, 35), (65, 0), (-65, 0), (52, -44), (-52, -44),
                      (70, 37), (-70, 37)]
        chosen = None
        for dx, dy in candidates:
            x, y = px + dx, py + dy
            if left + r <= x <= left + iw - r and top + r <= y <= top + ih - r:
                if all((x - qx)**2 + (y - qy)**2 >= (r * 2 + 4)**2 for qx, qy in collisions):
                    chosen = x, y
                    break
        if chosen is None:
            chosen = px, py
        x, y = chosen
        collisions.append((x, y))
        dr.line(((px, py), (x, y)), fill="#f8cb65", width=2)
        dr.ellipse((x - r, y - r, x + r, y + r), fill="#073a56", outline="#fff3bd", width=2)
        label = str(idx)
        bb = dr.textbbox((0, 0), label, font=fnum)
        dr.text((x - (bb[2] - bb[0]) / 2, y - (bb[3] - bb[1]) / 2 - bb[1]),
                label, font=fnum, fill="#ffffff")
    row_height = (work_height - 120) / 38
    for idx, pt in enumerate(points, 1):
        y = top + 66 + (idx - 1) * row_height
        if idx % 2:
            dr.rectangle((right_start, y - 2, right_start + panel - 10, y + row_height - 3),
                         fill="#1d2a3a")
        dr.text((right_start + 16, y), f"{idx:02d}  {pt['id']}", font=small, fill="#e4edfa")
        dr.text((right_start + panel - 250, y), f"{pt['x']:.1f}, {pt['y']:.1f}", font=small, fill="#ffcc76")
    foot_y = top + work_height + 16
    dr.text((left, foot_y), "SOURCE PHOTO INCHANGEE. Les cercles sont un CALQUE a partir du GET authentifie SRPose38.",
            font=small, fill="#f9dec0")
    dr.text((left, foot_y + 34), f"Produit/test: {head[:12]}  |  Modele: {EXPECTED_MODEL[:12]}  |  Source SHA256: {actual_sha[:18]}...",
            font=small, fill="#b8c4d8")
    dr.text((left, foot_y + 68), "Aucune calibration certifiee | aucune verite terrain | aucun diagnostic | pas de parite FACAD.",
            font=small, fill="#ffbf9a")
    name = f"fullfilm-{film}-38points-numerotes.png"
    target = output_dir / name
    canvas.save(target, format="PNG", optimize=True)
    return {
        "radio": film, "author": author, "source_title": source_title, "source_sha256": actual_sha,
        "source_pixels": [iw, ih], "study_id": case.get("study_id"), "landmarks_drawn": 38,
        "landmarks_outside": 0, "annotated_png": name,
        "annotated_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "svg_app_proof": f"04-ui-svg-{film}.png",
        "clinical_accuracy_validated": False,
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--sources", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    head = report.get("head")
    if not isinstance(head, str) or len(head) != 40 or head != __import__("os").environ.get("PRODUCT_HEAD"):
        raise ValueError("Product HEAD mismatch")
    if report.get("clinical_authority") is not False or report.get("model_sha256") != EXPECTED_MODEL:
        raise ValueError("Unverified science/model")
    if report.get("source") != "EXACT_SHA_AUTHENTICATED_GET_AFTER_REAL_UI_IMPORT":
        raise ValueError("Source is not authoritative authenticated GET")
    cases = report.get("cases", [])
    if not isinstance(cases, list) or len(cases) != 2 or {c.get("radio") for c in cases} != set(EXPECTED_SOURCES):
        raise ValueError("Missing one of the two independent studies")
    if cases[0].get("study_id") == cases[1].get("study_id"):
        raise ValueError("A/B study identity collision")
    args.output.mkdir(parents=True, exist_ok=True)
    outputs = [draw_one(case, report, args.sources, args.output, head) for case in cases]
    index = {"head": head, "model_sha256": EXPECTED_MODEL, "clinical_accuracy_validated": False,
             "scientific_ground_truth_comparison": "NOT_PERFORMED", "calibration": "NOT_AVAILABLE",
             "format": "original full native JPEG dimensions plus detached, numbered, annotated proof",
             "cases": outputs}
    (args.output / "fullfilm-review-index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print("CEPH_FULLFILM_38POINTS_2_PUBLIC_ORIGINALS_REVIEW_ONLY_PASS")
    print(json.dumps({"head": head, "images": [x["annotated_png"] for x in outputs]}, indent=2))

if __name__ == "__main__":
    main()
