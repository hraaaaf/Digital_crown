"""P3 non-clinical probe: execute REAL Digital Crown canonical V2 typed adapter.

The FACAD->DC landmark mappings below are *hypotheses for an educational
calculation*, NOT clinically verified identity mappings. Original FACAD
coordinates are in millimetres and are treated as arbitrary geometry-unit
positions: only ANGLES are considered. No fabricated pixel calibration,
Po/Or/Frankfort, image orientation, or patient metadata may enter this probe.

Pydantic is the only external runtime requirement. Load original checked-out
Digital Crown packages while bypassing backend.__init__, whose database and
application initialization must not run in a GitHub math-only audit.
"""
from __future__ import annotations

import importlib
import math
import sys
import types
from pathlib import Path

from audit import cephalo_facad_robert_public_ci as public

ROOT = Path(__file__).resolve().parents[1]
STUDY_REF = "FACAD_PUBLIC_DEMO_GEOMETRY_UNVERIFIED_LANDMARK_IDENTITIES"
CANDIDATE_CROSSWALK = {
    "Ii": "L1_incisal",
    "Iia": "L1_apex",
    "Is": "U1_incisal",
    "Isa": "U1_apex",
    "A": "A",
    "Pog": "Pog_hard",
}
REQUIRED_CANONICAL_METHODS = {
    "ILi/A-Pog": "RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2",
    "ILs/A-Pog": "RICKETTS_U1_APOG_INCLINATION_CANONICAL_DEG_V2",
}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _real_typed_adapter():
    """Import original canonical V2 source with an inert package namespace.

    This deliberately does NOT execute the application's SQLAlchemy,
    media, clinical endpoints, patient DB or startup side effects.
    """
    for label, relative in (
        ("backend", "backend"),
        ("backend.schemas", "backend/schemas"),
        ("backend.services", "backend/services"),
    ):
        root = (ROOT / relative).resolve(strict=True)
        namespace = sys.modules.get(label)
        if namespace is None:
            namespace = types.ModuleType(label)
            namespace.__path__ = [str(root)]
            sys.modules[label] = namespace
        else:
            require(list(getattr(namespace, "__path__", [])) == [str(root)],
                    "backend namespace modified; refuse arbitrary module import")
    evidence = importlib.import_module("backend.schemas.cephalo_evidence")
    adapter = importlib.import_module("backend.services.cephalo_canonical_analysis_v2")
    bridge = importlib.import_module("backend.services.cephalo_canonical_method_bridge")
    return evidence, adapter, bridge


def assess(fixture: dict) -> dict:
    # Executing this contract is NOT authorizing the crosswalk or the full runtime.
    result = public.validate_fixture(fixture)
    require(result["clinical_no_go"] is True and
            result["clinical_numeric_parities_verified"] == 0,
            "educational fixture promoted to clinical authority")
    require(fixture["coordinate_system"] ==
            "FACAD_EXPORTED_ORIGINAL_SAGITTAL_VERTICAL_MM_UNSPECIFIED_ORIENTATION" and
            fixture["coordinate_rounding_mm"] == 0.1,
            "FACAD coordinate source precision or orientation changed")
    coords = fixture["points_mm"]
    require(set(CANDIDATE_CROSSWALK).issubset(coords),
            "missing incisor landmarks or hard skeletal endpoints")
    require("P" not in coords and "Or" not in coords and "Po" not in coords,
            "FACAD demo was changed: review authentic Frankfort orientation")
    evidence, canonical, method_bridge = _real_typed_adapter()
    landmarks = {}
    for vendor_name, dc_id in CANDIDATE_CROSSWALK.items():
        x, y = coords[vendor_name]
        require(type(x) in (int,float) and type(y) in (int,float) and
                math.isfinite(x) and math.isfinite(y),
                "invalid educational coordinate")
        landmarks[dc_id] = evidence.LandmarkEvidence(
            evidence_id="provisional_facad_study_" + dc_id,
            landmark_id=dc_id, x=float(x), y=float(y),
            source_image_ref=STUDY_REF, origin=evidence.LandmarkOrigin.MANUAL,
            evidence_status=evidence.EvidenceStatus.OBSERVED,
            evidence_refs=[STUDY_REF],
        )
    typed = canonical.materialize_canonical_analysis_v2_measurements(
        measurement_namespace="FACAD_ROBERT_EDUCATIONAL_UNVERIFIED",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions={},
        image_orientation=None,
    )
    require(type(typed) is list and typed, "canonical V2 adapter did not run")
    rows = []
    for vendor_label, expected_method in REQUIRED_CANONICAL_METHODS.items():
        matches = [m for m in typed if m.method_id == expected_method]
        require(len(matches) == 1, "missing/duplicate exact canonical Ricketts adapter method")
        item = matches[0]
        require(method_bridge.canonical_measurement_id_for_method(expected_method) ==
                ("M_RICKETTS_L1_APOG_INCLINATION_DEG_V1" if vendor_label == "ILi/A-Pog"
                 else "M_RICKETTS_U1_APOG_INCLINATION_DEG_V1"),
                "source-locked clinical method bridge changed")
        require(item.analysis_id == "RICKETTS" and item.method_version == "2"
                and item.unit == "deg" and not item.requires_calibration and
                item.availability_status == evidence.AvailabilityStatus.AVAILABLE and
                item.value is not None and math.isfinite(item.value),
                "typed adapter did not produce a valid canonical angle")
        vendor_value = fixture["facad_values"]["32F"][vendor_label]["value"]
        require(abs(item.value - public.dc.raw_helpers(
                    {n:tuple(p) for n,p in coords.items()})[vendor_label]) < 1e-10,
                "canonical V2 result differs from checked-out math-only helper")
        rows.append({
            "facad_factor": vendor_label,
            "facad_display_deg": vendor_value,
            "dc_canonical_method_id": expected_method,
            "dc_typed_adapter_deg": round(item.value, 6),
            "raw_delta_deg": round(item.value - vendor_value, 6),
            "landmark_identity_proven": False,
            "source_image_orientation_proven": False,
            "clinical_parity": False,
        })
    # This probe must NOT upgrade the third candidate merely because the
    # CRANIOM angular helper was executed in the previous research stage.
    return {
        "status": "P3_TYPED_CANONICAL_V2_TWO_ANGLES_EDUCATIONAL_ONLY",
        "canonical_v2_typed_adapter_executed": True,
        "facad_operator_crosswalk_validated": False,
        "clinical_runtime_calibration_proven": False,
        "complete_analysis_runtime_executed": False,
        "clinical_parity_verified": 0,
        "clinical_no_go": True,
        "rows": rows,
    }


def main() -> int:
    import json
    try:
        fixture = json.loads(public.FIXTURE.read_text(encoding="utf-8"))
        public.read_checked_fixture(public.FIXTURE)
        result = assess(fixture)
    except (ValueError, KeyError, TypeError, OSError, ImportError,
            AssertionError, json.JSONDecodeError) as exc:
        print("FACAD_P3_TYPED_ADAPTER=FAIL_CLOSED_" + type(exc).__name__)
        return 2
    print("FACAD_P3_TYPED_ADAPTER=PRODUCTION_CANONICAL_V2_TWO_ANGLES_EXECUTED")
    print("FACAD_P3_CANONICAL_ANGLE_COUNT=" + str(len(result["rows"])))
    print("FACAD_P3_ANATOMICAL_MAPPING=UNVERIFIED")
    print("FACAD_P3_CLINICAL_PARITIES=0")
    print("CLINICAL_NO_GO=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
