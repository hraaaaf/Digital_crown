"""Typed evidence adapter for the source-safe R9 Ricketts subset.

R9 initially certifies Facial Depth only. Facial Axis, Point A Convexity and
E-line lip distances remain explicit blocked contracts until their landmark or
geometric conventions are source-locked. No norms, diagnosis, growth forecast
or treatment logic is activated here.
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
from backend.services.cephalo_ricketts_geometry import ricketts_facial_depth_deg_v1

RICKETTS_SOURCE_REFERENCES = (
    "doi:10.1016/0002-9416(60)90047-6",
    "doi:10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2",
)

RICKETTS_BLOCKED_CONTRACTS = {
    "RICKETTS_FACIAL_AXIS_DEG_V1": "BLOCKED_LANDMARK_CONVENTION: runtime PT_point has no source-certified semantic binding to Ricketts Pt",
    "RICKETTS_CONVEXITY_A_NPOG_MM_V1": "BLOCKED_GEOMETRIC_CONVENTION: sources diverge between point-line perpendicular distance and Frankfort-parallel linear measurement",
    "RICKETTS_E_LINE_LS_MM_V1": "BLOCKED_LANDMARK_CONVENTION: SRPose38 soft-tissue index nomenclature is not source-certified in the current runtime",
    "RICKETTS_E_LINE_LI_MM_V1": "BLOCKED_LANDMARK_CONVENTION: SRPose38 soft-tissue index nomenclature is not source-certified in the current runtime",
}


@dataclass(frozen=True)
class _RickettsSpec:
    metric_name: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, ...]


_RICKETTS_SPECS = (
    _RickettsSpec(
        metric_name="FACIAL_DEPTH",
        construction_definition_id="RICKETTS_FACIAL_DEPTH_V1",
        method_id="RICKETTS_FACIAL_DEPTH_DEG_V1",
        required_landmark_ids=("Po", "Or", "N", "Pog"),
    ),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def materialize_ricketts_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
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
                raise ValueError(
                    f"Landmark mapping key {landmark_id} resolves to {item.landmark_id}"
                )
            refs.append(item.evidence_id)
            sources.add(item.source_image_ref)
            if item.availability_status != AvailabilityStatus.AVAILABLE:
                missing.append(landmark_id)

        geometry: dict[str, object] = {
            "kind": "directed_cephalometric_angle",
            "analysis": "RICKETTS",
            "source_references": list(RICKETTS_SOURCE_REFERENCES),
            "required_landmark_ids": list(spec.required_landmark_ids),
            "coordinate_space": "source_image_pixels",
            "frankfort_plane": "Po-Or",
            "facial_plane": "N-Pog",
            "angle_convention": "posterior_angle_fh_po_or_to_pog_n_v1",
            "mirror_invariant": True,
        }

        availability = AvailabilityStatus.AVAILABLE
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
        else:
            value = ricketts_facial_depth_deg_v1(
                _point(landmarks, "Po"),
                _point(landmarks, "Or"),
                _point(landmarks, "N"),
                _point(landmarks, "Pog"),
            )
            if value is None:
                availability = AvailabilityStatus.INVALID
            else:
                geometry.update(
                    {
                        "computed_angle_deg": value,
                        "source_image_ref": next(iter(sources)),
                    }
                )

        out[spec.construction_definition_id] = ConstructionEvidence(
            construction_id=f"{construction_namespace}:{spec.construction_definition_id}",
            definition_id=spec.construction_definition_id,
            definition_version="1",
            landmark_refs=refs,
            missing_landmark_ids=missing,
            geometry=geometry,
            evidence_refs=refs,
            availability_status=availability,
        )
    return out


def adapt_ricketts_measurements(
    *, measurement_namespace: str, constructions: Mapping[str, ConstructionEvidence]
) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    presence = [spec.construction_definition_id in constructions for spec in _RICKETTS_SPECS]
    if not any(presence):
        # Compatibility for snapshots created before R9 existed.
        return []
    if not all(presence):
        raise ValueError("Partial Ricketts construction set is not a certified snapshot")

    out: list[MeasurementEvidence] = []
    for spec in _RICKETTS_SPECS:
        construction = constructions.get(spec.construction_definition_id)
        if construction is None:
            raise ValueError(f"Missing Ricketts construction {spec.construction_definition_id}")
        if construction.definition_id != spec.construction_definition_id:
            raise ValueError(
                f"Construction key {spec.construction_definition_id} resolves to {construction.definition_id}"
            )

        availability = construction.availability_status
        value: Optional[float] = None
        if availability == AvailabilityStatus.AVAILABLE:
            computed = construction.geometry.get("computed_angle_deg")
            if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
                raise ValueError(
                    f"Available Ricketts construction {spec.construction_definition_id} lacks finite computed_angle_deg"
                )
            value = float(computed)
        elif availability != AvailabilityStatus.INVALID:
            availability = AvailabilityStatus.NOT_COMPUTABLE

        out.append(
            MeasurementEvidence(
                measurement_id=f"{measurement_namespace}:{spec.metric_name}",
                analysis_id="RICKETTS",
                method_id=spec.method_id,
                method_version="1",
                value=value,
                unit="deg",
                construction_refs=[construction.construction_id],
                calibration_ref=None,
                requires_calibration=False,
                evidence_refs=[construction.construction_id],
                availability_status=availability,
            )
        )
    return out


RICKETTS_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _RICKETTS_SPECS
)
