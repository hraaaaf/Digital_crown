"""Local-only, non-clinical FACAD ↔ Digital Crown numeric comparison.

This FUE-0 helper reuses existing DC geometry; it never runs FACAD or proves
that a declared input actually came from the vendor or from a real patient.
No API, DB, PDF, registration, network, files written or clinical activation.
Input must remain on an authorized workstation. Do not commit case files.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from backend.services.cephalo_facad_wits_candidate import (
    facad_tweed_wits_bisected_ol_mm_candidate_v1,
)
from backend.services.cephalo_mcnamara_geometry import (
    mcnamara_ans_me_mm_v1,
    mcnamara_co_a_mm_v1,
    mcnamara_co_gn_mm_v1,
)

_SCHEMA = "CEPH_V1_FACAD_DC_LOCAL_SAME_TRACE_V1"
_METRICS = ("Wits", "Co-A", "Co-Gn", "ANS-Me")
_SHA = re.compile(r"^[0-9a-f]{64}$")


def _number(value: Any, *, positive: bool = False) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and (not positive or value > 0)
    )


def _point(value: Any) -> tuple[float, float] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2 and all(_number(v) for v in value):
        return (value[0], value[1])
    return None


def _not_comparable(reason: str) -> dict[str, Any]:
    return {
        "status": "NOT_COMPARABLE",
        "reason": reason,
        "facad_mm": None,
        "digital_crown_mm": None,
        "delta_mm": None,
    }


def compare_local_case(payload: Any) -> dict[str, Any]:
    """Compare declared values only; every numeric match remains non-clinical.

    Matching hashes/attestations are *declared* metadata, NOT proof of an actual
    vendor export. Clinical review and original artifact verification stay outside
    this script. Missing evidence fails closed, never silently treated as zero.
    """
    output: dict[str, Any] = {
        "schema_version": _SCHEMA,
        "scope": "LOCAL_DECLARED_VALUES_ONLY_NOT_CLINICALLY_VALIDATED",
        "clinical_validation_available": False,
        "same_trace_numeric_parity_observed": False,
        "measurements": {},
    }

    def reject_all(reason: str) -> dict[str, Any]:
        output["measurements"] = {name: _not_comparable(reason) for name in _METRICS}
        output["measurements"]["Z"] = _not_comparable("HOLD_Z_ORIENTATION")
        return output

    if not isinstance(payload, dict) or payload.get("schema_version") != _SCHEMA:
        return reject_all("SCHEMA_INVALID")
    facad, dc = payload.get("facad"), payload.get("digital_crown")
    if not isinstance(facad, dict) or not isinstance(dc, dict):
        return reject_all("SOURCE_MISSING")
    facad_case, dc_case = facad.get("same_trace_case_id"), dc.get("same_trace_case_id")
    if not (isinstance(facad_case, str) and facad_case.strip() and facad_case == dc_case):
        return reject_all("SAME_TRACE_ID_MISMATCH")
    facad_image, dc_image = facad.get("source_image_sha256"), dc.get("source_image_sha256")
    if not (
        isinstance(facad_image, str)
        and _SHA.fullmatch(facad_image)
        and facad_image == dc_image
    ):
        return reject_all("SOURCE_IMAGE_HASH_MISMATCH")
    if not all(
        isinstance(source.get("export_sha256"), str)
        and _SHA.fullmatch(source["export_sha256"])
        and isinstance(source.get("version"), str)
        and bool(source["version"].strip())
        for source in (facad, dc)
    ):
        return reject_all("EXPORT_ATTESTATION_MISSING")
    if facad.get("unit") != "mm":
        return reject_all("FACAD_UNIT_NOT_MM")
    if dc.get("coordinate_frame_verified") is not True:
        return reject_all("DC_COORDINATE_FRAME_UNVERIFIED")
    calibration = dc.get("calibration")
    if (
        not isinstance(calibration, dict)
        or calibration.get("verified") is not True
        or not isinstance(calibration.get("source"), str)
        or not calibration["source"].strip()
        or not _number(calibration.get("mm_per_pixel"), positive=True)
    ):
        return reject_all("DC_NATIVE_CALIBRATION_UNVERIFIED")
    tolerance = payload.get("tolerance_mm")
    if not _number(tolerance) or tolerance < 0:
        return reject_all("TOLERANCE_MISSING_OR_INVALID")
    values, points = facad.get("values_mm"), dc.get("landmarks_px")
    if not isinstance(values, dict) or not isinstance(points, dict):
        return reject_all("VALUES_OR_LANDMARKS_MISSING")

    scale = calibration["mm_per_pixel"]

    def evaluate(name: str, computed: float | None) -> None:
        observed = values.get(name)
        if computed is None or not _number(computed) or not _number(observed):
            output["measurements"][name] = _not_comparable("MEASUREMENT_EVIDENCE_INCOMPLETE")
            return
        delta = computed - observed
        output["measurements"][name] = {
            "status": "NUMERIC_MATCH" if abs(delta) <= tolerance else "DIFFERENT",
            "reason": "DECLARED_VALUES_COMPARISON_ONLY",
            "facad_mm": observed,
            "digital_crown_mm": computed,
            "delta_mm": delta,
        }

    if dc.get("manual_olp_verified") is not True:
        output["measurements"]["Wits"] = _not_comparable("MANUAL_OLP_NOT_ATTESTED")
    else:
        evaluate(
            "Wits",
            facad_tweed_wits_bisected_ol_mm_candidate_v1(
                olp=_point(points.get("olp")),
                u1_incisal=_point(points.get("u1_incisal")),
                l1_incisal=_point(points.get("l1_incisal")),
                a=_point(points.get("a")),
                b=_point(points.get("b")),
                mm_per_pixel=scale,
            ),
        )
    if dc.get("co_reference_equivalence_verified") is not True:
        for name in ("Co-A", "Co-Gn"):
            output["measurements"][name] = _not_comparable("CONDYLION_REFERENCE_NOT_ATTESTED")
    else:
        evaluate(
            "Co-A",
            mcnamara_co_a_mm_v1(_point(points.get("co_anatomic")), _point(points.get("a")), scale),
        )
        evaluate(
            "Co-Gn",
            mcnamara_co_gn_mm_v1(_point(points.get("co_anatomic")), _point(points.get("gn")), scale),
        )
    evaluate("ANS-Me", mcnamara_ans_me_mm_v1(_point(points.get("ans")), _point(points.get("me")), scale))
    # Sector orientation still requires the clinician's explicit decision.
    # In particular, an acute v1 value MUST NOT be auto-matched against FACAD Z.
    output["measurements"]["Z"] = _not_comparable("HOLD_Z_ORIENTATION")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Local declared-value FACAD/DC comparison (NOT clinical parity proof)"
    )
    parser.add_argument("--input-json", required=True, type=Path, help="local restricted-access JSON; never commit")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        print(json.dumps({"status": "INPUT_REJECTED", "reason": "UNREADABLE_OR_INVALID_JSON"}))
        return 2
    # Deliberately never print file paths, case IDs, source images, raw exports or landmarks.
    print(json.dumps(compare_local_case(payload), sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
