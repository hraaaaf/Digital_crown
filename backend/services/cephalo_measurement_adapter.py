"""Adapter from cephalo geometry payloads to typed CRANIOM measurement evidence.

Only measurements backed by versioned constructions are adapted here. No norm,
interpretation, diagnosis or treatment logic is copied from the legacy payload.
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
    metric_group: str
    method_id: str
    construction_definition_id: str
    unit: str
    requires_calibration: bool
    compatibility_optional: bool = False
    construction_definition_version: str = "1"


_CRANIOM_LINEAR_SPECS: Sequence[_MeasurementSpec] = (
    _MeasurementSpec(
        metric_name="Situation_A",
        metric_group="skeletal",
        method_id="CRANIOM_SITUATION_A_MM_V1",
        construction_definition_id="CRANIOM_A_TO_N_VERTICAL_V1",
        unit="mm",
        requires_calibration=True,
    ),
    _MeasurementSpec(
        metric_name="Situation_B",
        metric_group="skeletal",
        method_id="CRANIOM_SITUATION_B_MM_V1",
        construction_definition_id="CRANIOM_B_TO_N_VERTICAL_V1",
        unit="mm",
        requires_calibration=True,
    ),
    _MeasurementSpec(
        metric_name="Decalage_A_B",
        metric_group="skeletal",
        method_id="CRANIOM_AB_PRIME_MM_V1",
        construction_definition_id="CRANIOM_AB_PRIME_V1",
        unit="mm",
        requires_calibration=True,
    ),
    _MeasurementSpec(
        metric_name="Profondeur_Faciale",
        metric_group="skeletal",
        method_id="CRANIOM_FACIAL_DEPTH_MM_V1",
        construction_definition_id="CRANIOM_S_TO_N_VERTICAL_DEPTH_V1",
        unit="mm",
        requires_calibration=True,
    ),
)

_CRANIOM_ANGULAR_SPECS: Sequence[_MeasurementSpec] = (
    _MeasurementSpec(
        metric_name="I_Francfort",
        metric_group="dental",
        method_id="CRANIOM_U1_FRANKFORT_DEG_V1",
        construction_definition_id="CRANIOM_U1_TO_FRANKFORT_V1",
        unit="deg",
        requires_calibration=False,
        compatibility_optional=True,
    ),
)

_CRANIOM_SPECS: Sequence[_MeasurementSpec] = (
    *_CRANIOM_LINEAR_SPECS,
    *_CRANIOM_ANGULAR_SPECS,
)


def _valid_ratio(value: Optional[float]) -> bool:
    return value is not None and math.isfinite(value) and value > 0


def _required_construction(
    constructions: Mapping[str, ConstructionEvidence], spec: _MeasurementSpec
) -> Optional[ConstructionEvidence]:
    construction = constructions.get(spec.construction_definition_id)
    if construction is None:
        if spec.compatibility_optional:
            return None
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


def _raw_value(result: CephaloAnalysisResult, spec: _MeasurementSpec) -> Optional[float]:
    if spec.metric_group == "skeletal":
        group = result.metrics.analyse_osseuse
    elif spec.metric_group == "dental":
        group = result.metrics.analyse_dentaire
    else:
        raise ValueError(f"Unsupported CRANIOM metric group: {spec.metric_group}")
    return getattr(group, spec.metric_name).valeur


def _verified_angular_value(
    spec: _MeasurementSpec,
    construction: ConstructionEvidence,
    raw_value: Optional[float],
) -> float:
    computed = construction.geometry.get("computed_angle_deg")
    if not isinstance(computed, (int, float)) or not math.isfinite(float(computed)):
        raise ValueError(
            f"Available construction {spec.construction_definition_id} lacks finite computed_angle_deg"
        )
    computed_value = float(computed)
    if raw_value is None or not math.isfinite(raw_value) or not math.isclose(
        raw_value, computed_value, rel_tol=0.0, abs_tol=1e-12
    ):
        raise ValueError(
            f"Runtime {spec.metric_name} does not match typed construction geometry"
        )
    return computed_value


def adapt_craniom_measurements(
    result: CephaloAnalysisResult,
    *,
    measurement_namespace: str,
    constructions: Mapping[str, ConstructionEvidence],
    calibration_ref: Optional[str],
) -> list[MeasurementEvidence]:
    """Convert the certified CRANIOM geometry set into typed evidence.

    The R4 angular construction is compatibility-optional only so persisted R3
    snapshots can still undergo calibration-only revisions without fabricating a
    construction that did not exist in that snapshot. New R4 snapshots always
    materialize it through the construction adapter.
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
    adapted: list[MeasurementEvidence] = []

    for spec in _CRANIOM_SPECS:
        construction = _required_construction(constructions, spec)
        if construction is None:
            continue
        construction_ref = construction.construction_id
        raw_value = _raw_value(result, spec)

        availability = AvailabilityStatus.AVAILABLE
        value: Optional[float] = raw_value
        if construction.availability_status != AvailabilityStatus.AVAILABLE:
            availability = AvailabilityStatus.NOT_COMPUTABLE
            value = None
        elif spec.requires_calibration:
            if raw_value is not None and not math.isfinite(raw_value):
                availability = AvailabilityStatus.INVALID
                value = None
            elif raw_value is None or not ratio_valid or not calibration_available:
                availability = AvailabilityStatus.NOT_COMPUTABLE
                value = None
        else:
            value = _verified_angular_value(spec, construction, raw_value)

        evidence_refs = [construction_ref]
        effective_calibration_ref: Optional[str] = None
        if spec.requires_calibration and calibration_available:
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
                unit=spec.unit,
                construction_refs=[construction_ref],
                calibration_ref=effective_calibration_ref,
                requires_calibration=spec.requires_calibration,
                evidence_refs=evidence_refs,
                availability_status=availability,
            )
        )

    return adapted


def adapt_craniom_linear_measurements(
    result: CephaloAnalysisResult,
    *,
    measurement_namespace: str,
    constructions: Mapping[str, ConstructionEvidence],
    calibration_ref: Optional[str],
) -> list[MeasurementEvidence]:
    """Backward-compatible entry point returning the certified CRANIOM set."""

    return adapt_craniom_measurements(
        result,
        measurement_namespace=measurement_namespace,
        constructions=constructions,
        calibration_ref=calibration_ref,
    )


CRANIOM_LINEAR_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _CRANIOM_LINEAR_SPECS
)
CRANIOM_ANGULAR_CONSTRUCTION_DEFINITIONS = tuple(
    spec.construction_definition_id for spec in _CRANIOM_ANGULAR_SPECS
)
CRANIOM_CONSTRUCTION_DEFINITIONS = (
    *CRANIOM_LINEAR_CONSTRUCTION_DEFINITIONS,
    *CRANIOM_ANGULAR_CONSTRUCTION_DEFINITIONS,
)
