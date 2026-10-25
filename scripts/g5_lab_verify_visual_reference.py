"""Research-only G5 visual candidate validator. No DB write or clinical import.

Usage:
  python scripts/g5_lab_verify_visual_reference.py --geometry path/to/geometry.json --image path/to/original.png

A visually approved generative illustration is NOT a clinician source-pixel tracing.
This checker confirms provenance, size, image digest and exact Bézier sampler parity,
but never changes the clinical authorization status.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "backend/services/ortho_g5_bezier_profile.py"


def load_pure_sampler():
    spec = importlib.util.spec_from_file_location("g5_lab_source_sampler", HELPER)
    if not spec or not spec.loader:
        raise RuntimeError("G5_LAB_MISSING_BEZIER_SOURCE")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assess(candidate: dict, image_path: Path) -> dict:
    mod = load_pure_sampler()
    image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
    if candidate.get("contract") != "G5_LAB_RESEARCH_VISUAL_REFERENCE_ONLY_NOT_FOR_CLINICIAN_MANUAL":
        raise ValueError("G5_LAB_NOT_RESEARCH_ONLY")
    if candidate.get("source_sha256") != image_hash:
        raise ValueError("G5_LAB_RADIO_SHA256_MISMATCH")
    if candidate.get("source_size") != [1935, 2400]:
        raise ValueError("G5_LAB_IMAGE_SIZE_MISMATCH")
    reference = candidate.get("reference", "")
    if "visual" not in reference or "clinical" not in reference:
        raise ValueError("G5_LAB_PROVENANCE_NOT_DECLARED")
    nodes = candidate.get("bezier_profile_nodes")
    samples = candidate.get("sampled_polyline_source_pixels")
    expected = mod.sample_bezier_profile(nodes, image_size=(1935, 2400))
    if samples != expected:
        raise ValueError("G5_LAB_SAMPLES_DO_NOT_MATCH_SOURCE_BEZIER")
    if len(expected) > 600:
        raise ValueError("G5_LAB_OVER_V1_SAMPLE_LIMIT")
    return {
        "status": "RESEARCH_GEOMETRY_PARITY_ONLY",
        "image_sha256": image_hash,
        "nodes": len(nodes),
        "sampled_points": len(expected),
        "budget_max": 600,
        "remaining_budget": 600 - len(expected),
        "contour_sha256": hashlib.sha256(json.dumps(expected, separators=(",", ":")).encode()).hexdigest(),
        "clinical_authority": False,
        "may_auto_approve": False,
        "may_import_as_clinician_manual": False,
        "message": "Research visual reference only. Reassess anatomy on original radiograph.",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--geometry", required=True, type=Path)
    p.add_argument("--image", required=True, type=Path)
    args = p.parse_args()
    try:
        report = assess(json.loads(args.geometry.read_text(encoding="utf-8")), args.image)
    except Exception as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
