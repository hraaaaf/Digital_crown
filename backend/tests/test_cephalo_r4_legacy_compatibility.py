"""Compatibility gates for incrementally extending typed CRANIOM evidence."""

from backend.schemas.cephalo_evidence import ConstructionEvidence
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_measurement_adapter import (
    CRANIOM_LINEAR_CONSTRUCTION_DEFINITIONS,
    adapt_craniom_linear_measurements,
)


def _points():
    return {
        "S": (10.0, 10.0), "N": (20.0, 10.0),
        "Po": (0.0, 20.0), "Or": (20.0, 20.0),
        "A": (24.0, 28.0), "B": (22.0, 38.0),
        "Go": (5.0, 50.0), "Me": (25.0, 55.0),
        "U1_apex": (20.0, 25.0), "U1_incisal": (24.0, 35.0),
        "L1_apex": (20.0, 48.0), "L1_incisal": (23.0, 38.0),
    }


def _pre_r4_constructions():
    return {
        definition_id: ConstructionEvidence(
            construction_id=f"construction:legacy:{definition_id}",
            definition_id=definition_id,
            definition_version="1",
            landmark_refs=["landmark:legacy"],
            geometry={"kind": "persisted_pre_r4"},
            evidence_refs=["landmark:legacy"],
        )
        for definition_id in CRANIOM_LINEAR_CONSTRUCTION_DEFINITIONS
    }


def _pre_l1_downs_constructions():
    constructions = _pre_r4_constructions()
    constructions["CRANIOM_U1_TO_FRANKFORT_V1"] = ConstructionEvidence(
        construction_id="construction:legacy:CRANIOM_U1_TO_FRANKFORT_V1",
        definition_id="CRANIOM_U1_TO_FRANKFORT_V1",
        definition_version="1",
        landmark_refs=["landmark:legacy:u1"],
        geometry={
            "kind": "persisted_r4_u1",
            "computed_angle_deg": 111.8,
        },
        evidence_refs=["landmark:legacy:u1"],
    )
    return constructions


def test_pre_r4_four_construction_snapshot_remains_adaptable_during_calibration_revision():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="legacy:r3",
        constructions=_pre_r4_constructions(),
        calibration_ref="source:legacy:calibration",
    )

    assert len(measurements) == 4
    assert all(m.requires_calibration for m in measurements)
    assert all(m.calibration_ref == "source:legacy:calibration" for m in measurements)
    assert all(m.method_id != "CRANIOM_U1_FRANKFORT_DEG_V1" for m in measurements)
    assert all(m.method_id != "CRANIOM_L1_DOWNS_DEG_V1" for m in measurements)


def test_pre_l1_five_construction_snapshot_remains_adaptable_without_fabricating_l1():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())
    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="legacy:r4-u1",
        constructions=_pre_l1_downs_constructions(),
        calibration_ref="source:legacy:calibration",
    )

    assert len(measurements) == 5
    methods = {m.method_id for m in measurements}
    assert "CRANIOM_U1_FRANKFORT_DEG_V1" in methods
    assert "CRANIOM_L1_DOWNS_DEG_V1" not in methods
    u1 = next(m for m in measurements if m.method_id == "CRANIOM_U1_FRANKFORT_DEG_V1")
    assert u1.requires_calibration is False
    assert u1.calibration_ref is None
