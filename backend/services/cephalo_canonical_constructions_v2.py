"""Canonical derived constructions required by LOT06 v2 measurements."""
from __future__ import annotations

from typing import Mapping

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_ricketts_geometry import ricketts_constructed_gn_v1, ricketts_xi_from_r1_r4_fh_v1

RICKETTS_GN_CONSTRUCTION_ID = "RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1"
RICKETTS_GN_REQUIRED_LANDMARKS = ("N", "Pog_hard", "Go", "Me")
RICKETTS_PTV_CONSTRUCTION_ID = "RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1"
RICKETTS_PTV_REQUIRED_LANDMARKS = ("PR_Ricketts_PTV", "Po_anatomic", "Or")
RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID = "RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1"
RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_REQUIRED_LANDMARKS = (
    "FOP_PREMOLAR_Ricketts",
    "FOP_MOLAR_Ricketts",
)
RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID = "RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1"
RICKETTS_MANDIBULAR_PLANE_REQUIRED_LANDMARKS = ("MP_ANGLE_INFERIOR_Ricketts", "Me")
RICKETTS_XI_CONSTRUCTION_ID = "RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1"
RICKETTS_XI_REQUIRED_LANDMARKS = ("R1_Ricketts", "R2_Ricketts", "R3_Ricketts", "R4_Ricketts", "Po_anatomic", "Or")
RICKETTS_CF_CONSTRUCTION_ID = "RICKETTS_CF_FH_PTV_INTERSECTION_V1"


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
        if (
            landmark_id == "PR_Ricketts_PTV"
            and item.origin not in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}
            and landmark_id not in ptv_missing
        ):
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
                "anterior_x": fh_x / norm,
                "anterior_y": fh_y / norm,
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
    def _explicit_line(
        definition_id: str,
        required_ids: tuple[str, str],
        construction_rule: str,
    ) -> ConstructionEvidence:
        line_refs: list[str] = []
        line_missing: list[str] = []
        line_sources: set[str] = set()
        for landmark_id in required_ids:
            item = landmarks.get(landmark_id)
            if item is None:
                line_missing.append(landmark_id)
                continue
            if item.landmark_id != landmark_id:
                raise ValueError(
                    f"Landmark mapping key {landmark_id} resolves to {item.landmark_id}"
                )
            line_refs.append(item.evidence_id)
            line_sources.add(item.source_image_ref)
            if item.availability_status != AvailabilityStatus.AVAILABLE:
                line_missing.append(landmark_id)

        line_geometry: dict[str, object] = {
            "kind": "constructed_line",
            "construction_rule": construction_rule,
            "required_landmark_ids": list(required_ids),
            "coordinate_space": "source_image_pixels",
        }
        line_availability = AvailabilityStatus.AVAILABLE
        if line_missing:
            line_availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(line_sources) != 1:
            line_availability = AvailabilityStatus.INVALID
        else:
            p1 = landmarks[required_ids[0]]
            p2 = landmarks[required_ids[1]]
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            norm = (dx * dx + dy * dy) ** 0.5
            if norm <= 1e-12:
                line_availability = AvailabilityStatus.INVALID
            else:
                line_geometry.update(
                    {
                        "point_x": p1.x,
                        "point_y": p1.y,
                        "direction_x": dx / norm,
                        "direction_y": dy / norm,
                        "source_image_ref": next(iter(line_sources)),
                    }
                )
        return ConstructionEvidence(
            construction_id=f"{construction_namespace}:{definition_id}",
            definition_id=definition_id,
            definition_version="1",
            landmark_refs=line_refs,
            missing_landmark_ids=line_missing,
            geometry=line_geometry,
            evidence_refs=line_refs,
            availability_status=line_availability,
        )

    functional_occlusal_plane = _explicit_line(
        RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID,
        RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_REQUIRED_LANDMARKS,
        "line_through_explicit_Ricketts_buccal_occlusion_premolar_and_molar_points",
    )
    mandibular_plane = _explicit_line(
        RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID,
        RICKETTS_MANDIBULAR_PLANE_REQUIRED_LANDMARKS,
        "line_through_explicit_Ricketts_inferior_angle_point_and_Menton",
    )


    xi_refs: list[str] = []
    xi_missing: list[str] = []
    xi_sources: set[str] = set()
    for landmark_id in RICKETTS_XI_REQUIRED_LANDMARKS:
        item = landmarks.get(landmark_id)
        if item is None:
            xi_missing.append(landmark_id)
            continue
        if item.landmark_id != landmark_id:
            raise ValueError(
                f"Landmark mapping key {landmark_id} resolves to {item.landmark_id}"
            )
        xi_refs.append(item.evidence_id)
        xi_sources.add(item.source_image_ref)
        if item.availability_status != AvailabilityStatus.AVAILABLE:
            xi_missing.append(landmark_id)
        if (
            landmark_id in {"R1_Ricketts", "R2_Ricketts", "R3_Ricketts", "R4_Ricketts"}
            and item.origin not in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}
            and landmark_id not in xi_missing
        ):
            xi_missing.append(landmark_id)

    xi_geometry: dict[str, object] = {
        "kind": "constructed_landmark",
        "constructed_landmark_id": "Xi_Ricketts",
        "required_landmark_ids": list(RICKETTS_XI_REQUIRED_LANDMARKS),
        "construction_rule": "center_of_R1_R2_R3_R4_ramal_rectangle_in_anatomical_Frankfort_basis",
        "coordinate_space": "source_image_pixels",
    }
    xi_availability = AvailabilityStatus.AVAILABLE
    if xi_missing:
        xi_availability = AvailabilityStatus.NOT_COMPUTABLE
    elif len(xi_sources) != 1:
        xi_availability = AvailabilityStatus.INVALID
    else:
        xi_point = ricketts_xi_from_r1_r4_fh_v1(
            (landmarks["R1_Ricketts"].x, landmarks["R1_Ricketts"].y),
            (landmarks["R2_Ricketts"].x, landmarks["R2_Ricketts"].y),
            (landmarks["R3_Ricketts"].x, landmarks["R3_Ricketts"].y),
            (landmarks["R4_Ricketts"].x, landmarks["R4_Ricketts"].y),
            (landmarks["Po_anatomic"].x, landmarks["Po_anatomic"].y),
            (landmarks["Or"].x, landmarks["Or"].y),
        )
        if xi_point is None:
            xi_availability = AvailabilityStatus.INVALID
        else:
            xi_geometry.update({
                "x": xi_point[0],
                "y": xi_point[1],
                "source_image_ref": next(iter(xi_sources)),
            })

    cf_geometry: dict[str, object] = {
        "kind": "constructed_landmark",
        "constructed_landmark_id": "CF_Ricketts",
        "construction_rule": "intersection_of_anatomical_Frankfort_and_source_locked_Ricketts_PTV",
        "coordinate_space": "source_image_pixels",
    }
    cf_refs = list(ptv.landmark_refs)
    cf_availability = ptv.availability_status
    if cf_availability == AvailabilityStatus.AVAILABLE:
        po = landmarks["Po_anatomic"]
        or_ = landmarks["Or"]
        pr = landmarks["PR_Ricketts_PTV"]
        fh_x = or_.x - po.x
        fh_y = or_.y - po.y
        fh_len_sq = fh_x * fh_x + fh_y * fh_y
        if fh_len_sq <= 1e-12:
            cf_availability = AvailabilityStatus.INVALID
        else:
            t = ((pr.x - po.x) * fh_x + (pr.y - po.y) * fh_y) / fh_len_sq
            cf_geometry.update({
                "x": po.x + t * fh_x,
                "y": po.y + t * fh_y,
                "source_image_ref": ptv.geometry.get("source_image_ref"),
            })
    cf_construction = ConstructionEvidence(
        construction_id=f"{construction_namespace}:{RICKETTS_CF_CONSTRUCTION_ID}",
        definition_id=RICKETTS_CF_CONSTRUCTION_ID,
        definition_version="1",
        landmark_refs=cf_refs,
        missing_landmark_ids=list(ptv.missing_landmark_ids),
        geometry=cf_geometry,
        evidence_refs=cf_refs,
        availability_status=cf_availability,
    )

    xi_construction = ConstructionEvidence(
        construction_id=f"{construction_namespace}:{RICKETTS_XI_CONSTRUCTION_ID}",
        definition_id=RICKETTS_XI_CONSTRUCTION_ID,
        definition_version="1",
        landmark_refs=xi_refs,
        missing_landmark_ids=xi_missing,
        geometry=xi_geometry,
        evidence_refs=xi_refs,
        availability_status=xi_availability,
    )

    return {
        RICKETTS_GN_CONSTRUCTION_ID: construction,
        RICKETTS_PTV_CONSTRUCTION_ID: ptv,
        RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID: functional_occlusal_plane,
        RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID: mandibular_plane,
        RICKETTS_XI_CONSTRUCTION_ID: xi_construction,
        RICKETTS_CF_CONSTRUCTION_ID: cf_construction,
    }
