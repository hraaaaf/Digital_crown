#!/usr/bin/env python3
"""Read-only research evidence for 2 public Aariz exports; NOT a clinical verdict."""
import argparse
import hashlib
import io
import json
import math
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MIRROR = "ea6678cd8ba62b615d909ecb1065023ea73eb827"
ROOT = "Aariz_dataset/Aariz/test"
ORIGIN = "https://raw.githubusercontent.com/Annagdy/CNN-CVM/" + MIRROR + "/"
SOFT_POG = "Pog" + chr(96)
POINTS = ("Po", "Or", "Co", "Gn", SOFT_POG, "Ls", "Li", "A", "ANS", "Me")
CASES = (
    ("veraviewepocs2d", "cl6cc2n5k405307716g0393xo", "jpeg",
     "b476ccd8cdebee3f3d4dcc9f611f2c89caa2ec0d",
     "fa5bdf3841aea69bd74efcfdfba3bfdeb1fc00e4",
     "2186adfdbc2b9be821c8a4da5cddcf3572f00907", (959, 1198)),
    ("promax2d", "cl5lc0isd1298072u53z31emu", "jpg",
     "b99415aef13a4c294555b78bb43c70a4f3fb3c27",
     "fcc0d7f1eaad54c3e2099dafa230530d0e0e5cbd",
     "3447e8ef82d3aae2ef1fe11e28a6bbde22b4815d", (1256, 1592)),
)

def blob_hash(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def get_verified(path, expected_sha):
    url = ORIGIN + urllib.parse.quote(path, safe="/")
    error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "DC-Research-AarizOverlay/1.0"})
            with urllib.request.urlopen(request, timeout=35) as resp:
                data = resp.read()
            assert blob_hash(data) == expected_sha, f"SOURCE_BLOB_MISMATCH {path}"
            return data, url
        except (OSError, TimeoutError) as exc:
            error = exc
            time.sleep(attempt + 1)
    raise RuntimeError(f"SOURCE_UNAVAILABLE {path}: {error}")

def read_labels(case_id, team, sha, size):
    path = f"{ROOT}/Annotations/Cephalometric Landmarks/{team}/{case_id}.json"
    data, url = get_verified(path, sha)
    obj = json.loads(data)
    assert obj["ceph_id"] == case_id and len(obj["landmarks"]) == 29
    result = {}
    for landmark in obj["landmarks"]:
        sym, val = landmark["symbol"], landmark["value"]
        assert sym not in result, "DUPLICATE_SYMBOL"
        x, y = val["x"], val["y"]
        assert math.isfinite(x) and math.isfinite(y)
        assert 0 <= x < size[0] and 0 <= y < size[1], "OUT_OF_IMAGE_BOUNDS"
        result[sym] = (x, y)
    assert set(POINTS).issubset(result)
    return result, url

def crop_zoom(canvas, consensus, symbols, banner=90, margin=100):
    coords = [consensus[k] for k in symbols]
    left = max(0, int(min(x for x, y in coords) - margin))
    top = max(0, int(min(y for x, y in coords) + banner - margin))
    right = min(canvas.width, int(max(x for x, y in coords) + margin))
    bottom = min(canvas.height, int(max(y for x, y in coords) + banner + margin))
    assert right > left and bottom > top
    img = canvas.crop((left, top, right, bottom))
    return img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)

def create_overlay(image, jr, sr, label):
    banner = 90
    canvas = Image.new("RGB", (image.width, image.height + banner), "#15202a")
    canvas.paste(image.convert("RGB"), (0, banner))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    captions = (
        f"AARIZ {label} -- RESEARCH ONLY, NOT CLINICAL APPROVAL",
        "Junior cyan | Senior orange | Consensus green -- positions require HUMAN review",
        "FH candidate Po-Or yellow | Co-Gn magenta | Lip-Pog soft blue (NOT CLINICAL LINES)",
        "Khalid et al. (2025) CC BY 4.0 -- Git mirror pinned, original DICOM unverified",
    )
    for row, caption in enumerate(captions):
        draw.text((10, 8 + row * 20), caption, font=font, fill="white")
    consensus = {k: (math.ceil((jr[k][0] + sr[k][0]) / 2),
                     math.ceil((jr[k][1] + sr[k][1]) / 2)) for k in jr}
    def xy(k):
        return consensus[k][0], consensus[k][1] + banner
    for k1, k2, color in (("Po", "Or", "#ffff50"), ("Co", "Gn", "#ff50cc"),
                          ("Ls", SOFT_POG, "#70b5ff")):
        draw.line([xy(k1), xy(k2)], fill=color, width=2)
    for k in POINTS:
        for pts, color, radius in ((jr, "#25e6fc", 4), (sr, "#ffac4a", 4),
                                   (consensus, "#a6ff6b", 2)):
            x, y = round(pts[k][0]), round(pts[k][1]) + banner
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=color, width=2)
        x, y = xy(k)
        draw.text((x+8, y-10), k.replace(chr(96), "-soft"), font=font,
                  fill="#bdff80", stroke_width=2, stroke_fill="#15202a")
    return canvas, consensus

def main(destination, expected_head):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert head == expected_head, f"WRONG_HEAD {head} != {expected_head}"
    destination.mkdir(parents=True, exist_ok=True)
    reports = []
    for label, case_id, ext, img_sha, jr_sha, sr_sha, dims in CASES:
        image_path = f"{ROOT}/Cephalograms/{case_id}.{ext}"
        data, image_url = get_verified(image_path, img_sha)
        with Image.open(io.BytesIO(data)) as opened:
            assert opened.size == dims and opened.getexif().get(274, 1) == 1
            source = opened.convert("RGB")
        jr, jr_url = read_labels(case_id, "Junior Orthodontists", jr_sha, dims)
        sr, sr_url = read_labels(case_id, "Senior Orthodontists", sr_sha, dims)
        assert set(jr) == set(sr) and len(jr) == 29
        annotated, avg = create_overlay(source, jr, sr, label)
        folder = destination / label
        folder.mkdir(parents=True, exist_ok=True)
        annotated.save(folder / "full_overlay.png", optimize=True)
        crop_zoom(annotated, avg, ("Po", "Or", "Co")).save(folder / "posterior_zoom.png", optimize=True)
        crop_zoom(annotated, avg, ("Gn", "Me", SOFT_POG, "Ls", "Li")).save(folder / "profile_zoom.png", optimize=True)
        differences = [math.hypot(jr[k][0]-sr[k][0], jr[k][1]-sr[k][1]) for k in jr]
        reports.append({
            "device": label, "image_url": image_url, "image_blob_sha": img_sha,
            "junior_annotations_url": jr_url, "junior_blob_sha": jr_sha,
            "senior_annotations_url": sr_url, "senior_blob_sha": sr_sha,
            "image_dimensions_px": list(dims), "points_per_group": 29,
            "out_of_bounds": 0, "max_inter_group_difference_px": round(max(differences), 3),
            "clinical_landmark_validation": "NOT_EVALUABLE",
            "native_dicom_scale": "NOT_EVALUABLE",
            "agent_independent_run": "NOT_RUN",
            "approved_by_clinician": False,
        })
        print(f"SOURCE_IMAGE_PASS {label}: {dims[0]}x{dims[1]}, 29+29 points, Git SHA VERIFIED")
    manifest = {"product_head": head, "official_dataset_doi": "10.6084/m9.figshare.27986417.v1",
                "source": f"unofficial pinned Git mirror @{MIRROR}", "license": "CC BY 4.0",
                "clinical_validation": False, "cases": reports}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    (destination / "README.md").write_text(
        "# Aariz source-overlay study — RESEARCH ONLY\n\n"
        "Source attribution: Khalid et al. (2025), Aariz Cephalometric Dataset, Figshare, "
        "https://doi.org/10.6084/m9.figshare.27986417.v1 (CC BY 4.0).\n"
        "Original image and landmark files were fetched from an unofficial mirror, "
        "but checked against immutable Git blob SHA values. Equality to the official "
        "Figshare ZIP is NOT verified.\n\n"
        "This artifact contains annotated public images for human inspection only. "
        "Junior/senior group marks and candidate line segments DO NOT establish anatomical "
        "validity, native pixel spacing, normative measurements or clinical approval. "
        "The original images and landmark coordinates are NOT committed to the application repo.\n",
        encoding="utf-8")
    assert len(reports) == 2
    print("AARIZ_OVERLAY_LAB_PASS: 2 public images, 4 annotation JSONs, 116 in-bounds markers; clinical HOLD")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    main(args.output, args.expected_head)
