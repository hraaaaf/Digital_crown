"""Source-specific geometry recovery for historical COM/Tweed/Ricketts debt.

Geometry only. This module may expose a raw patient measurement when every
source-specific construction dependency is satisfied, but it never activates a
norm, classification, finding, diagnosis, indication, or treatment.

Scientific invariant:
    landmark != construction != measurement != interpretation != diagnosis

No-substitution invariant:
    generic runtime landmarks/lines must never silently replace a historical
    source-specific construction.
"""
from __future__ import annotations

import math
from typing import Mapping, Optional, Tuple

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
)

Point = Tuple[float, float]
_EPS = 1e-12

# Ricketts, Angle Orthodontist 1981, 51(2):115-150.
# The paper specifies the mandibular-plane indicator as true Frankfort to
# Sub.Go.-M. and explicitly distinguishes true Frankfort from ear-rod proxying.
# These points are therefore represented source-specifically rather than by
# relabelling generic SRPose38 Po/Or/Go/Me.
RICKETTS_1981_FMA_SOURCE = "doi:10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2"
RICKETTS_1981_FMA_DEFINITION_ID = "RICKETTS_1981_FMA_TRUE_FH_SUBGO_ME_V2"
RICKETTS_1981_FMA_METHOD_ID = "RICKETTS_1981_FMA_DEG_V2"
RICKETTS_1981_FMA_REQUIRED_LANDMARKS = (
    "RickettsTruePo",
    "RickettsTrueOr",
    "RickettsSubGo",
    "RickettsMe",
)

# Tweed remains intentionally blocked. Existing Go-Me / Go-Gn convenience lines
# are not promoted to historical source-exact geometry without a locked tracing
# contract for Tweed Frankfort and the mandibular lower-border tangent.
TWEED_SOURCE_EXACT_GEOMETRY_BLOCKER = {
    "status": "BLOCKED_SOURCE_SPECIFIC_GEOMETRY",
    "source_refs": (
        "doi:10.1016/0096-6347(46)90001-4",
        "TWEED_1954_FMIA_PRIMARY",
    ),
    "mandibular_plane_requirement": "source_specific_lower_border_tangent",
    "frankfort_requirement": "source_specific_tweed_frankfort_construction",
    "forbidden_substitutions": (
        "Go-Me_as_Tweed_mandibular_plane",
        "Go-Gn_as_Tweed_mandibular_plane",
        "generic_Po-Or_as_source_exact_Tweed_FH_without_proof",
    ),
    "next_exact": (
        "Version a clinician-audited source-specific Tweed tracing contract for "
        "the historical Frankfort reference and mandibular lower-border tangent "
        "before materializing Tweed FMA/IMPA."
    ),
}


def _finite_points(*points: Point) -> bool:
    return all(math.isfinite(value) for point in points for value in point)


def _acute_line_angle_deg(v1: Point, v2: Point) -> Optional[float]:
    """Return the acute/non-oriented angle between two geometric lines."""

    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if not all(math.isfinite(v) for v in (*v1, *v2, len1, len2)):
        return None
    if len1 <= _EPS or len2 <= _EPS:
        return None
    cosine = abs((v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2))
    cosine = max(0.0, min(1.0, cosine))
    value = math.degrees(math.acos(cosine))
    return value if math.isfinite(value) else None


def ricketts_1981_fma_deg_v2(
    true_po: Point,
    true_or: Point,
    subgo: Point,
    me: Point,
) -> Optional[float]:
    """Angle between Ricketts true Frankfort and Subgonion-Menton lines."""

    if not _finite_points(true_po, true_or, subgo, me):
        return None
    return _acute_line_angle_deg(
        (true_or[0] - true_po[0], true_or[1] - true_po[1]),
        (me[0] - subgo[0], me[1] - subgo[1]),
    )


def _require_mapping_identity(key: str, item: LandmarkEvidence) -> None:
    if item.landmark_id != key:
        raise ValueError(f"Landmark mapping key {key} resolves to {item.landmark_id}")


def _require_validated_source_manual(key: str, item: LandmarkEvidence) -> None:
    _require_mapping_identity(key, item)
    if item.origin != LandmarkOrigin.MANUAL:
        raise ValueError(
            f"{key} must be a source-specific MANUAL landmark; generic automatic "
            "landmarks must not substitute"
        )
    if item.evidence_status != EvidenceStatus.CLINICIAN_VALIDATED:
        raise ValueError(f"{key} requires CLINICIAN_VALIDATED evidence status")
    if not item.validated_by or item.validated_at is None:
        raise ValueError(f"{key} requires clinician/operator audit metadata")
    if item.availability_status != AvailabilityStatus.AVAILABLE:
        raise ValueError(f"{key} must be AVAILABLE")


def materialize_ricketts_1981_fma_construction(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    construction_namespace: str,
) -> ConstructionEvidence:
    """Materialize Ricketts 1981 FMA only from explicit source-specific points."""

    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    refs: list[str] = []
    missing: list[str] = []
    source_images: set[str] = set()

    for landmark_id in RICKETTS_1981_FMA_REQUIRED_LANDMARKS:
        item = landmarks.get(landmark_id)
        if item is None:
            missing.append(landmark_id)
            continue
        _require_validated_source_manual(landmark_id, item)
        refs.append(item.evidence_id)
        source_images.add(item.source_image_ref)

    geometry: dict[str, object] = {
        "analysis": "RICKETTS_1981",
        "kind": "source_specific_cephalometric_angle",
        "required_landmark_ids": list(RICKETTS_1981_FMA_REQUIRED_LANDMARKS),
        "coordinate_space": "source_image_pixels",
        "frankfort_plane": "RickettsTruePo-RickettsTrueOr",
        "mandibular_plane": "RickettsSubGo-RickettsMe",
        "source_references": [RICKETTS_1981_FMA_SOURCE],
        "forbidden_substitutions": [
            "SRPose38_Po-Or_for_Ricketts_true_FH",
            "Go_for_RickettsSubGo",
            "Go-Me_for_RickettsSubGo-RickettsMe",
            "Go-Gn_for_RickettsSubGo-RickettsMe",
        ],
        "patient_classification_active": False,
    }

    availability = AvailabilityStatus.AVAILABLE
    if missing:
        availability = AvailabilityStatus.NOT_COMPUTABLE
    elif len(source_images) != 1:
        availability = AvailabilityStatus.INVALID
    else:
        true_po = landmarks["RickettsTruePo"]
        true_or = landmarks["RickettsTrueOr"]
        subgo = landmarks["RickettsSubGo"]
        me = landmarks["RickettsMe"]
        value = ricketts_1981_fma_deg_v2(
            (true_po.x, true_po.y),
            (true_or.x, true_or.y),
            (subgo.x, subgo.y),
            (me.x, me.y),
        )
        if value is None:
            availability = AvailabilityStatus.INVALID
        else:
            geometry["computed_angle_deg"] = value
            geometry["source_image_ref"] = next(iter(source_images))
            geometry["manual_landmark_evidence_refs"] = refs
            geometry["manual_landmark_validators"] = {
                key: landmarks[key].validated_by
                for key in RICKETTS_1981_FMA_REQUIRED_LANDMARKS
            }

    return ConstructionEvidence(
        construction_id=f"{construction_namespace}:{RICKETTS_1981_FMA_DEFINITION_ID}",
        definition_id=RICKETTS_1981_FMA_DEFINITION_ID,
        definition_version="2",
        landmark_refs=refs,
        missing_landmark_ids=missing,
        geometry=geometry,
        evidence_refs=refs,
        availability_status=availability,
    )


def adapt_ricketts_1981_fma_measurement(
    construction: ConstructionEvidence,
    *,
    measurement_namespace: str,
) -> MeasurementEvidence:
    """Expose the raw source-specific FMA only; never apply a historical norm."""

    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")
    if construction.definition_id != RICKETTS_1981_FMA_DEFINITION_ID:
        raise ValueError("Ricketts 1981 FMA adapter received a different construction")

    availability = construction.availability_status
    value: Optional[float] = None
    if availability == AvailabilityStatus.AVAILABLE:
        computed = construction.geometry.get("computed_angle_deg")
        if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
            raise ValueError("Available Ricketts 1981 FMA construction lacks finite angle")
        value = float(computed)
    elif availability != AvailabilityStatus.INVALID:
        availability = AvailabilityStatus.NOT_COMPUTABLE

    return MeasurementEvidence(
        measurement_id=f"{measurement_namespace}:RICKETTS_1981_FMA",
        analysis_id="RICKETTS_1981",
        method_id=RICKETTS_1981_FMA_METHOD_ID,
        method_version="2",
        value=value,
        unit="deg",
        construction_refs=[construction.construction_id],
        requires_calibration=False,
        evidence_refs=[construction.construction_id],
        availability_status=availability,
    )
