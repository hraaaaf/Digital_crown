"""Build a local-only, source-locked image-pixel workbook for two PUBLIC JPEGs.

G12 doesn't annotate automatically or validate any landmarks/scale/orientation.
Generated HTML + two public JPEGs stay local; CI uploads text QA only.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from pathlib import Path

from scripts.cephalo_r23g11_public_radiograph_smoke import REGISTRY, smoke, load
from scripts.cephalo_r23g10_annotation_intake import G9_REL

TEMPLATE = "docs/audits/g12_atlas33_public_pixel_workbook.template.html"
TOKEN = "/*__SOURCE_CATALOG__*/"
PROFILE = "RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1"
SCHEMA = "CEPHALO_R23G12_PUBLIC_PIXEL_ANNOTATION_DRAFT_V1"
PXL = "ORIGINAL_IMAGE_PIXEL_X_RIGHT_Y_DOWN"
CASE_KEYS = {"source_case", "source_image_sha256", "source_image_dimensions_px",
             "coordinate_system", "landmarks", "missing_source_specific_ids",
             "annotation_status", "image_orientation_verified", "calibration_mm_per_pixel",
             "is_ricketts_goldset_reference"}
TOP_KEYS = {"schema_version", "scope", "operator_token", "source_profile_id",
            "clinical_release", "independent_expert_authentication",
            "expert_goldset_ready", "atlas33_measurements_validated",
            "reference_group", "note", "cases"}

def require(predicate, explanation):
    if not predicate:
        raise ValueError(explanation)

def exact(value, keys, what):
    require(isinstance(value, dict) and set(value) == keys,
            "Unknown or missing " + what + " keys")
    return value

def build_catalog(repo_root, result):
    ledger = load(repo_root / REGISTRY)
    matrix = load(repo_root / G9_REL)
    ids = matrix["identities_without_strict_mapping"]
    require(matrix["profile_id"] == PROFILE and
            matrix["clinical_release"] is False and
            matrix["semantic_aliasing_authorized"] is False and
            len(ids) == 21 and ids == sorted(set(ids)),
            "G9 source identity drift")
    result_rows = {r["id"]: r for r in result["cases"]}
    rows = []
    for src in ledger["cases"]:
        measured = result_rows[src["id"]]
        require(measured["original_public_jpeg_sha1_match"] is True and
                measured["g10_public_case_rejected"] is True and
                measured["image_header_dimensions_match"] is True,
                "G11 must verify actual original public image bytes")
        rows.append({
            "id": src["id"], "author": src["author"], "year": src["year"],
            "filename": src["filename"], "page": src["page"],
            "license": src["license"], "sha1": src["sha1"],
            "sha256": measured["image_sha256"],
            "width": src["width"], "height": src["height"],
        })
    return {"profile_id": PROFILE,
            "source_scope": "TWO_PUBLIC_IMAGES_NONCLINICAL_PIXEL_DRAFT",
            "clinical_release": False,
            "required_source_ids": ids, "cases": rows}

def build_workbook(repo_root: Path, input_dir: Path, output_dir: Path):
    result = smoke(repo_root, input_dir)
    require(result["case_count"] == 2 and
            result["aariz_goldset_cases_admitted"] == 0 and
            result["atlas33_clinical_measurements_validated"] == 0 and
            result["clinical_release"] is False,
            "G11 source proof not accepted")
    catalog = build_catalog(repo_root, result)
    template = (repo_root / TEMPLATE).read_text(encoding="utf-8")
    require(template.count(TOKEN) == 1, "Missing/duplicated inert source injection token")
    # Fixed repository-controlled strings only; HTML script context is escaped.
    js_catalog = json.dumps(catalog, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = template.replace(TOKEN, js_catalog)
    require(output_dir.resolve() != repo_root.resolve() and
            output_dir.resolve() != input_dir.resolve() and
            not output_dir.resolve().is_relative_to(repo_root.resolve()),
            "Output must stay outside the repository and source directory")
    if output_dir.exists():
        require(output_dir.is_dir() and not any(output_dir.iterdir()),
                "Refuse overwriting a nonempty output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    images = output_dir / "images"
    images.mkdir()
    for case in catalog["cases"]:
        shutil.copyfile(input_dir / case["filename"], images / case["filename"])
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    proof = {
        "schema_version": "CEPHALO_R23G12_PUBLIC_WORKBOOK_BUILD_PROOF_V1",
        "source_scope": "PUBLIC_ONLY",
        "case_count": 2,
        "source_specific_identity_count": len(catalog["required_source_ids"]),
        "image_sha256": {c["id"]: c["sha256"] for c in catalog["cases"]},
        "coordinates_created": 0,
        "clinical_release": False,
        "expert_reference_verified": False,
        "mm_calibration_verified": False,
        "anatomical_orientation_verified": False,
        "user_interface_requires_manual_click": True,
    }
    (output_dir / "source-only-build-proof.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return catalog, proof

def verify_draft(draft: dict, catalog: dict):
    """Fail-closed STRUCTURAL validation of a public demo JSON, not clinical acceptance."""
    exact(draft, TOP_KEYS, "draft")
    require(draft["schema_version"] == SCHEMA and
            draft["scope"] == "PUBLIC_WIKIMEDIA_IMAGES_ONLY" and
            draft["source_profile_id"] == PROFILE and
            isinstance(draft["operator_token"], str) and
            re.fullmatch(r"[A-Za-z0-9_-]{3,48}", draft["operator_token"]),
            "Draft identity/version/operator drift")
    require(draft["clinical_release"] is False and
            draft["independent_expert_authentication"] is False and
            draft["expert_goldset_ready"] is False and
            type(draft["atlas33_measurements_validated"]) is int and
            draft["atlas33_measurements_validated"] == 0 and
            draft["reference_group"] == "NO_REFERENCE" and
            draft["note"] == "Manual unverified pixels only; no clinical use or expert verification",
            "Falsified clinical/expert reference claim")
    originals = {s["id"]: s for s in catalog["cases"]}
    ids = catalog["required_source_ids"]
    require(isinstance(draft["cases"], list) and len(draft["cases"]) == 2 and
            all(isinstance(c, dict) for c in draft["cases"]),
            "Exactly two public cases required")
    seen = set()
    point_count = 0
    for case in draft["cases"]:
        exact(case, CASE_KEYS, "case")
        ref = originals.get(case["source_case"]) if isinstance(case["source_case"], str) else None
        require(ref and case["source_case"] not in seen,
                "Unknown/duplicated public source")
        seen.add(case["source_case"])
        require(case["source_image_sha256"] == ref["sha256"] and
                case["source_image_dimensions_px"] ==
                {"width": ref["width"], "height": ref["height"]} and
                case["coordinate_system"] == PXL,
                "Image bytes, dimensions or pixel orientation drift")
        require(case["annotation_status"] == "MANUAL_DRAFT_UNVERIFIED" and
                case["image_orientation_verified"] is False and
                case["calibration_mm_per_pixel"] is None and
                case["is_ricketts_goldset_reference"] is False,
                "Clinical coordinate/calibration promotion forbidden")
        positions = case["landmarks"]
        require(isinstance(positions, dict) and set(positions).issubset(set(ids)),
                "Unexpected point alias or non-object landmarks")
        require(case["missing_source_specific_ids"] ==
                [label for label in ids if label not in positions],
                "Missing source-specific point list out of sync")
        for point in positions.values():
            exact(point, {"x", "y"}, "point")
            x, y = point["x"], point["y"]
            require(all(type(v) in (float, int) and math.isfinite(v) for v in (x, y)) and
                    0 <= x <= ref["width"] and 0 <= y <= ref["height"],
                    "Nonfinite or out-of-image coordinate")
        point_count += len(positions)
    require(len(seen) == 2, "Missing source cases")
    return {
        "schema_version": "CEPHALO_R23G12_PIXEL_DRAFT_QA_V1",
        "cases_checked": 2,
        "manual_draft_pixel_points": point_count,
        "valid_structure_only": True,
        "anatomical_expertise_verified": False,
        "clinical_release": False,
        "atlas33_measurements_validated": 0,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--input-dir", type=Path, required=True,
                        help="Folder containing exact public anug.jpg and challiyan.jpg")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="An empty local folder OUTSIDE the repository")
    args = parser.parse_args()
    _, proof = build_workbook(args.repo_root, args.input_dir, args.output_dir)
    print(json.dumps(proof, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
