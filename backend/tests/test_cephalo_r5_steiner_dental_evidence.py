from __future__ import annotations

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_steiner_dental_evidence import (
    STEINER_DENTAL_CONSTRUCTION_DEFINITIONS,
    adapt_steiner_dental_measurements,
    materialize_steiner_dental_constructions,
)


def _lm(landmark_id: str, x: float, y: float, source: str = "source:ceph:1"):
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
        "N": _lm("N", 20.0, 10.0),
        "A": _lm("A", 24.0, 28.0),
        "B": _lm("B", 22.0, 38.0),
        "U1_apex": _lm("U1_apex", 20.0, 25.0),
        "U1_incisal": _lm("U1_incisal", 24.0, 35.0),
        "L1_apex": _lm("L1_apex", 20.0, 48.0),
        "L1_incisal": _lm("L1_incisal", 23.0, 38.0),
    }


def test_dental_constructions_and_measurements_are_typed_and_uncalibrated():
    constructions = materialize_steiner_dental_constructions(
        _landmarks(), construction_namespace="construction:steiner:dental:1"
    )
    assert set(constructions) == set(STEINER_DENTAL_CONSTRUCTION_DEFINITIONS)
    assert all(x.availability_status == AvailabilityStatus.AVAILABLE for x in constructions.values())
    assert all(x.geometry["axis_orientation_invariant"] is True for x in constructions.values())

    measurements = adapt_steiner_dental_measurements(
        measurement_namespace="measurement:steiner:dental:1",
        constructions=constructions,
    )
    assert [x.method_id for x in measurements] == [
        "STEINER_U1_NA_DEG_V1",
        "STEINER_L1_NB_DEG_V1",
    ]
    assert all(x.analysis_id == "STEINER" for x in measurements)
    assert all(x.unit == "deg" for x in measurements)
    assert all(x.requires_calibration is False for x in measurements)
    assert all(x.calibration_ref is None for x in measurements)


def test_dental_missing_and_cross_image_landmarks_fail_closed():
    missing = _landmarks()
    missing.pop("U1_apex")
    constructions = materialize_steiner_dental_constructions(
        missing, construction_namespace="construction:steiner:dental:2"
    )
    assert constructions["STEINER_U1_NA_ANGLE_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["STEINER_L1_NB_ANGLE_V1"].availability_status == AvailabilityStatus.AVAILABLE

    mixed = _landmarks()
    mixed["B"] = _lm("B", 22.0, 38.0, source="source:other")
    constructions = materialize_steiner_dental_constructions(
        mixed, construction_namespace="construction:steiner:dental:3"
    )
    assert constructions["STEINER_L1_NB_ANGLE_V1"].availability_status == AvailabilityStatus.INVALID
