from __future__ import annotations

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_mcnamara_evidence import (
    MCNAMARA_CONSTRUCTION_DEFINITIONS,
    adapt_mcnamara_measurements,
    materialize_mcnamara_constructions,
)
from backend.services.cephalo_mcnamara_geometry import (
    mcnamara_ans_me_mm_v1,
    mcnamara_co_a_mm_v1,
    mcnamara_co_gn_mm_v1,
)


def _landmark(landmark_id: str, x: float, y: float, *, source: str = "source:ceph:1"):
    return LandmarkEvidence(
        evidence_id=f"landmark:{landmark_id}",
        landmark_id=landmark_id,
        x=x,
        y=y,
        source_image_ref=source,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _landmarks():
    return {
        "Co": _landmark("Co", 0.0, 0.0),
        "A": _landmark("A", 3.0, 4.0),
        "Gn": _landmark("Gn", 6.0, 8.0),
        "ANS": _landmark("ANS", 2.0, 1.0),
        "Me": _landmark("Me", 2.0, 7.0),
    }


def test_mcnamara_linear_geometry_requires_valid_calibration_and_fails_closed():
    assert mcnamara_co_a_mm_v1((0, 0), (3, 4), 0.2) == pytest.approx(1.0)
    assert mcnamara_co_gn_mm_v1((0, 0), (6, 8), 0.2) == pytest.approx(2.0)
    assert mcnamara_ans_me_mm_v1((2, 1), (2, 7), 0.2) == pytest.approx(1.2)

    assert mcnamara_co_a_mm_v1((0, 0), (3, 4), None) is None
    assert mcnamara_co_a_mm_v1((0, 0), (3, 4), 0.0) is None
    assert mcnamara_co_a_mm_v1((0, 0), (0, 0), 0.2) is None


def test_mcnamara_constructions_are_source_bound_and_measurements_need_calibration_evidence():
    constructions = materialize_mcnamara_constructions(
        _landmarks(), construction_namespace="construction:mcnamara:1"
    )
    assert set(constructions) == set(MCNAMARA_CONSTRUCTION_DEFINITIONS)
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in constructions.values())
    assert all(item.geometry["analysis"] == "MCNAMARA" for item in constructions.values())

    uncalibrated = adapt_mcnamara_measurements(
        measurement_namespace="measurement:mcnamara:1",
        constructions=constructions,
        mm_per_pixel=None,
        calibration_ref=None,
    )
    assert all(item.analysis_id == "MCNAMARA" for item in uncalibrated)
    assert all(item.requires_calibration is True for item in uncalibrated)
    assert all(item.availability_status == AvailabilityStatus.NOT_COMPUTABLE for item in uncalibrated)
    assert all(item.value is None for item in uncalibrated)
    assert all(item.calibration_ref is None for item in uncalibrated)

    calibrated = adapt_mcnamara_measurements(
        measurement_namespace="measurement:mcnamara:2",
        constructions=constructions,
        mm_per_pixel=0.2,
        calibration_ref="source:calibration:1",
    )
    assert [item.method_id for item in calibrated] == [
        "MCNAMARA_CO_A_MM_V1",
        "MCNAMARA_CO_GN_MM_V1",
        "MCNAMARA_ANS_ME_MM_V1",
    ]
    assert [item.value for item in calibrated] == pytest.approx([1.0, 2.0, 1.2])
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in calibrated)
    assert all(item.calibration_ref == "source:calibration:1" for item in calibrated)


def test_mcnamara_rejects_partial_calibration_contract():
    constructions = materialize_mcnamara_constructions(
        _landmarks(), construction_namespace="construction:mcnamara:partial"
    )

    ratio_without_evidence = adapt_mcnamara_measurements(
        measurement_namespace="measurement:mcnamara:ratio-only",
        constructions=constructions,
        mm_per_pixel=0.2,
        calibration_ref=None,
    )
    assert all(item.availability_status == AvailabilityStatus.INVALID for item in ratio_without_evidence)
    assert all(item.value is None for item in ratio_without_evidence)

    evidence_without_ratio = adapt_mcnamara_measurements(
        measurement_namespace="measurement:mcnamara:evidence-only",
        constructions=constructions,
        mm_per_pixel=None,
        calibration_ref="source:calibration:1",
    )
    assert all(item.availability_status == AvailabilityStatus.INVALID for item in evidence_without_ratio)
    assert all(item.value is None for item in evidence_without_ratio)


def test_mcnamara_pre_r8_snapshot_is_optional_but_partial_construction_set_is_rejected():
    assert adapt_mcnamara_measurements(
        measurement_namespace="measurement:mcnamara:legacy",
        constructions={},
        mm_per_pixel=0.2,
        calibration_ref="source:calibration:1",
    ) == []

    constructions = materialize_mcnamara_constructions(
        _landmarks(), construction_namespace="construction:mcnamara:partial-set"
    )
    constructions.pop("MCNAMARA_ANS_ME_V1")
    with pytest.raises(ValueError, match="Partial McNamara construction set"):
        adapt_mcnamara_measurements(
            measurement_namespace="measurement:mcnamara:partial-set",
            constructions=constructions,
            mm_per_pixel=0.2,
            calibration_ref="source:calibration:1",
        )


def test_mcnamara_missing_cross_image_and_degenerate_segments_fail_closed():
    missing = _landmarks()
    missing.pop("A")
    constructions = materialize_mcnamara_constructions(
        missing, construction_namespace="construction:mcnamara:missing"
    )
    assert constructions["MCNAMARA_CO_A_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["MCNAMARA_CO_GN_V1"].availability_status == AvailabilityStatus.AVAILABLE

    mixed = _landmarks()
    mixed["A"] = _landmark("A", 3.0, 4.0, source="source:ceph:other")
    constructions = materialize_mcnamara_constructions(
        mixed, construction_namespace="construction:mcnamara:mixed"
    )
    assert constructions["MCNAMARA_CO_A_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["MCNAMARA_CO_GN_V1"].availability_status == AvailabilityStatus.AVAILABLE

    degenerate = _landmarks()
    degenerate["A"] = _landmark("A", 0.0, 0.0)
    constructions = materialize_mcnamara_constructions(
        degenerate, construction_namespace="construction:mcnamara:degenerate"
    )
    assert constructions["MCNAMARA_CO_A_V1"].availability_status == AvailabilityStatus.INVALID
