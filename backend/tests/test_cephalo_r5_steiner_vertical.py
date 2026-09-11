from __future__ import annotations

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_steiner_geometry import steiner_sn_mp_deg_v1
from backend.services.cephalo_steiner_vertical_evidence import (
    STEINER_SN_MP_CONSTRUCTION_ID,
    STEINER_SN_MP_METHOD_ID,
    adapt_steiner_vertical_measurements,
    materialize_steiner_vertical_constructions,
)


def _lm(landmark_id: str, x: float, y: float, source: str = "source:ceph:1") -> LandmarkEvidence:
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


def _landmarks() -> dict[str, LandmarkEvidence]:
    return {
        "S": _lm("S", 10.0, 10.0),
        "N": _lm("N", 20.0, 10.0),
        "Go": _lm("Go", 14.0, 50.0),
        "Gn": _lm("Gn", 34.0, 62.0),
    }


def test_sn_mp_uses_smallest_orientation_invariant_sn_to_gogn_angle():
    s = (10.0, 10.0)
    n = (20.0, 10.0)
    go = (14.0, 50.0)
    gn = (34.0, 62.0)
    expected = 30.9637565321
    assert steiner_sn_mp_deg_v1(s, n, go, gn) == pytest.approx(expected)
    assert steiner_sn_mp_deg_v1(n, s, go, gn) == pytest.approx(expected)
    assert steiner_sn_mp_deg_v1(s, n, gn, go) == pytest.approx(expected)


def test_sn_mp_typed_evidence_is_uncalibrated_and_source_bound():
    constructions = materialize_steiner_vertical_constructions(
        _landmarks(), construction_namespace="construction:steiner:vertical:1"
    )
    construction = constructions[STEINER_SN_MP_CONSTRUCTION_ID]
    assert construction.availability_status == AvailabilityStatus.AVAILABLE
    assert construction.geometry["reference_axis"] == "S-N"
    assert construction.geometry["mandibular_plane"] == "Go-Gn"
    assert construction.geometry["axis_orientation_invariant"] is True

    measurements = adapt_steiner_vertical_measurements(
        measurement_namespace="measurement:steiner:vertical:1",
        constructions=constructions,
    )
    assert len(measurements) == 1
    measurement = measurements[0]
    assert measurement.analysis_id == "STEINER"
    assert measurement.method_id == STEINER_SN_MP_METHOD_ID
    assert measurement.unit == "deg"
    assert measurement.requires_calibration is False
    assert measurement.calibration_ref is None
    assert measurement.availability_status == AvailabilityStatus.AVAILABLE


def test_sn_mp_fails_closed_on_missing_cross_image_and_degenerate_geometry():
    missing = _landmarks()
    missing.pop("Gn")
    construction = materialize_steiner_vertical_constructions(
        missing, construction_namespace="construction:steiner:vertical:2"
    )[STEINER_SN_MP_CONSTRUCTION_ID]
    assert construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE

    mixed = _landmarks()
    mixed["Gn"] = _lm("Gn", 34.0, 62.0, source="source:other")
    construction = materialize_steiner_vertical_constructions(
        mixed, construction_namespace="construction:steiner:vertical:3"
    )[STEINER_SN_MP_CONSTRUCTION_ID]
    assert construction.availability_status == AvailabilityStatus.INVALID

    degenerate = _landmarks()
    degenerate["N"] = _lm("N", 10.0, 10.0)
    construction = materialize_steiner_vertical_constructions(
        degenerate, construction_namespace="construction:steiner:vertical:4"
    )[STEINER_SN_MP_CONSTRUCTION_ID]
    assert construction.availability_status == AvailabilityStatus.INVALID
