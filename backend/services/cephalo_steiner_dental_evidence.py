"""Typed Steiner dental angular evidence.

No norms, diagnosis, treatment logic, or linear crown-distance assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
)
from backend.services.cephalo_steiner_evidence_adapter import STEINER_SOURCE_REFERENCES
from backend.services.cephalo_steiner_geometry import (
    steiner_l1_nb_deg_v1,
    steiner_u1_na_deg_v1,
)


@dataclass(frozen=True)
class _DentalSpec:
    metric_name: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, ...]


_SPECS = (
    _DentalSpec(
        metric_name="U1_NA",
        construction_definition_id="STEINER_U1_NA_ANGLE_V1",
        method_id="STEINER_U1_NA_DEG_V1",
        required_landmark_ids=("U1_apex", "U1_incisal", "N", "A"),
    ),
    _DentalSpec(
        metric_name="L1_NB",
        construction_definition_id="STEINER_L1_NB_ANGLE_V1",
        method_id="STEINER_L1_NB_DEG_V1",
        required_landmark_ids=("L1_apex", "L1_incisal", "N", "B"),
    ),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def _compute(definition_id: str, landmarks: Mapping[str, LandmarkEvidence]) -> Optional[float]:
    if definition_id == "STEINER_U1_NA_ANGLE_V1":
        return steiner_u1_na_deg_v1(
            _point(landmarks, "U1_apex"),
            _point(landmarks, "U1_incisal"),
            _point(landmarks, "N"),
            _point(landmarks, "A"),
        )
    if definition_id == "STEINER_L1_NB_ANGLE_V1":
        return steiner_l1_nb_deg_v1(
            _point(landmarks, "L1_apex"),
            _point(landmarks, "L1_incisal"),
            _point(landmarks, "N"),
            _point(landmarks, "B"),
        )
    raise ValueError(f"Unsupported Steiner dental construction {definition_id}")


def materialize_steiner_dental_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    out: dict[str, ConstructionEvidence] = {}
    for spec in _SPECS:
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

        availability = AvailabilityStatus.AVAILABLE
        geometry: dict[str, object] = {
            "kind": "cephalometric_angle",
            "analysis": "STEINER",
            "source_references": list(STEINER_SOURCE_REFERENCES),
            "required_landmark_ids": list(spec.required_landmark_ids),
            "axis_orientation_invariant": True,
        }
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
        else:
            value = _compute(spec.construction_definition_id, landmarks)
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


def adapt_steiner_dental_measurements(
    *, measurement_namespace: str, constructions: Mapping[str, ConstructionEvidence]
) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    out: list[MeasurementEvidence] = []
    for spec in _SPECS:
        construction = constructions.get(spec.construction_definition_id)
        if construction is None:
            raise ValueError(f"Missing Steiner dental construction {spec.construction_definition_id}")
        availability = construction.availability_status
        value = None
        if availability == AvailabilityStatus.AVAILABLE:
            computed = construction.geometry.get("computed_angle_deg")
            if not isinstance(computed, (int, float)):
                raise ValueError(
                    f"Available Steiner dental construction {spec.construction_definition_id} lacks computed_angle_deg"
                )
            value = float(computed)
        elif availability != AvailabilityStatus.INVALID:
            availability = AvailabilityStatus.NOT_COMPUTABLE

        out.append(
            MeasurementEvidence(
                measurement_id=f"{measurement_namespace}:{spec.metric_name}",
                analysis_id="STEINER",
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


STEINER_DENTAL_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _SPECS
)
