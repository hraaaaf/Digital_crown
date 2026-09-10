"""Contract tests for CRANIOM geometry -> MeasurementEvidence adaptation."""

import math

import pytest

from backend.schemas.cephalo_evidence import AvailabilityStatus
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_measurement_adapter import (
    CRANIOM_LINEAR_CONSTRUCTION_DEFINITIONS,
    adapt_craniom_linear_measurements,
)


def _points():
    return {
        "S": (10.0, 10.0),
        "N": (20.0, 10.0),
        "Po": (0.0, 20.0),
        "Or": (20.0, 20.0),
        "A": (24.0, 28.0),
        "B": (22.0, 38.0),
        "Go": (5.0, 50.0),
        "Me": (25.0, 55.0),
        "U1a": (20.0, 25.0),
        "U1i": (24.0, 35.0),
        "L1a": (20.0, 48.0),
        "L1i": (23.0, 38.0),
    }


def _construction_refs():
    return {
        definition_id: f"construction:{definition_id}"
        for definition_id in CRANIOM_LINEAR_CONSTRUCTION_DEFINITIONS
    }


def test_adapter_emits_only_certified_craniom_linear_measurements():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:42",
        construction_refs=_construction_refs(),
        calibration_ref="source:calibration:42",
    )

    assert [m.measurement_id for m in measurements] == [
        "cephalo:42:Situation_A",
        "cephalo:42:Situation_B",
        "cephalo:42:Decalage_A_B",
        "cephalo:42:Profondeur_Faciale",
    ]
    assert all(m.analysis_id == "CRANIOM" for m in measurements)
    assert all(m.unit == "mm" for m in measurements)
    assert all(m.requires_calibration for m in measurements)
    assert all(m.availability_status == AvailabilityStatus.AVAILABLE for m in measurements)
    assert all(m.calibration_ref == "source:calibration:42" for m in measurements)

    expected = {
        "Situation_A": result.metrics.analyse_osseuse.Situation_A.valeur,
        "Situation_B": result.metrics.analyse_osseuse.Situation_B.valeur,
        "Decalage_A_B": result.metrics.analyse_osseuse.Decalage_A_B.valeur,
        "Profondeur_Faciale": result.metrics.analyse_osseuse.Profondeur_Faciale.valeur,
    }
    for measurement in measurements:
        metric_name = measurement.measurement_id.rsplit(":", 1)[1]
        assert measurement.value == expected[metric_name]


def test_adapter_drops_patient_values_without_calibration_evidence():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:43",
        construction_refs=_construction_refs(),
        calibration_ref=None,
    )

    assert all(m.value is None for m in measurements)
    assert all(m.calibration_ref is None for m in measurements)
    assert all(
        m.availability_status == AvailabilityStatus.NOT_COMPUTABLE
        for m in measurements
    )


def test_adapter_preserves_not_computable_geometry_from_runtime():
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:44",
        construction_refs=_construction_refs(),
        calibration_ref=None,
    )

    assert all(m.value is None for m in measurements)
    assert all(
        m.availability_status == AvailabilityStatus.NOT_COMPUTABLE
        for m in measurements
    )


def test_adapter_requires_materialized_construction_evidence():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    refs = _construction_refs()
    refs.pop("CRANIOM_AB_PRIME_V1")

    with pytest.raises(ValueError, match="CRANIOM_AB_PRIME_V1"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="cephalo:45",
            construction_refs=refs,
            calibration_ref="source:calibration:45",
        )


def test_adapter_rejects_empty_namespace():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())

    with pytest.raises(ValueError, match="measurement_namespace"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="",
            construction_refs=_construction_refs(),
            calibration_ref="source:calibration:46",
        )


def test_adapter_marks_nonfinite_legacy_value_invalid_instead_of_forwarding_it():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    result.metrics.analyse_osseuse.Situation_A.valeur = float("nan")

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:47",
        construction_refs=_construction_refs(),
        calibration_ref="source:calibration:47",
    )

    situation_a = measurements[0]
    assert situation_a.value is None
    assert situation_a.availability_status == AvailabilityStatus.INVALID
    assert all(
        measurement.value is None or math.isfinite(measurement.value)
        for measurement in measurements
    )
