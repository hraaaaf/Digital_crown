"""Canonical derived constructions required by LOT06 v2 measurements."""
from __future__ import annotations

from typing import Mapping

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    LandmarkEvidence,
)
from backend.services.cephalo_ricketts_geometry import ricketts_constructed_gn_v1

RICKETTS_GN_CONSTRUCTION_ID = "RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1"
RICKETTS_GN_REQUIRED_LANDMARKS = ("N", "Pog_hard", "Go", "Me")
RICKETTS_PTV_CONSTRUCTION_ID = "RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1"
RICKETTS_PTV_REQUIRED_LANDMARKS = ("PR_Ricketts_PTV", "Po_anatomic", "Or")


def materialize_canonical_constructions_v2(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    construction_namespace: str,
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    refs: list[str] = []
    missing: list[str] = []
    sources: set[str] = set()
    for landmark_id in RICKETTS_GN_REQUIRED_LANDMARKS:
        item = landmarks.get(landmark_id)
        if item is None:
            missing.append(landmark_id)
            continue
        if item.landmark_id != landmark_id:
            raise ValueError(
                f"Landmark mapping key {landmark_id} resolves to {item.landmark_id}"
            )
        refs.append(item.evidence_id)
        sources.add(item.source_image_ref)
        if item.availability_status != AvailabilityStatus.AVAILABLE:
            missing.append(landmark_id)

    geometry: dict[str, object] = {
        "kind": "constructed_landmark",
        "constructed_landmark_id": "Gn_constructed_Ricketts",
        "required_landmark_ids": list(RICKETTS_GN_REQUIRED_LANDMARKS),
        "construction_rule": "intersection_of_N_Pog_hard_and_Go_Me_infinite_lines",
        "coordinate_space": "source_image_pixels",
    }
    availability = AvailabilityStatus.AVAILABLE
    if missing:
        availability = AvailabilityStatus.NOT_COMPUTABLE
    elif len(sources) != 1:
        availability = AvailabilityStatus.INVALID
    else:
        point = ricketts_constructed_gn_v1(
            (landmarks["N"].x, landmarks["N"].y),
            (landmarks["Pog_hard"].x, landmarks["Pog_hard"].y),
            (landmarks["Go"].x, landmarks["Go"].y),
            (landmarks["Me"].x, landmarks["Me"].y),
        )
        if point is None:
            availability = AvailabilityStatus.INVALID
        else:
            geometry.update(
                {
                    "x": point[0],
                    "y": point[1],
                    "source_image_ref": next(iter(sources)),
                }
            )

    construction = ConstructionEvidence(
        construction_id=f"{construction_namespace}:{RICKETTS_GN_CONSTRUCTION_ID}",
        definition_id=RICKETTS_GN_CONSTRUCTION_ID,
        definition_version="1",
        landmark_refs=refs,
        missing_landmark_ids=missing,
        geometry=geometry,
        evidence_refs=refs,
        availability_status=availability,
    )
    ptv_refs: list[str] = []
    ptv_missing: list[str] = []
    ptv_sources: set[str] = set()
    for landmark_id in RICKETTS_PTV_REQUIRED_LANDMARKS:
        item = landmarks.get(landmark_id)
        if item is None:
            ptv_missing.append(landmark_id)
            continue
        if item.landmark_id != landmark_id:
            raise ValueError(
                f"Landmark mapping key {landmark_id} resolves to {item.landmark_id}"
            )
        ptv_refs.append(item.evidence_id)
        ptv_sources.add(item.source_image_ref)
        if item.availability_status != AvailabilityStatus.AVAILABLE:
            ptv_missing.append(landmark_id)

    ptv_geometry: dict[str, object] = {
        "kind": "constructed_line",
        "construction_rule": "line_through_PR_Ricketts_PTV_perpendicular_to_Frankfort_Po_anatomic_Or",
        "required_landmark_ids": list(RICKETTS_PTV_REQUIRED_LANDMARKS),
        "coordinate_space": "source_image_pixels",
    }
    ptv_availability = AvailabilityStatus.AVAILABLE
    if ptv_missing:
        ptv_availability = AvailabilityStatus.NOT_COMPUTABLE
    elif len(ptv_sources) != 1:
        ptv_availability = AvailabilityStatus.INVALID
    else:
        po = landmarks["Po_anatomic"]
        or_ = landmarks["Or"]
        pt = landmarks["PR_Ricketts_PTV"]
        fh_x = or_.x - po.x
        fh_y = or_.y - po.y
        norm = (fh_x * fh_x + fh_y * fh_y) ** 0.5
        if norm <= 1e-12:
            ptv_availability = AvailabilityStatus.INVALID
        else:
            # PTV direction is perpendicular to anatomical Frankfort.
            dx = -fh_y / norm
            dy = fh_x / norm
            ptv_geometry.update({
                "point_x": pt.x,
                "point_y": pt.y,
                "direction_x": dx,
                "direction_y": dy,
                "source_image_ref": next(iter(ptv_sources)),
            })

    ptv = ConstructionEvidence(
        construction_id=f"{construction_namespace}:{RICKETTS_PTV_CONSTRUCTION_ID}",
        definition_id=RICKETTS_PTV_CONSTRUCTION_ID,
        definition_version="1",
        landmark_refs=ptv_refs,
        missing_landmark_ids=ptv_missing,
        geometry=ptv_geometry,
        evidence_refs=ptv_refs,
        availability_status=ptv_availability,
    )
    return {
        RICKETTS_GN_CONSTRUCTION_ID: construction,
        RICKETTS_PTV_CONSTRUCTION_ID: ptv,
    }
