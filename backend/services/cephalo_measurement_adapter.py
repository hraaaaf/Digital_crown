"""Adapter from legacy cephalo geometry payloads to typed measurement evidence.

Only the CRANIOM linear measurements whose backend constructions are already
versioned are adapted here. No norm, interpretation, diagnosis or treatment
logic is copied from the legacy payload.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from backend.schemas.cephalo_evidence import AvailabilityStatus, MeasurementEvidence
from backend.schemas.clinical import CephaloAnalysisResult


@dataclass(frozen=True)
class _MeasurementSpec:
    metric_name: str
    method_id: str
    construction_definition_id: str


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


def _required_construction_ref(
    construction_refs: Mapping[str, str], definition_id: str
) -> str:
    ref = construction_refs.get(definition_id)
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError(
            f"Missing materialized construction evidence for {definition_id}"
        )
    return ref


def adapt_craniom_linear_measurements(
    result: CephaloAnalysisResult,
    *,
    measurement_namespace: str,
    construction_refs: Mapping[str, str],
    calibration_ref: Optional[str],
) -> list[MeasurementEvidence]:
    """Convert certified CRANIOM linear geometry into typed evidence.

    A patient value is emitted only when both the runtime payload has a valid
    positive pixel ratio and a calibration evidence reference is supplied.
    Otherwise the measurement is retained explicitly as ``NOT_COMPUTABLE``.
    """

    if not isinstance(measurement_namespace, str) or not measurement_namespace.strip():
        raise ValueError("measurement_namespace must be non-empty")
    if result.analysis_metadata.type != "COM_Skeletal":
        raise ValueError(
            f"Unsupported cephalo payload type for CRANIOM adapter: {result.analysis_metadata.type}"
        )

    ratio_valid = _valid_ratio(result.analysis_metadata.pixel_ratio)
    calibration_available = isinstance(calibration_ref, str) and bool(calibration_ref.strip())
    skeletal = result.metrics.analyse_osseuse
    adapted: list[MeasurementEvidence] = []

    for spec in _CRANIOM_LINEAR_SPECS:
        construction_ref = _required_construction_ref(
            construction_refs, spec.construction_definition_id
        )
        raw_value = getattr(skeletal, spec.metric_name).valeur

        availability = AvailabilityStatus.AVAILABLE
        value: Optional[float] = raw_value
        if raw_value is not None and not math.isfinite(raw_value):
            availability = AvailabilityStatus.INVALID
            value = None
        elif raw_value is None or not ratio_valid or not calibration_available:
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
