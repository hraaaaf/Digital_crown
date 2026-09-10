"""Adapter from legacy cephalo geometry payloads to typed measurement evidence.

Only the CRANIOM linear measurements whose backend constructions are already
versioned are adapted here. No norm, interpretation, diagnosis or treatment
logic is copied from the legacy payload.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    MeasurementEvidence,
)
from backend.schemas.clinical import CephaloAnalysisResult


@dataclass(frozen=True)
class _MeasurementSpec:
    metric_name: str
    method_id: str
    construction_definition_id: str
    construction_definition_version: str = "1"


_CRANIOM_LINEAR_SPECS: Sequence[_MeasurementSpec] = (
    _MeasurementSpec(
        metric_name="Situation_A",
        method_id="CRANIOM_SITUATION_A_MM_V1",
        construction_definition_id="CRANIOM_A_TO_N_VERTICAL_V1",
    ),
    _MeasurementSpec(
        metric_name="Situation_B",
        method_id="CRANIOM_SITUATION_B_MM_V1",
        construction_definition_id="CRANIOM_B_TO_N_VERTICAL_V1",
    ),
    _MeasurementSpec(
        metric_name="Decalage_A_B",
        method_id="CRANIOM_AB_PRIME_MM_V1",
        construction_definition_id="CRANIOM_AB_PRIME_V1",
    ),
    _MeasurementSpec(
        metric_name="Profondeur_Faciale",
        method_id="CRANIOM_FACIAL_DEPTH_MM_V1",
        construction_definition_id="CRANIOM_S_TO_N_VERTICAL_DEPTH_V1",
    ),
)


def _valid_ratio(value: Optional[float]) -> bool:
    return value is not None and math.isfinite(value) and value > 0


def _required_construction(
    constructions: Mapping[str, ConstructionEvidence], spec: _MeasurementSpec
) -> ConstructionEvidence:
    construction = constructions.get(spec.construction_definition_id)
    if construction is None:
        raise ValueError(
            "Missing materialized construction evidence for "
            f"{spec.construction_definition_id}"
        )
    if construction.definition_id != spec.construction_definition_id:
        raise ValueError(
            f"Construction key {spec.construction_definition_id} resolves to "
            f"definition {construction.definition_id}"
        )
    if construction.definition_version != spec.construction_definition_version:
        raise ValueError(
            f"Construction {spec.construction_definition_id} version "
            f"{construction.definition_version} is not certified version "
            f"{spec.construction_definition_version}"
        )
    return construction


def adapt_craniom_linear_measurements(
    result: CephaloAnalysisResult,
    *,
    measurement_namespace: str,
    constructions: Mapping[str, ConstructionEvidence],
    calibration_ref: Optional[str],
) -> list[MeasurementEvidence]:
    """Convert certified CRANIOM linear geometry into typed evidence.

    A patient value is emitted only when the runtime payload is millimetric,
    carries a valid positive pixel ratio, has a calibration evidence reference,
    and the required materialized construction is available.
    """

    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")
    if result.analysis_metadata.type != "COM_Skeletal":
        raise ValueError(
            f"Unsupported cephalo payload type for CRANIOM adapter: {result.analysis_metadata.type}"
        )
    if result.analysis_metadata.unit != "mm":
        raise ValueError(
            f"Unsupported cephalo payload unit for CRANIOM adapter: {result.analysis_metadata.unit}"
        )

    ratio_valid = _valid_ratio(result.analysis_metadata.pixel_ratio)
    calibration_available = isinstance(calibration_ref, str) and bool(calibration_ref.strip())
    skeletal = result.metrics.analyse_osseuse
    adapted: list[MeasurementEvidence] = []

    for spec in _CRANIOM_LINEAR_SPECS:
        construction = _required_construction(constructions, spec)
        construction_ref = construction.construction_id
        raw_value = getattr(skeletal, spec.metric_name).valeur

        availability = AvailabilityStatus.AVAILABLE
        value: Optional[float] = raw_value
        if raw_value is not None and not math.isfinite(raw_value):
            availability = AvailabilityStatus.INVALID
            value = None
        elif (
            raw_value is None
            or not ratio_valid
            or not calibration_available
            or construction.availability_status != AvailabilityStatus.AVAILABLE
        ):
            availability = AvailabilityStatus.NOT_COMPUTABLE
            value = None

        evidence_refs = [construction_ref]
        effective_calibration_ref: Optional[str] = None
        if calibration_available:
            assert calibration_ref is not None
            effective_calibration_ref = calibration_ref
            evidence_refs.append(calibration_ref)

        adapted.append(
            MeasurementEvidence(
                measurement_id=f"{measurement_namespace}:{spec.metric_name}",
                analysis_id="CRANIOM",
                method_id=spec.method_id,
                method_version="1",
                value=value,
                unit="mm",
                construction_refs=[construction_ref],
                calibration_ref=effective_calibration_ref,
                requires_calibration=True,
                evidence_refs=evidence_refs,
                availability_status=availability,
            )
        )

    return adapted


CRANIOM_LINEAR_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _CRANIOM_LINEAR_SPECS
)
