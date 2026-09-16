"""Typed evidence adapter for source-safe McNamara measurements.

The legacy R8 subset contains Co-A, Co-Gn and ANS-Me. The Céphalo-N extension
adds only the two McNamara N-perpendicular distances whose source definition,
landmarks, sign and unit are locked: A-Nperp and Pog-Nperp.

No norms, diagnosis, growth projection or treatment logic is activated here.
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
from backend.services.cephalo_constructions import (
    frankfort_axis_v1,
    signed_axis_distance_px_v1,
)
from backend.services.cephalo_mcnamara_geometry import mcnamara_linear_distance_px_v1
from backend.services.cephalo_measure_registry import canonical_unit

MCNAMARA_SOURCE_REFERENCES = (
    "doi:10.1016/S0002-9416(84)90352-X",
    "pmid:6594933",
)
MCNAMARA_NPERP_SECONDARY_REFERENCE = "pmc:PMC4436328"


@dataclass(frozen=True)
class _McNamaraSpec:
    metric_name: str
    construction_definition_id: str
    method_id: str
    required_landmark_ids: tuple[str, str]


@dataclass(frozen=True)
class _McNamaraNPerpSpec:
    metric_name: str
    canonical_id: str
    construction_definition_id: str
    required_landmark_ids: tuple[str, str, str, str]


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

_MCNAMARA_NPERP_SPECS = (
    _McNamaraNPerpSpec(
        metric_name="A_NPERP",
        canonical_id="M_A_NPERP_MM_V1",
        construction_definition_id="MCNAMARA_A_NPERP_V1",
        required_landmark_ids=("A", "N", "Po", "Or"),
    ),
    _McNamaraNPerpSpec(
        metric_name="POG_NPERP",
        canonical_id="M_POG_NPERP_MM_V1",
        construction_definition_id="MCNAMARA_POG_NPERP_V1",
        required_landmark_ids=("Pog", "N", "Po", "Or"),
    ),
)


def _point(landmarks: Mapping[str, LandmarkEvidence], key: str) -> tuple[float, float]:
    item = landmarks[key]
    return (item.x, item.y)


def _resolve_landmark_dependencies(
    landmarks: Mapping[str, LandmarkEvidence],
    required_landmark_ids: tuple[str, ...],
) -> tuple[list[str], list[str], set[str]]:
    refs: list[str] = []
    missing: list[str] = []
    sources: set[str] = set()
    for landmark_id in required_landmark_ids:
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
    return refs, missing, sources


def materialize_mcnamara_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    """Materialize the historical McNamara calibrated length constructions."""
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    out: dict[str, ConstructionEvidence] = {}
    for spec in _MCNAMARA_SPECS:
        refs, missing, sources = _resolve_landmark_dependencies(
            landmarks, spec.required_landmark_ids
        )
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


def materialize_mcnamara_nperp_constructions(
    landmarks: Mapping[str, LandmarkEvidence], *, construction_namespace: str
) -> dict[str, ConstructionEvidence]:
    """Materialize source-locked McNamara A/Pog distances to N-perpendicular.

    Frankfort is anatomical Po->Or. N-perpendicular passes through N and is
    perpendicular to Frankfort. The signed AP distance is the projection of
    target-N on the Po->Or unit axis: positive anterior, negative posterior.
    """
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    out: dict[str, ConstructionEvidence] = {}
    source_refs = [*MCNAMARA_SOURCE_REFERENCES, MCNAMARA_NPERP_SECONDARY_REFERENCE]
    for spec in _MCNAMARA_NPERP_SPECS:
        refs, missing, sources = _resolve_landmark_dependencies(
            landmarks, spec.required_landmark_ids
        )
        geometry: dict[str, object] = {
            "kind": "signed_distance_to_nasion_perpendicular",
            "analysis": "MCNAMARA",
            "canonical_measurement_id": spec.canonical_id,
            "source_references": source_refs,
            "required_landmark_ids": list(spec.required_landmark_ids),
            "coordinate_space": "source_image_pixels",
            "frankfort_definition": "Po_anatomic-Or",
            "frankfort_orientation": "Po_to_Or",
            "reference_line": "N_perpendicular_to_FH",
            "sign_convention": "positive_anterior_negative_posterior",
        }

        availability = AvailabilityStatus.AVAILABLE
        if missing:
            availability = AvailabilityStatus.NOT_COMPUTABLE
        elif len(sources) != 1:
            availability = AvailabilityStatus.INVALID
        else:
            target_id, nasion_id, po_id, or_id = spec.required_landmark_ids
            axis = frankfort_axis_v1(_point(landmarks, po_id), _point(landmarks, or_id))
            distance_px = signed_axis_distance_px_v1(
                _point(landmarks, target_id), _point(landmarks, nasion_id), axis
            )
            if distance_px is None:
                availability = AvailabilityStatus.INVALID
            else:
                geometry.update(
                    {
                        "computed_signed_distance_px": distance_px,
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
    """Adapt the historical McNamara calibrated length subset."""
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    presence = [
        spec.construction_definition_id in constructions for spec in _MCNAMARA_SPECS
    ]
    if not any(presence):
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


def adapt_mcnamara_nperp_measurements(
    *,
    measurement_namespace: str,
    constructions: Mapping[str, ConstructionEvidence],
    mm_per_pixel: Optional[float],
    calibration_ref: Optional[str],
) -> list[MeasurementEvidence]:
    """Adapt the two source-locked canonical McNamara N-perp measurements."""
    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")

    presence = [
        spec.construction_definition_id in constructions
        for spec in _MCNAMARA_NPERP_SPECS
    ]
    if not any(presence):
        return []
    if not all(presence):
        raise ValueError("Partial McNamara N-perp construction set is not certified")

    calibration_available = isinstance(calibration_ref, str) and bool(calibration_ref.strip())
    ratio_valid = _valid_ratio(mm_per_pixel)
    out: list[MeasurementEvidence] = []
    for spec in _MCNAMARA_NPERP_SPECS:
        if canonical_unit(spec.canonical_id) != "mm":
            raise ValueError(
                f"Canonical unit is not source-locked to mm for {spec.canonical_id}"
            )
        construction = constructions[spec.construction_definition_id]
        if construction.definition_id != spec.construction_definition_id:
            raise ValueError(
                f"Construction key {spec.construction_definition_id} resolves to {construction.definition_id}"
            )

        availability = construction.availability_status
        value: Optional[float] = None
        if availability == AvailabilityStatus.AVAILABLE:
            distance_px = construction.geometry.get("computed_signed_distance_px")
            if not isinstance(distance_px, (int, float)) or not math.isfinite(float(distance_px)):
                raise ValueError(
                    f"Available McNamara N-perp construction {spec.construction_definition_id} lacks a valid signed distance"
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
                method_id=spec.canonical_id,
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
MCNAMARA_NPERP_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _MCNAMARA_NPERP_SPECS
)
