"""Two original, source-locked Wikimedia lateral cephalograms: NONCLINICAL G11 smoke.

This is a real JPEG byte/dimension and G10 case-admission *rejection* test.
It does NOT locate human anatomy, calibrate the images, score measurements,
or certify a clinical reference. Images are ephemeral local/CI inputs only.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path

from scripts.cephalo_r23g10_annotation_intake import (
    G9_REL, TEMPLATE_REL, load, verify_intake,
)

REGISTRY = "docs/audits/schemas/cephalo_r23g11_public_radiographs_v1.json"
G4_CAPTURE = "frontend/scripts/capture-cephalo-r23g4-public-source-profiles.mjs"
KNOWN = {
    "anug": {
        "sha1": "2a284993c666790a72d0c004044b35a92534ce9d",
        "size": (2272, 1818), "filename": "anug.jpg",
        "author": "ANUG",
        "url": "https://upload.wikimedia.org/wikipedia/commons/6/66/Cephalometric_radiograph.JPG",
        "page": "https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG",
    },
    "challiyan": {
        "sha1": "66c74c588af3c54dfc581f8a870c5276c3427498",
        "size": (1000, 1255), "filename": "challiyan.jpg",
        "author": "Challiyan",
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/8e/A_lateral_cephalogram_without_true_vertical.jpg",
        "page": "https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg",
    },
}
SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9,
               0xCA, 0xCB, 0xCD, 0xCE, 0xCF}

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def jpeg_dimensions(image: bytes) -> tuple[int, int]:
    """Read a JPEG Start-of-Frame without decoding or interpreting anatomy."""
    require(image[:2] == b"\xff\xd8", "JPEG SOI missing")
    i = 2
    while i < len(image):
        require(image[i] == 0xFF, "JPEG marker absent/corrupt header")
        while i < len(image) and image[i] == 0xFF:
            i += 1
        require(i < len(image), "Truncated marker")
        marker = image[i]
        i += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        if marker == 0xDA:  # scan data does not carry the required SOF
            raise ValueError("JPEG scan started before a supported SOF")
        require(i + 2 <= len(image), "Truncated JPEG segment header")
        length = struct.unpack(">H", image[i:i + 2])[0]
        require(length >= 2 and i + length <= len(image),
                "Invalid/truncated JPEG segment")
        if marker in SOF_MARKERS:
            require(length >= 7, "Invalid JPEG dimensions segment")
            height = struct.unpack(">H", image[i + 3:i + 5])[0]
            width = struct.unpack(">H", image[i + 5:i + 7])[0]
            require(width > 0 and height > 0, "Invalid JPEG dimensions")
            return width, height
        i += length
    raise ValueError("JPEG SOF missing")

def validate_registry(registry: dict, g4_source: str) -> list[dict]:
    require(set(registry) == {"schema_version", "source_scope", "clinical_release",
                              "patient_reference_verified", "cases"},
            "Unexpected source ledger fields")
    require(registry["schema_version"] == "CEPHALO_R23G11_PUBLIC_RADIOGRAPH_SOURCE_LOCK_V1"
            and registry["source_scope"] == "PUBLIC_UX_AND_IMAGE_PROVENANCE_SMOKE_ONLY__NOT_AARIZ_GOLDSET"
            and registry["clinical_release"] is False
            and registry["patient_reference_verified"] is False,
            "Source cannot be promoted to goldset or clinical evidence")
    rows = registry["cases"]
    require(isinstance(rows, list) and len(rows) == 2 and
            {r.get("id") for r in rows if isinstance(r, dict)} == set(KNOWN),
            "Exactly the two approved G4 public cases are required")
    for row in rows:
        expected = KNOWN[row["id"]]
        require(set(row) == {"id", "author", "year", "page", "url", "filename",
                             "sha1", "width", "height", "license",
                             "calibration_verified", "orientation_verified",
                             "manual_landmarks_verified"}, "Source metadata drift")
        require(row["author"] == expected["author"] and
                row["sha1"] == expected["sha1"] and
                row["url"] == expected["url"] and
                row["page"] == expected["page"] and
                row["filename"] == expected["filename"] and
                (row["width"], row["height"]) == expected["size"] and
                row["license"] == "CC BY-SA 4.0" and
                row["calibration_verified"] is False and
                row["orientation_verified"] is False and
                row["manual_landmarks_verified"] is False,
                "Public source, rights or truth-claim drift")
        require(f"sha1:'{expected['sha1']}'" in g4_source and
                f"width:{row['width']},height:{row['height']}" in g4_source,
                "Original product G4 public-image lock diverged")
    return rows

def smoke(repo_root: Path, input_dir: Path):
    registry = load(repo_root / REGISTRY)
    rows = validate_registry(
        registry, (repo_root / G4_CAPTURE).read_text(encoding="utf-8")
    )
    matrix = load(repo_root / G9_REL)
    intake = load(repo_root / TEMPLATE_REL)
    # Critical: G10 must still have zero real case assignments and clinical NO-GO.
    base = verify_intake(intake, matrix)
    require(base["case_assignment_count"] == 0 and
            base["goldset_clinically_verified"] is False and
            base["source_manifest_frozen_bytes_checked"] is False,
            "G10 public demo must not establish an Aariz source case")
    checked = []
    for row in rows:
        image = (input_dir / row["filename"]).read_bytes()
        sha1 = hashlib.sha1(image).hexdigest()
        require(sha1 == row["sha1"], f"{row['id']}: public image hash mismatch")
        dims = jpeg_dimensions(image)
        require(dims == (row["width"], row["height"]),
                f"{row['id']}: public image dimensions mismatch")
        # Negative test on ACTUAL public JPEG SHA256: a public demo must never
        # enter protected LOT02/Aariz annotation assignments through a fake split.
        synthetic = copy.deepcopy(intake)
        synthetic["cases"] = [{
            "case_token": "public_" + row["id"],
            "lot02_case_id": "public_" + row["id"],
            "split": "public_demo",
            "source_image_sha256": hashlib.sha256(image).hexdigest(),
            "required_annotation_ids": matrix["identities_without_strict_mapping"],
            "assigned_blinded_experts": ["demo_alpha", "demo_beta"],
            "calibration_status": "PENDING_INDEPENDENT_VERIFICATION",
            "orientation_status": "PENDING_INDEPENDENT_VERIFICATION",
            "annotation_status": "UNANNOTATED",
        }]
        try:
            verify_intake(synthetic, matrix)
        except ValueError as exc:
            require("Untouched test split must not be exposed" in str(exc),
                    f"{row['id']}: rejected for unexpected reason: {exc}")
        else:
            raise ValueError(f"{row['id']}: public demo wrongfully accepted as LOT02")
        checked.append({
            "id": row["id"], "author": row["author"], "license": row["license"],
            "source_page": row["page"], "image_sha1": sha1,
            "image_sha256": hashlib.sha256(image).hexdigest(),
            "bytes": len(image), "width": dims[0], "height": dims[1],
            "original_public_jpeg_sha1_match": True,
            "image_header_dimensions_match": True,
            "g10_public_case_rejected": True,
            "same_image_calibration_verified": False,
            "image_anatomical_orientation_verified": False,
            "real_human_landmark_annotations": False,
            "atlas33_measurements_verified": 0,
        })
    return {
        "schema_version": "CEPHALO_R23G11_PUBLIC_RADIOGRAPH_SMOKE_V1",
        "result": "PASS_IMAGE_BYTES_AND_G10_FAIL_CLOSED__NONCLINICAL",
        "input_type": "TWO_ORIGINAL_PUBLIC_WIKIMEDIA_JPEGS",
        "case_count": len(checked),
        "aariz_goldset_cases_admitted": 0,
        "atlas33_clinical_measurements_validated": 0,
        "clinical_release": False,
        "expert_goldset_ready": False,
        "source_calibration_and_orientation_verified": False,
        "cases": checked,
        "caveat": "Image hashes and header sizes only; no real anatomy annotated, calibrated or scored.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = smoke(args.repo_root, args.input_dir)
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    print(output)

if __name__ == "__main__":
    main()
