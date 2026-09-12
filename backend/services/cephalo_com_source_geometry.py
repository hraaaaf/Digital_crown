"""Source-specific geometry recovery for historical COM/Tweed/Ricketts debt.

This module is deliberately geometry-only. It may materialize a raw patient
measurement when the source-specific construction is satisfied, but it does not
activate a norm, classification, finding, diagnosis, indication, or treatment.

Scientific invariant:
    landmark != construction != measurement != interpretation != diagnosis

No-substitution invariant:
    a convenient runtime landmark/line must never silently replace a historical
    source-specific definition.
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

RICKETTS_1981_FMA_DEFINITION_ID = "RICKETTS_1981_FMA_TRUE_FH_SUBGO_ME_V1"
RICKETTS_1981_FMA_METHOD_ID = "RICKETTS_1981_FMA_DEG_V1"
RICKETTS_1981_FMA_SOURCE = "doi:10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2"
RICKETTS_1981_FMA_REQUIRED_LANDMARKS = ("Po", "Or", "SubGo", "Me")

# Tweed remains intentionally blocked. The existing runtime Go-Me line is not a
# source-exact replacement for Tweed's lower-border tangent, and current Po-Or
# must not be silently relabelled as Tweed's historical Frankfort construction.
TWEED_SOURCE_EXACT_GEOMETRY_BLOCKER = {
    "status": "BLOCKED_SOURCE_SPECIFIC_GEOMETRY",
    "source_refs": (
        "TWEED_1954_FMIA",
        "TWEED_FOUNDATION_1946_FMA",
    ),
    "mandibular_plane_requirement": "tangent_to_lower_border_of_mandible",
    "frankfort_requirement": "source_specific_tweed_frankfort_construction",
    "forbidden_substitutions": (
        "Go-Me_as_Tweed_mandibular_plane",
        "Go-Gn_as_Tweed_mandibular_plane",
        "generic_Po-Or_as_source_exact_Tweed_FH_without_proof",
    ),
    "next_exact": (
        "Version a clinician-audited source-specific Tweed tracing contract for "
        "the historical Frankfort reference and lower-border tangent before "
        "materializing Tweed FMA/IMPA."
    ),
}


def _finite_points(*points: Point) -> bool:
    return all(math.isfinite(value) for point in points for value in point)


def _angle_deg(v1: Point, v2: Point) -> Optional[float]:
    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if not all(math.isfinite(v) for v in (*v1, *v2, len1, len2)):
        return None
    if len1 <= _EPS or len2 <= _EPS:
        return None
    cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
    cosine = max(-1.0, min(1.0, cosine))
    value = math.degrees(math.acos(cosine))
    return value if math.isfinite(value) else None


def ricketts_1981_fma_deg_v1(po: Point, or_: Point, subgo: Point, me: Point) -> Optional[float]:
    """Angle between true FH Po-Or and the Ricketts Subgonion-Menton plane."""

    if not _finite_points(po, or_, subgo, me):
        return None
    return _angle_deg(
        (or_[0] - po[0], or_[1] - po[1]),
        (me[0] - subgo[0], me[1] - subgo[1]),
    )


def _require_mapping_identity(key: str, item: LandmarkEvidence) -> None:
    if item.landmark_id != key:
        raise ValueError(f"Landmark mapping key {key} resolves to {item.landmark_id}")


def _require_validated_manual_subgo(item: LandmarkEvidence) -> None:
    if item.landmark_id != "SubGo":
        raise ValueError("Ricketts 1981 FMA requires the explicit SubGo landmark")
    if item.origin != LandmarkOrigin.MANUAL:
        raise ValueError("SubGo must be a source-specific manual landmark; Go must not substitute")
    if item.evidence_status != EvidenceStatus.CLINICIAN_VALIDATED:
        raise ValueError("Manual SubGo requires CLINICIAN_VALIDATED evidence status")
    if not item.validated_by or item.validated_at is None:
        raise ValueError("Manual SubGo requires clinician/operator audit metadata")
    if item.availability_status != AvailabilityStatus.AVAILABLE:
        raise ValueError("Validated manual SubGo must be AVAILABLE")


def materialize_ricketts_1981_fma_construction(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    construction_namespace: str,
) -> ConstructionEvidence:
    """Materialize source-specific Ricketts 1981 FMA geometry fail-closed.

    `SubGo` is absent from SRPose38, so the exact historical construction becomes
    computable only when a clinician/operator explicitly places and validates a
    manual Subgonion. A present `Go` never satisfies this dependency.
    """

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
        _require_mapping_identity(landmark_id, item)
        if landmark_id == "SubGo":
            _require_validated_manual_subgo(item)
        refs.append(item.evidence_id)
        source_images.add(item.source_image_ref)
        if item.availability_status != AvailabilityStatus.AVAILABLE:
            missing.append(landmark_id)

    geometry: dict[str, object] = {
        "analysis": "RICKETTS_1981",
        "kind": "source_specific_cephalometric_angle",
        "required_landmark_ids": list(RICKETTS_1981_FMA_REQUIRED_LANDMARKS),
        "coordinate_space": "source_image_pixels",
        "frankfort_plane": "Po-Or",
        "mandibular_plane": "SubGo-Me",
        "subgo_definition": "lower_border_of_mandibular_angle",
        "source_references": [RICKETTS_1981_FMA_SOURCE],
        "forbidden_substitutions": ["Go_for_SubGo", "Go-Me_for_SubGo-Me", "Go-Gn_for_SubGo-Me"],
        "patient_classification_active": False,
    }

    availability = AvailabilityStatus.AVAILABLE
    if missing:
        availability = AvailabilityStatus.NOT_COMPUTABLE
    elif len(source_images) != 1:
        availability = AvailabilityStatus.INVALID
    else:
        po = landmarks["Po"]
        or_ = landmarks["Or"]
        subgo = landmarks["SubGo"]
        me = landmarks["Me"]
        value = ricketts_1981_fma_deg_v1(
            (po.x, po.y),
            (or_.x, or_.y),
            (subgo.x, subgo.y),
            (me.x, me.y),
        )
        if value is None:
            availability = AvailabilityStatus.INVALID
        else:
            geometry["computed_angle_deg"] = value
            geometry["source_image_ref"] = next(iter(source_images))
            geometry["subgo_evidence_ref"] = subgo.evidence_id
            geometry["subgo_validated_by"] = subgo.validated_by
            geometry["subgo_validated_at"] = subgo.validated_at.isoformat() if subgo.validated_at else None

    return ConstructionEvidence(
        construction_id=f"{construction_namespace}:{RICKETTS_1981_FMA_DEFINITION_ID}",
        definition_id=RICKETTS_1981_FMA_DEFINITION_ID,
        definition_version="1",
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
    """Expose the raw source-specific FMA only; never apply the historical norm."""

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
        method_version="1",
        value=value,
        unit="deg",
        construction_refs=[construction.construction_id],
        requires_calibration=False,
        evidence_refs=[construction.construction_id],
        availability_status=availability,
    )
