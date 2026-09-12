"""Typed evidence adapter for the source-locked R9 Ricketts subset.

R9 certifies Facial Depth, Point-A Convexity and upper/lower lip distance to the
Ricketts E-line with explicit, versioned geometric conventions. Facial Axis
remains blocked until the runtime PT landmark is independently provenance-locked
to the exact Ricketts Pt definition. No norms, diagnosis, growth forecast or
treatment logic is activated here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Optional

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
)
from backend.services.cephalo_ricketts_geometry import (
    ricketts_convexity_signed_distance_px_v1,
    ricketts_e_line_horizontal_signed_distance_px_v1,
    ricketts_facial_depth_deg_v1,
)

RICKETTS_FACIAL_DEPTH_REFERENCES = (
    "doi:10.1016/0002-9416(60)90047-6",
    "doi:10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2",
)
RICKETTS_CONVEXITY_REFERENCES = (
    "doi:10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2",
    "PMCID:PMC3059215",
)
RICKETTS_E_LINE_REFERENCES = (
    "doi:10.1016/S0002-9416(68)90278-9",
    "PMCID:PMC10973926",
    "PMCID:PMC12569150",
)
RICKETTS_LANDMARK_CONTRACT = "docs/SRPOSE38_LANDMARK_CONTRACT.md"

RICKETTS_BLOCKED_CONTRACTS: dict[str, str] = {
    "RICKETTS_FACIAL_AXIS_DEG_V1": (
        "BLOCKED_LANDMARK_CONVENTION: CL-Detection landmark #28 is named PT, but "
        "its public provenance does not independently lock the annotation to the "
        "exact Ricketts Pt definition at the inferior border of foramen rotundum / "
        "posterior wall of the pterygomaxillary fissure. No runtime alias is allowed."
    ),
}


@dataclass(frozen=True)
class _RickettsSpec:
    metric_name: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, ...]
    kind: str
    unit: str
    requires_calibration: bool


_RICKETTS_SPECS = (
    _RickettsSpec("FACIAL_DEPTH", "RICKETTS_FACIAL_DEPTH_V1", "RICKETTS_FACIAL_DEPTH_DEG_V1", ("Po", "Or", "N", "Pog"), "facial_depth", "deg", False),
    _RickettsSpec("CONVEXITY_A_NPOG", "RICKETTS_CONVEXITY_A_NPOG_V1", "RICKETTS_CONVEXITY_A_NPOG_MM_V1", ("A", "N", "Pog", "Po", "Or"), "convexity", "mm", True),
    _RickettsSpec("E_LINE_LS", "RICKETTS_E_LINE_LS_V1", "RICKETTS_E_LINE_LS_MM_V1", ("Ls_soft", "Prn", "Pog_soft", "Po", "Or"), "e_line", "mm", True),
    _RickettsSpec("E_LINE_LI", "RICKETTS_E_LINE_LI_V1", "RICKETTS_E_LINE_LI_MM_V1", ("Li_soft", "Prn", "Pog_soft", "Po", "Or"), "e_line", "mm", True),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def _geometry_metadata(spec: _RickettsSpec) -> dict[str, object]:
    common: dict[str, object] = {
        "analysis": "RICKETTS",
        "required_landmark_ids": list(spec.required_landmark_ids),
        "coordinate_space": "source_image_pixels",
        "landmark_contract": RICKETTS_LANDMARK_CONTRACT,
        "mirror_invariant": True,
    }
    if spec.kind == "facial_depth":
        return {**common, "kind": "directed_cephalometric_angle", "source_references": list(RICKETTS_FACIAL_DEPTH_REFERENCES), "frankfort_plane": "Po-Or", "facial_plane": "N-Pog", "angle_convention": "posterior_angle_fh_po_or_to_pog_n_v1"}
    if spec.kind == "convexity":
        return {**common, "kind": "signed_perpendicular_point_to_line_distance", "source_references": list(RICKETTS_CONVEXITY_REFERENCES), "target_landmark": "A", "facial_plane": "N-Pog", "sign_convention": "positive_anterior_negative_posterior_v1", "sign_orientation_axis": "FH_PO_OR_V1", "distance_convention": "perpendicular_shortest_distance_v1"}
    return {**common, "kind": "signed_fh_parallel_point_to_line_distance", "source_references": list(RICKETTS_E_LINE_REFERENCES), "e_line": "Prn-Pog_soft", "target_landmark": spec.required_landmark_ids[0], "sign_convention": "positive_anterior_negative_posterior_v1", "measurement_axis": "FH_PO_OR_V1", "distance_convention": "parallel_to_frankfort_v1"}


def materialize_ricketts_constructions(landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")
    out: dict[str, ConstructionEvidence] = {}
    for spec in _RICKETTS_SPECS:
        refs: list[str] = []
        missing: list[str] = []
        sources: set[str] = set()
        for landmark_id in spec.required_landmark_ids:
            item = landmarks.get(landmark_id)
            if item is None:
                missing.append(landmark_id)
                continue
            if item.landmark_id != landmark_id:
                raise ValueError(f"Landmark mapping key {landmark_id} resolves to {item.landmark_id}")
            refs.append(item.evidence_id)
            sources.add(item.source_image_ref)
            if item.availability_status != AvailabilityStatus.AVAILABLE:
                missing.append(landmark_id)
        geometry = _geometry_metadata(spec)
        availability = AvailabilityStatus.AVAILABLE
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
        else:
            value: Optional[float]
            value_key: str
            if spec.kind == "facial_depth":
                value = ricketts_facial_depth_deg_v1(_point(landmarks, "Po"), _point(landmarks, "Or"), _point(landmarks, "N"), _point(landmarks, "Pog"))
                value_key = "computed_angle_deg"
            elif spec.kind == "convexity":
                value = ricketts_convexity_signed_distance_px_v1(_point(landmarks, "A"), _point(landmarks, "N"), _point(landmarks, "Pog"), _point(landmarks, "Po"), _point(landmarks, "Or"))
                value_key = "computed_signed_distance_px"
            else:
                value = ricketts_e_line_horizontal_signed_distance_px_v1(_point(landmarks, spec.required_landmark_ids[0]), _point(landmarks, "Prn"), _point(landmarks, "Pog_soft"), _point(landmarks, "Po"), _point(landmarks, "Or"))
                value_key = "computed_signed_distance_px"
            if value is None:
                availability = AvailabilityStatus.INVALID
            else:
                geometry.update({value_key: value, "source_image_ref": next(iter(sources))})
        out[spec.construction_definition_id] = ConstructionEvidence(
            construction_id=f"{construction_namespace}:{spec.construction_definition_id}", definition_id=spec.construction_definition_id,
            definition_version="1", landmark_refs=refs, missing_landmark_ids=missing, geometry=geometry,
            evidence_refs=refs, availability_status=availability,
        )
    return out


def _valid_ratio(value: Optional[float]) -> bool:
    return value is not None and math.isfinite(value) and value > 0


def adapt_ricketts_measurements(*, measurement_namespace: str, constructions: Mapping[str, ConstructionEvidence], mm_per_pixel: Optional[float], calibration_ref: Optional[str]) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")
    presence = [spec.construction_definition_id in constructions for spec in _RICKETTS_SPECS]
    if not any(presence):
        return []
    if not all(presence):
        raise ValueError("Partial Ricketts construction set is not a certified snapshot")
    calibration_available = isinstance(calibration_ref, str) and bool(calibration_ref.strip())
    ratio_valid = _valid_ratio(mm_per_pixel)
    out: list[MeasurementEvidence] = []
    for spec in _RICKETTS_SPECS:
        construction = constructions[spec.construction_definition_id]
        if construction.definition_id != spec.construction_definition_id:
            raise ValueError(f"Construction key {spec.construction_definition_id} resolves to {construction.definition_id}")
        availability = construction.availability_status
        value: Optional[float] = None
        effective_calibration_ref: Optional[str] = None
        evidence_refs = [construction.construction_id]
        if availability == AvailabilityStatus.AVAILABLE:
            if spec.requires_calibration:
                computed = construction.geometry.get("computed_signed_distance_px")
                if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
                    raise ValueError(f"Available Ricketts construction {spec.construction_definition_id} lacks finite computed_signed_distance_px")
                if calibration_available and ratio_valid:
                    assert mm_per_pixel is not None and calibration_ref is not None
                    value = float(computed) * mm_per_pixel
                    if not math.isfinite(value):
                        availability = AvailabilityStatus.INVALID
                        value = None
                    else:
                        effective_calibration_ref = calibration_ref
                        evidence_refs.append(calibration_ref)
                elif calibration_available != ratio_valid:
                    availability = AvailabilityStatus.INVALID
                else:
                    availability = AvailabilityStatus.NOT_COMPUTABLE
            else:
                computed = construction.geometry.get("computed_angle_deg")
                if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
                    raise ValueError(f"Available Ricketts construction {spec.construction_definition_id} lacks finite computed_angle_deg")
                value = float(computed)
        elif availability != AvailabilityStatus.INVALID:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        out.append(MeasurementEvidence(
            measurement_id=f"{measurement_namespace}:{spec.metric_name}", analysis_id="RICKETTS", method_id=spec.method_id,
            method_version="1", value=value, unit=spec.unit, construction_refs=[construction.construction_id],
            calibration_ref=effective_calibration_ref, requires_calibration=spec.requires_calibration,
            evidence_refs=evidence_refs, availability_status=availability,
        ))
    return out


RICKETTS_CONSTRUCTION_DEFINITIONS = tuple(spec.construction_definition_id for spec in _RICKETTS_SPECS)
