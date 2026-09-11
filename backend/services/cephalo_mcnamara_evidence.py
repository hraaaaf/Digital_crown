"""Typed evidence adapter for the source-safe R8 McNamara linear subset.

The initial R8 slice contains only Co-A, Co-Gn and ANS-Me. All three require
verified calibration. No norms, diagnosis, growth projection or treatment logic
is activated here.
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
from backend.services.cephalo_mcnamara_geometry import mcnamara_linear_distance_px_v1

MCNAMARA_SOURCE_REFERENCES = (
    "doi:10.1016/S0002-9416(84)90352-X",
    "McNamara JA Jr. A method of cephalometric evaluation. Am J Orthod. 1984;86(6):449-469",
)


@dataclass(frozen=True)
class _McNamaraSpec:
    metric_name: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, str]


_MCNAMARA_SPECS = (
    _McNamaraSpec(
        metric_name="CO_A",
        construction_definition_id="MCNAMARA_CO_A_V1",
        method_id="MCNAMARA_CO_A_MM_V1",
        required_landmark_ids=("Co", "A"),
    ),
    _McNamaraSpec(
        metric_name="CO_GN",
        construction_definition_id="MCNAMARA_CO_GN_V1",
        method_id="MCNAMARA_CO_GN_MM_V1",
        required_landmark_ids=("Co", "Gn"),
    ),
    _McNamaraSpec(
        metric_name="ANS_ME",
        construction_definition_id="MCNAMARA_ANS_ME_V1",
        method_id="MCNAMARA_ANS_ME_MM_V1",
        required_landmark_ids=("ANS", "Me"),
    ),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def materialize_mcnamara_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    out: dict[str, ConstructionEvidence] = {}
    for spec in _MCNAMARA_SPECS:
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
            "kind": "euclidean_linear_distance",
            "analysis": "MCNAMARA",
            "source_references": list(MCNAMARA_SOURCE_REFERENCES),
            "required_landmark_ids": list(spec.required_landmark_ids),
            "coordinate_space": "source_image_pixels",
            "segment_start": spec.required_landmark_ids[0],
            "segment_end": spec.required_landmark_ids[1],
        }

        availability = AvailabilityStatus.AVAILABLE
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
        else:
            distance_px = mcnamara_linear_distance_px_v1(
                _point(landmarks, spec.required_landmark_ids[0]),
                _point(landmarks, spec.required_landmark_ids[1]),
            )
            if distance_px is None:
                availability = AvailabilityStatus.INVALID
            else:
                geometry.update(
                    {
                        "computed_distance_px": distance_px,
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


def _valid_ratio(value: Optional[float]) -> bool:
    return value is not None and math.isfinite(value) and value > 0


def adapt_mcnamara_measurements(
    *,
    measurement_namespace: str,
    constructions: Mapping[str, ConstructionEvidence],
    mm_per_pixel: Optional[float],
    calibration_ref: Optional[str],
) -> list[MeasurementEvidence]:
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    presence = [
        spec.construction_definition_id in constructions for spec in _MCNAMARA_SPECS
    ]
    if not any(presence):
        # Compatibility for persisted snapshots created before R8 existed.
        return []
    if not all(presence):
        raise ValueError("Partial McNamara construction set is not a certified snapshot")

    calibration_available = isinstance(calibration_ref, str) and bool(calibration_ref.strip())
    ratio_valid = _valid_ratio(mm_per_pixel)
    out: list[MeasurementEvidence] = []

    for spec in _MCNAMARA_SPECS:
        construction = constructions.get(spec.construction_definition_id)
        if construction is None:
            raise ValueError(f"Missing McNamara construction {spec.construction_definition_id}")
        if construction.definition_id != spec.construction_definition_id:
            raise ValueError(
                f"Construction key {spec.construction_definition_id} resolves to {construction.definition_id}"
            )

        availability = construction.availability_status
        value: Optional[float] = None
        if availability == AvailabilityStatus.AVAILABLE:
            distance_px = construction.geometry.get("computed_distance_px")
            if (
                not isinstance(distance_px, (int, float))
                or not math.isfinite(float(distance_px))
                or float(distance_px) <= 0
            ):
                raise ValueError(
                    f"Available McNamara construction {spec.construction_definition_id} lacks a valid computed_distance_px"
                )
            if calibration_available and ratio_valid:
                assert mm_per_pixel is not None
                value = float(distance_px) * mm_per_pixel
                if not math.isfinite(value):
                    availability = AvailabilityStatus.INVALID
                    value = None
            elif calibration_available != ratio_valid:
                availability = AvailabilityStatus.INVALID
            else:
                availability = AvailabilityStatus.NOT_COMPUTABLE
        elif availability != AvailabilityStatus.INVALID:
            availability = AvailabilityStatus.NOT_COMPUTABLE

        evidence_refs = [construction.construction_id]
        effective_calibration_ref: Optional[str] = None
        if calibration_available:
            assert calibration_ref is not None
            effective_calibration_ref = calibration_ref
            evidence_refs.append(calibration_ref)

        out.append(
            MeasurementEvidence(
                measurement_id=f"{measurement_namespace}:{spec.metric_name}",
                analysis_id="MCNAMARA",
                method_id=spec.method_id,
                method_version="1",
                value=value,
                unit="mm",
                construction_refs=[construction.construction_id],
                calibration_ref=effective_calibration_ref,
                requires_calibration=True,
                evidence_refs=evidence_refs,
                availability_status=availability,
            )
        )
    return out


MCNAMARA_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _MCNAMARA_SPECS
)
