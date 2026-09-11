"""Typed Steiner vertical angular evidence.

Only source-bound patient geometry is materialized here. No norms, diagnosis,
classification, growth projection or treatment logic is activated.
"""
from __future__ import annotations

from typing import Mapping

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    LandmarkEvidence,
    MeasurementEvidence,
)
from backend.services.cephalo_steiner_evidence_adapter import STEINER_SOURCE_REFERENCES
from backend.services.cephalo_steiner_geometry import steiner_sn_mp_deg_v1

STEINER_SN_MP_CONSTRUCTION_ID = "STEINER_SN_MP_ANGLE_V1"
STEINER_SN_MP_METHOD_ID = "STEINER_SN_MP_DEG_V1"
_REQUIRED = ("S", "N", "Go", "Gn")


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def materialize_steiner_vertical_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    refs: list[str] = []
    missing: list[str] = []
    sources: set[str] = set()
    for landmark_id in _REQUIRED:
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
        "required_landmark_ids": list(_REQUIRED),
        "axis_orientation_invariant": True,
        "reference_axis": "S-N",
        "mandibular_plane": "Go-Gn",
    }
    if missing:
        availability = AvailabilityStatus.NOT_COMPUTABLE
    elif len(sources) != 1:
        availability = AvailabilityStatus.INVALID
    else:
        value = steiner_sn_mp_deg_v1(
            _point(landmarks, "S"),
            _point(landmarks, "N"),
            _point(landmarks, "Go"),
            _point(landmarks, "Gn"),
        )
        if value is None:
            availability = AvailabilityStatus.INVALID
        else:
            geometry.update(
                {
                    "computed_angle_deg": round(value, 1),
                    "source_image_ref": next(iter(sources)),
                }
            )

    construction = ConstructionEvidence(
        construction_id=f"{construction_namespace}:{STEINER_SN_MP_CONSTRUCTION_ID}",
        definition_id=STEINER_SN_MP_CONSTRUCTION_ID,
        definition_version="1",
        landmark_refs=refs,
        missing_landmark_ids=missing,
        geometry=geometry,
        evidence_refs=refs,
        availability_status=availability,
    )
    return {STEINER_SN_MP_CONSTRUCTION_ID: construction}


def adapt_steiner_vertical_measurements(
    *, measurement_namespace: str, constructions: Mapping[str, ConstructionEvidence]
) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")
    construction = constructions.get(STEINER_SN_MP_CONSTRUCTION_ID)
    if construction is None:
        raise ValueError(f"Missing Steiner vertical construction {STEINER_SN_MP_CONSTRUCTION_ID}")

    availability = construction.availability_status
    value = None
    if availability == AvailabilityStatus.AVAILABLE:
        computed = construction.geometry.get("computed_angle_deg")
        if not isinstance(computed, (int, float)):
            raise ValueError("Available Steiner SN-MP construction lacks computed_angle_deg")
        value = float(computed)
    elif availability != AvailabilityStatus.INVALID:
        availability = AvailabilityStatus.NOT_COMPUTABLE

    return [
        MeasurementEvidence(
            measurement_id=f"{measurement_namespace}:SN_MP",
            analysis_id="STEINER",
            method_id=STEINER_SN_MP_METHOD_ID,
            method_version="1",
            value=value,
            unit="deg",
            construction_refs=[construction.construction_id],
            calibration_ref=None,
            requires_calibration=False,
            evidence_refs=[construction.construction_id],
            availability_status=availability,
        )
    ]
