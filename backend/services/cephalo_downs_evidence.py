"""Typed evidence adapter for the source-safe subset of Downs analysis.

No norms, diagnosis, prognosis or treatment logic is activated here.
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
from backend.services.cephalo_downs_geometry import (
    downs_facial_angle_deg_v1,
    downs_y_axis_deg_v1,
)

DOWNS_SOURCE_REFERENCES = (
    "doi:10.1016/0002-9416(48)90015-3",
    "Downs WB. Variations in facial relationships; their significance in treatment and prognosis. Am J Orthod. 1948;34(10):812-840",
)


@dataclass(frozen=True)
class _DownsSpec:
    metric_name: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, ...]


_DOWNS_SPECS = (
    _DownsSpec(
        metric_name="FACIAL_ANGLE",
        construction_definition_id="DOWNS_FACIAL_ANGLE_V1",
        method_id="DOWNS_FACIAL_ANGLE_DEG_V1",
        required_landmark_ids=("Po", "Or", "N", "Pog"),
    ),
    _DownsSpec(
        metric_name="Y_AXIS",
        construction_definition_id="DOWNS_Y_AXIS_V1",
        method_id="DOWNS_Y_AXIS_DEG_V1",
        required_landmark_ids=("S", "Gn", "Po", "Or"),
    ),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def _computed_value(definition_id: str, landmarks: Mapping[str, LandmarkEvidence]) -> Optional[float]:
    if definition_id == "DOWNS_FACIAL_ANGLE_V1":
        return downs_facial_angle_deg_v1(
            _point(landmarks, "Po"), _point(landmarks, "Or"),
            _point(landmarks, "N"), _point(landmarks, "Pog"),
        )
    if definition_id == "DOWNS_Y_AXIS_V1":
        return downs_y_axis_deg_v1(
            _point(landmarks, "S"), _point(landmarks, "Gn"),
            _point(landmarks, "Po"), _point(landmarks, "Or"),
        )
    raise ValueError(f"Unsupported Downs construction {definition_id}")


def materialize_downs_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    out: dict[str, ConstructionEvidence] = {}
    for spec in _DOWNS_SPECS:
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
            "kind": "cephalometric_angle",
            "analysis": "DOWNS",
            "source_references": list(DOWNS_SOURCE_REFERENCES),
            "required_landmark_ids": list(spec.required_landmark_ids),
            "axis_orientation_invariant": True,
            "frankfort_plane": "Po-Or",
        }
        if spec.construction_definition_id == "DOWNS_FACIAL_ANGLE_V1":
            geometry["facial_plane"] = "N-Pog"
        else:
            geometry["y_axis"] = "S-Gn"

        availability = AvailabilityStatus.AVAILABLE
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
        else:
            value = _computed_value(spec.construction_definition_id, landmarks)
            if value is None:
                availability = AvailabilityStatus.INVALID
            else:
                geometry.update(
                    {
                        "computed_angle_deg": round(value, 1),
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


def adapt_downs_measurements(
    *, measurement_namespace: str, constructions: Mapping[str, ConstructionEvidence]
) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    out: list[MeasurementEvidence] = []
    for spec in _DOWNS_SPECS:
        construction = constructions.get(spec.construction_definition_id)
        if construction is None:
            raise ValueError(f"Missing Downs construction {spec.construction_definition_id}")

        availability = construction.availability_status
        value: Optional[float] = None
        if availability == AvailabilityStatus.AVAILABLE:
            computed = construction.geometry.get("computed_angle_deg")
            if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
                raise ValueError(
                    f"Available Downs construction {spec.construction_definition_id} lacks finite computed_angle_deg"
                )
            value = float(computed)
        elif availability == AvailabilityStatus.INVALID:
            value = None
        else:
            availability = AvailabilityStatus.NOT_COMPUTABLE
            value = None

        out.append(
            MeasurementEvidence(
                measurement_id=f"{measurement_namespace}:{spec.metric_name}",
                analysis_id="DOWNS",
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


DOWNS_CONSTRUCTION_DEFINITIONS = tuple(spec.construction_definition_id for spec in _DOWNS_SPECS)
