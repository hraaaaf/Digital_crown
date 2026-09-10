"""Adapter from legacy cephalometric runtime output to typed measurement evidence.

Only the CRANIOM linear constructions already versioned in the geometry registry
are adapted here. The adapter does not apply norms, create findings, diagnose,
or propose treatment.

Construction evidence and calibration evidence refs are supplied explicitly by
the caller. The adapter never invents graph references from a metric name and
refuses a construction whose registered definition does not match the metric.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    MeasurementEvidence,
)
from backend.schemas.clinical import CephaloAnalysisResult, MeasureData


class CephaloMeasurementEvidenceAdapterError(ValueError):
    """Raised when runtime output cannot be represented safely as evidence."""


@dataclass(frozen=True)
class _MetricContract:
    result_field: str
    construction_definition_id: str
    method_id: str
    method_version: str = "1"
    unit: str = "mm"


_CRANIOM_LINEAR_CONTRACTS: Tuple[_MetricContract, ...] = (
    _MetricContract(
        "Situation_A",
        "CRANIOM_A_TO_N_VERTICAL_V1",
        "CRANIOM_A_TO_N_VERTICAL_V1",
    ),
    _MetricContract(
        "Situation_B",
        "CRANIOM_B_TO_N_VERTICAL_V1",
        "CRANIOM_B_TO_N_VERTICAL_V1",
    ),
    _MetricContract(
        "Decalage_A_B",
        "CRANIOM_AB_PRIME_V1",
        "CRANIOM_AB_PRIME_V1",
    ),
    _MetricContract(
        "Profondeur_Faciale",
        "CRANIOM_S_TO_N_VERTICAL_DEPTH_V1",
        "CRANIOM_S_TO_N_VERTICAL_DEPTH_V1",
    ),
)


def _require_nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CephaloMeasurementEvidenceAdapterError(f"{name} must be non-empty")


def _valid_ratio(value: Optional[float]) -> bool:
    return value is not None and math.isfinite(value) and value > 0


def _metric_from_result(result: CephaloAnalysisResult, field: str) -> MeasureData:
    metric = getattr(result.metrics.analyse_osseuse, field, None)
    if not isinstance(metric, MeasureData):
        raise CephaloMeasurementEvidenceAdapterError(
            f"Missing CRANIOM runtime metric: {field}"
        )
    return metric


def adapt_craniom_linear_measurements(
    result: CephaloAnalysisResult,
    *,
    analysis_instance_id: str,
    constructions: Mapping[str, ConstructionEvidence],
    calibration_ref: Optional[str],
) -> list[MeasurementEvidence]:
    """Convert versioned CRANIOM linear runtime metrics into typed evidence.

    ``constructions`` is keyed by the runtime result field and contains the real
    `ConstructionEvidence` instances already created for that analysis. The
    construction's `definition_id` and `definition_version` must match the metric
    contract before its id can be referenced by a `MeasurementEvidence`.

    Available millimetric values require both a valid runtime pixel ratio and an
    explicit calibration evidence reference. Missing runtime values become
    ``NOT_COMPUTABLE`` and remain value-less; they are never converted to zero.
    """

    _require_nonempty(analysis_instance_id, "analysis_instance_id")
    if result.analysis_metadata.type != "COM_Skeletal":
        raise CephaloMeasurementEvidenceAdapterError(
            "CRANIOM adapter only accepts COM_Skeletal runtime results"
        )

    output: list[MeasurementEvidence] = []
    for contract in _CRANIOM_LINEAR_CONTRACTS:
        construction = constructions.get(contract.result_field)
        if construction is None:
            raise CephaloMeasurementEvidenceAdapterError(
                f"Missing explicit construction evidence for {contract.result_field}"
            )
        if construction.definition_id != contract.construction_definition_id:
            raise CephaloMeasurementEvidenceAdapterError(
                f"Construction for {contract.result_field} is {construction.definition_id!r}, "
                f"expected {contract.construction_definition_id!r}"
            )
        if construction.definition_version != contract.method_version:
            raise CephaloMeasurementEvidenceAdapterError(
                f"Construction version for {contract.result_field} is "
                f"{construction.definition_version!r}, expected {contract.method_version!r}"
            )
        construction_ref = construction.construction_id
        _require_nonempty(construction_ref, f"construction id for {contract.result_field}")

        metric = _metric_from_result(result, contract.result_field)
        value = metric.valeur
        available = value is not None

        if available:
            if not _valid_ratio(result.analysis_metadata.pixel_ratio):
                raise CephaloMeasurementEvidenceAdapterError(
                    f"{contract.result_field} has a patient value without valid mm/pixel calibration"
                )
            if calibration_ref is None:
                raise CephaloMeasurementEvidenceAdapterError(
                    f"{contract.result_field} has a patient value without calibration_ref"
                )
            _require_nonempty(calibration_ref, "calibration_ref")

        evidence_refs = [construction_ref]
        if calibration_ref:
            evidence_refs.append(calibration_ref)

        output.append(
            MeasurementEvidence(
                measurement_id=f"measurement:{analysis_instance_id}:{contract.result_field}",
                analysis_id="CRANIOM",
                method_id=contract.method_id,
                method_version=contract.method_version,
                value=value if available else None,
                unit=contract.unit,
                construction_refs=[construction_ref],
                calibration_ref=calibration_ref if available else None,
                requires_calibration=True,
                evidence_refs=evidence_refs,
                availability_status=(
                    AvailabilityStatus.AVAILABLE
                    if available
                    else AvailabilityStatus.NOT_COMPUTABLE
                ),
            )
        )

    return output
