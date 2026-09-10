"""Contract tests for typed CRANIOM construction materialization."""

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_construction_evidence_adapter import (
    CRANIOM_LINEAR_REQUIRED_LANDMARKS,
    materialize_craniom_linear_constructions,
)
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_measurement_adapter import adapt_craniom_linear_measurements


def _landmark(landmark_id: str, *, source: str = "source:ceph:1", availability=AvailabilityStatus.AVAILABLE):
    coordinates = {
        "A": (24.0, 28.0),
        "B": (22.0, 38.0),
        "N": (20.0, 10.0),
        "Po": (0.0, 20.0),
        "Or": (20.0, 20.0),
        "S": (10.0, 10.0),
    }
    x, y = coordinates[landmark_id]
    return LandmarkEvidence(
        evidence_id=f"landmark:{landmark_id}",
        landmark_id=landmark_id,
        x=x,
        y=y,
        source_image_ref=source,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source],
        evidence_status=EvidenceStatus.OBSERVED,
        availability_status=availability,
    )


def _landmarks():
    return {landmark_id: _landmark(landmark_id) for landmark_id in ("A", "B", "N", "Po", "Or", "S")}


def _engine_points():
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


def test_all_required_landmarks_materialize_four_available_constructions():
    constructions = materialize_craniom_linear_constructions(
        _landmarks(), construction_namespace="cephalo:1:construction"
    )

    assert set(constructions) == set(CRANIOM_LINEAR_REQUIRED_LANDMARKS)
    for definition_id, construction in constructions.items():
        assert construction.definition_id == definition_id
        assert construction.definition_version == "1"
        assert construction.availability_status == AvailabilityStatus.AVAILABLE
        assert construction.missing_landmark_ids == []
        assert construction.geometry["source_image_ref"] == "source:ceph:1"
        assert set(construction.landmark_refs) == {
            f"landmark:{landmark_id}"
            for landmark_id in CRANIOM_LINEAR_REQUIRED_LANDMARKS[definition_id]
        }


def test_missing_or_propagates_not_computable_without_fake_reference():
    landmarks = _landmarks()
    landmarks.pop("Or")

    constructions = materialize_craniom_linear_constructions(
        landmarks, construction_namespace="cephalo:2:construction"
    )

    assert all(
        construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE
        for construction in constructions.values()
    )
    for construction in constructions.values():
        assert "Or" in construction.missing_landmark_ids
        assert "landmark:Or" not in construction.landmark_refs
        assert construction.geometry == {}


def test_missing_a_only_blocks_a_dependent_constructions():
    landmarks = _landmarks()
    landmarks.pop("A")

    constructions = materialize_craniom_linear_constructions(
        landmarks, construction_namespace="cephalo:3:construction"
    )

    assert constructions["CRANIOM_A_TO_N_VERTICAL_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["CRANIOM_AB_PRIME_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["CRANIOM_B_TO_N_VERTICAL_V1"].availability_status == AvailabilityStatus.AVAILABLE
    assert constructions["CRANIOM_S_TO_N_VERTICAL_DEPTH_V1"].availability_status == AvailabilityStatus.AVAILABLE


def test_present_but_unavailable_landmark_is_not_used_as_computable_evidence():
    landmarks = _landmarks()
    landmarks["A"] = _landmark("A", availability=AvailabilityStatus.INVALID)

    constructions = materialize_craniom_linear_constructions(
        landmarks, construction_namespace="cephalo:4:construction"
    )

    assert constructions["CRANIOM_A_TO_N_VERTICAL_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["CRANIOM_AB_PRIME_V1"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert constructions["CRANIOM_A_TO_N_VERTICAL_V1"].missing_landmark_ids == ["A"]


def test_mixed_source_images_make_only_affected_constructions_invalid():
    landmarks = _landmarks()
    landmarks["A"] = _landmark("A", source="source:ceph:2")

    constructions = materialize_craniom_linear_constructions(
        landmarks, construction_namespace="cephalo:5:construction"
    )

    assert constructions["CRANIOM_A_TO_N_VERTICAL_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["CRANIOM_AB_PRIME_V1"].availability_status == AvailabilityStatus.INVALID
    assert constructions["CRANIOM_B_TO_N_VERTICAL_V1"].availability_status == AvailabilityStatus.AVAILABLE
    assert constructions["CRANIOM_S_TO_N_VERTICAL_DEPTH_V1"].availability_status == AvailabilityStatus.AVAILABLE


def test_mapping_key_must_match_canonical_landmark_id():
    landmarks = _landmarks()
    landmarks["A"] = _landmark("B")

    with pytest.raises(ValueError, match="mapping key A resolves to B"):
        materialize_craniom_linear_constructions(
            landmarks, construction_namespace="cephalo:6:construction"
        )


def test_empty_construction_namespace_is_rejected():
    with pytest.raises(ValueError, match="construction_namespace"):
        materialize_craniom_linear_constructions(
            _landmarks(), construction_namespace=""
        )


def test_materialized_constructions_feed_measurement_adapter_without_free_text_logic():
    constructions = materialize_craniom_linear_constructions(
        _landmarks(), construction_namespace="cephalo:7:construction"
    )
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_engine_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:7:measurement",
        constructions=constructions,
        calibration_ref="source:calibration:7",
    )

    assert len(measurements) == 4
    assert all(m.availability_status == AvailabilityStatus.AVAILABLE for m in measurements)
    assert all(m.value is not None for m in measurements)


def test_missing_landmark_propagates_through_materializer_to_measurements():
    landmarks = _landmarks()
    landmarks.pop("Or")
    constructions = materialize_craniom_linear_constructions(
        landmarks, construction_namespace="cephalo:8:construction"
    )
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_engine_points())

    measurements = adapt_craniom_linear_measurements(
        result,
        measurement_namespace="cephalo:8:measurement",
        constructions=constructions,
        calibration_ref="source:calibration:8",
    )

    assert all(m.value is None for m in measurements)
    assert all(
        m.availability_status == AvailabilityStatus.NOT_COMPUTABLE
        for m in measurements
    )
