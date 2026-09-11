from __future__ import annotations

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_downs_evidence import (
    DOWNS_CONSTRUCTION_DEFINITIONS,
    adapt_downs_measurements,
    materialize_downs_constructions,
)
from backend.services.cephalo_downs_geometry import (
    downs_facial_angle_deg_v1,
    downs_y_axis_deg_v1,
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
        "Po": _landmark("Po", 0.0, 0.0),
        "Or": _landmark("Or", 10.0, 0.0),
        "N": _landmark("N", 2.0, 2.0),
        "Pog": _landmark("Pog", 2.0, 12.0),
        "S": _landmark("S", 0.0, 2.0),
        "Gn": _landmark("Gn", 10.0, 12.0),
    }


def test_downs_geometry_is_orientation_and_mirror_invariant():
    facial = downs_facial_angle_deg_v1((0, 0), (10, 0), (2, 2), (2, 12))
    y_axis = downs_y_axis_deg_v1((0, 2), (10, 12), (0, 0), (10, 0))

    assert facial == pytest.approx(90.0)
    assert y_axis == pytest.approx(45.0)
    assert downs_facial_angle_deg_v1((10, 0), (0, 0), (2, 12), (2, 2)) == pytest.approx(facial)
    assert downs_y_axis_deg_v1((10, 12), (0, 2), (10, 0), (0, 0)) == pytest.approx(y_axis)
    assert downs_facial_angle_deg_v1((0, 0), (-10, 0), (-2, 2), (-2, 12)) == pytest.approx(facial)
    assert downs_y_axis_deg_v1((0, 2), (-10, 12), (0, 0), (-10, 0)) == pytest.approx(y_axis)


def test_downs_constructions_are_source_bound_uncalibrated_and_available():
    constructions = materialize_downs_constructions(
        _landmarks(), construction_namespace="construction:downs:1"
    )

    assert set(constructions) == set(DOWNS_CONSTRUCTION_DEFINITIONS)
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in constructions.values())
    assert all(item.geometry["analysis"] == "DOWNS" for item in constructions.values())
    assert all(item.geometry["axis_orientation_invariant"] is True for item in constructions.values())

    measurements = adapt_downs_measurements(
        measurement_namespace="measurement:downs:1",
        constructions=constructions,
    )
    assert [item.method_id for item in measurements] == [
        "DOWNS_FACIAL_ANGLE_DEG_V1",
        "DOWNS_Y_AXIS_DEG_V1",
    ]
    assert all(item.analysis_id == "DOWNS" for item in measurements)
    assert all(item.requires_calibration is False for item in measurements)
    assert all(item.calibration_ref is None for item in measurements)


def test_downs_missing_landmark_fails_closed_per_measure():
    landmarks = _landmarks()
    landmarks.pop("Pog")
    constructions = materialize_downs_constructions(
        landmarks, construction_namespace="construction:downs:missing"
    )

    assert constructions["DOWNS_FACIAL_ANGLE_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["DOWNS_Y_AXIS_V1"].availability_status == AvailabilityStatus.AVAILABLE


def test_downs_cross_image_and_degenerate_geometry_fail_closed():
    mixed = _landmarks()
    mixed["Pog"] = _landmark("Pog", 2.0, 12.0, source="source:ceph:other")
    constructions = materialize_downs_constructions(
        mixed, construction_namespace="construction:downs:mixed"
    )
    assert constructions["DOWNS_FACIAL_ANGLE_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["DOWNS_Y_AXIS_V1"].availability_status == AvailabilityStatus.AVAILABLE

    degenerate = _landmarks()
    degenerate["Or"] = _landmark("Or", 0.0, 0.0)
    constructions = materialize_downs_constructions(
        degenerate, construction_namespace="construction:downs:degenerate"
    )
    assert all(item.availability_status == AvailabilityStatus.INVALID for item in constructions.values())
