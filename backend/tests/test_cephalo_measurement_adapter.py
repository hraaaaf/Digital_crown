"""Contract tests for CRANIOM geometry -> MeasurementEvidence adaptation."""

import math

import pytest

from backend.schemas.cephalo_evidence import AvailabilityStatus, ConstructionEvidence
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_measurement_adapter import (
    CRANIOM_CONSTRUCTION_DEFINITIONS,
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
        "U1_apex": (20.0, 25.0),
        "U1_incisal": (24.0, 35.0),
        "L1_apex": (20.0, 48.0),
        "L1_incisal": (23.0, 38.0),
    }


def _constructions():
    constructions = {}
    for definition_id in CRANIOM_CONSTRUCTION_DEFINITIONS:
        geometry = {"kind": "synthetic_test_construction"}
        if definition_id == "CRANIOM_U1_TO_FRANKFORT_V1":
            geometry["computed_angle_deg"] = 111.8
        constructions[definition_id] = ConstructionEvidence(
            construction_id=f"construction:{definition_id}",
            definition_id=definition_id,
            definition_version="1",
            landmark_refs=["landmark:synthetic"],
            geometry=geometry,
            evidence_refs=["landmark:synthetic"],
        )
    return constructions


def _by_name(measurements):
    return {m.measurement_id.rsplit(":", 1)[1]: m for m in measurements}


def test_adapter_emits_certified_craniom_measurements_including_r4_u1_frankfort():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:42",
        constructions=_constructions(),
        calibration_ref="source:calibration:42",
    )

    assert [m.measurement_id for m in measurements] == [
        "cephalo:42:Situation_A",
        "cephalo:42:Situation_B",
        "cephalo:42:Decalage_A_B",
        "cephalo:42:Profondeur_Faciale",
        "cephalo:42:I_Francfort",
    ]
    assert all(m.analysis_id == "CRANIOM" for m in measurements)
    assert all(m.availability_status == AvailabilityStatus.AVAILABLE for m in measurements)

    by_name = _by_name(measurements)
    for name in ("Situation_A", "Situation_B", "Decalage_A_B", "Profondeur_Faciale"):
        assert by_name[name].unit == "mm"
        assert by_name[name].requires_calibration is True
        assert by_name[name].calibration_ref == "source:calibration:42"
    assert by_name["I_Francfort"].unit == "deg"
    assert by_name["I_Francfort"].requires_calibration is False
    assert by_name["I_Francfort"].calibration_ref is None
    assert by_name["I_Francfort"].value == 111.8
    assert by_name["I_Francfort"].value == result.metrics.analyse_dentaire.I_Francfort.valeur


def test_without_calibration_only_linear_values_are_not_computable():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:43",
        constructions=_constructions(),
        calibration_ref=None,
    )

    by_name = _by_name(measurements)
    for name in ("Situation_A", "Situation_B", "Decalage_A_B", "Profondeur_Faciale"):
        assert by_name[name].value is None
        assert by_name[name].availability_status == AvailabilityStatus.NOT_COMPUTABLE
        assert by_name[name].calibration_ref is None
    assert by_name["I_Francfort"].value == 111.8
    assert by_name["I_Francfort"].availability_status == AvailabilityStatus.AVAILABLE
    assert by_name["I_Francfort"].calibration_ref is None


def test_missing_pixel_ratio_does_not_block_uncalibrated_angular_measurement():
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:44",
        constructions=_constructions(),
        calibration_ref=None,
    )

    by_name = _by_name(measurements)
    assert all(
        by_name[name].availability_status == AvailabilityStatus.NOT_COMPUTABLE
        for name in ("Situation_A", "Situation_B", "Decalage_A_B", "Profondeur_Faciale")
    )
    assert by_name["I_Francfort"].availability_status == AvailabilityStatus.AVAILABLE
    assert by_name["I_Francfort"].value == 111.8


def test_u1_runtime_value_must_match_typed_construction_geometry():
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(_points())
    result.metrics.analyse_dentaire.I_Francfort.valeur = 99.9

    with pytest.raises(ValueError, match="Runtime I_Francfort does not match"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="cephalo:44b",
            constructions=_constructions(),
            calibration_ref=None,
        )


def test_adapter_requires_materialized_construction_evidence():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    constructions = _constructions()
    constructions.pop("CRANIOM_AB_PRIME_V1")

    with pytest.raises(ValueError, match="CRANIOM_AB_PRIME_V1"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="cephalo:45",
            constructions=constructions,
            calibration_ref="source:calibration:45",
        )


def test_adapter_rejects_wrong_construction_definition():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    constructions = _constructions()
    constructions["CRANIOM_AB_PRIME_V1"] = constructions[
        "CRANIOM_AB_PRIME_V1"
    ].model_copy(update={"definition_id": "OTHER_CONSTRUCTION"})

    with pytest.raises(ValueError, match="resolves to definition OTHER_CONSTRUCTION"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="cephalo:45b",
            constructions=constructions,
            calibration_ref="source:calibration:45b",
        )


def test_adapter_rejects_wrong_construction_version():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    constructions = _constructions()
    constructions["CRANIOM_AB_PRIME_V1"] = constructions[
        "CRANIOM_AB_PRIME_V1"
    ].model_copy(update={"definition_version": "2"})

    with pytest.raises(ValueError, match="not certified version 1"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="cephalo:45c",
            constructions=constructions,
            calibration_ref="source:calibration:45c",
        )


def test_unavailable_construction_makes_only_dependent_measurement_not_computable():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    constructions = _constructions()
    constructions["CRANIOM_AB_PRIME_V1"] = constructions[
        "CRANIOM_AB_PRIME_V1"
    ].model_copy(update={"availability_status": AvailabilityStatus.NOT_COMPUTABLE})

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:45d",
        constructions=constructions,
        calibration_ref="source:calibration:45d",
    )

    by_name = _by_name(measurements)
    assert by_name["Decalage_A_B"].value is None
    assert by_name["Decalage_A_B"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert by_name["Situation_A"].availability_status == AvailabilityStatus.AVAILABLE
    assert by_name["Situation_B"].availability_status == AvailabilityStatus.AVAILABLE
    assert by_name["Profondeur_Faciale"].availability_status == AvailabilityStatus.AVAILABLE
    assert by_name["I_Francfort"].availability_status == AvailabilityStatus.AVAILABLE


def test_unavailable_u1_construction_blocks_only_u1_measurement():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    constructions = _constructions()
    constructions["CRANIOM_U1_TO_FRANKFORT_V1"] = constructions[
        "CRANIOM_U1_TO_FRANKFORT_V1"
    ].model_copy(update={"availability_status": AvailabilityStatus.NOT_COMPUTABLE})

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:45e",
        constructions=constructions,
        calibration_ref="source:calibration:45e",
    )
    by_name = _by_name(measurements)
    assert by_name["I_Francfort"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert by_name["I_Francfort"].value is None
    assert all(
        by_name[name].availability_status == AvailabilityStatus.AVAILABLE
        for name in ("Situation_A", "Situation_B", "Decalage_A_B", "Profondeur_Faciale")
    )


def test_adapter_rejects_empty_namespace():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())

    with pytest.raises(ValueError, match="measurement_namespace"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="",
            constructions=_constructions(),
            calibration_ref="source:calibration:46",
        )


def test_adapter_rejects_non_mm_payload_unit():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    result.analysis_metadata.unit = "px"

    with pytest.raises(ValueError, match="Unsupported cephalo payload unit"):
        adapt_craniom_linear_measurements(
            result,
            measurement_namespace="cephalo:46b",
            constructions=_constructions(),
            calibration_ref="source:calibration:46b",
        )


def test_adapter_marks_nonfinite_legacy_value_invalid_instead_of_forwarding_it():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    result.metrics.analyse_osseuse.Situation_A.valeur = float("nan")

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:47",
        constructions=_constructions(),
        calibration_ref="source:calibration:47",
    )

    situation_a = measurements[0]
    assert situation_a.value is None
    assert situation_a.availability_status == AvailabilityStatus.INVALID
    assert all(
        measurement.value is None or math.isfinite(measurement.value)
        for measurement in measurements
    )
