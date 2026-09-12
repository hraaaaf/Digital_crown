"""Regression contract for the ten-measure COM simplified projection geometry."""

import math

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_construction_evidence_adapter import (
    materialize_craniom_constructions,
)
from backend.services.cephalo_constructions import (
    craniom_ab_prime_mm_v1,
    craniom_facial_depth_mm_v1,
    nasion_vertical_offset_mm_v1,
)


def _landmark(landmark_id: str, x: float, y: float) -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"landmark:{landmark_id}",
        landmark_id=landmark_id,
        x=x,
        y=y,
        source_image_ref="source:ceph:com",
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:ceph:com"],
        evidence_status=EvidenceStatus.OBSERVED,
        availability_status=AvailabilityStatus.AVAILABLE,
    )


def _linear_landmarks() -> dict[str, LandmarkEvidence]:
    return {
        "A": _landmark("A", 24.0, 28.0),
        "B": _landmark("B", 22.0, 38.0),
        "N": _landmark("N", 20.0, 10.0),
        "Po": _landmark("Po", 0.0, 20.0),
        "Or": _landmark("Or", 20.0, 20.0),
        "S": _landmark("S", 10.0, 10.0),
    }


def _rotate(point: tuple[float, float], theta: float) -> tuple[float, float]:
    c, s = math.cos(theta), math.sin(theta)
    x, y = point
    return (x * c - y * s, x * s + y * c)


def test_ab_prime_evidence_requires_nasion_and_materializes_clinical_construction():
    landmarks = _linear_landmarks()
    constructions = materialize_craniom_constructions(
        landmarks,
        construction_namespace="cephalo:com:construction",
    )
    ab = constructions["CRANIOM_AB_PRIME_V1"]

    assert ab.availability_status == AvailabilityStatus.AVAILABLE
    assert set(ab.landmark_refs) == {
        "landmark:A", "landmark:B", "landmark:N", "landmark:Po", "landmark:Or"
    }
    assert ab.geometry["mcnamara_origin_landmark"] == "N"
    assert ab.geometry["mcnamara_relation"] == "perpendicular_to_FH"
    assert ab.geometry["a_prime_construction"] == "parallel_to_McNamara_through_A_intersect_FH"
    assert ab.geometry["b_prime_construction"] == "parallel_to_McNamara_through_B_intersect_FH"
    assert ab.geometry["positive_direction"] == "A_anterior_to_B_along_Po_to_Or"


def test_ab_prime_fails_closed_when_nasion_is_missing():
    landmarks = _linear_landmarks()
    landmarks.pop("N")
    ab = materialize_craniom_constructions(
        landmarks,
        construction_namespace="cephalo:com:construction",
    )["CRANIOM_AB_PRIME_V1"]

    assert ab.availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert ab.missing_landmark_ids == ["N"]
    assert set(ab.geometry) == {"geometric_convention"}


def test_ab_prime_sign_translation_rotation_and_degenerate_frankfort():
    a, b = (6.0, 1.0), (2.0, 4.0)
    po, orbitale = (0.0, 0.0), (10.0, 0.0)
    ratio = 0.5

    positive = craniom_ab_prime_mm_v1(a, b, po, orbitale, ratio)
    reverse = craniom_ab_prime_mm_v1(b, a, po, orbitale, ratio)
    assert positive == pytest.approx(2.0)
    assert reverse == pytest.approx(-2.0)

    shift = (17.0, -11.0)
    translated = craniom_ab_prime_mm_v1(
        (a[0] + shift[0], a[1] + shift[1]),
        (b[0] + shift[0], b[1] + shift[1]),
        (po[0] + shift[0], po[1] + shift[1]),
        (orbitale[0] + shift[0], orbitale[1] + shift[1]),
        ratio,
    )
    assert translated == pytest.approx(positive)

    theta = math.radians(37)
    rotated = craniom_ab_prime_mm_v1(
        _rotate(a, theta), _rotate(b, theta), _rotate(po, theta), _rotate(orbitale, theta), ratio
    )
    assert rotated == pytest.approx(positive)
    assert craniom_ab_prime_mm_v1(a, b, po, po, ratio) is None


def test_situation_a_b_sign_and_rigid_rotation_are_source_consistent():
    n, po, orbitale = (3.0, 7.0), (0.0, 0.0), (10.0, 0.0)
    anterior, posterior = (7.0, 9.0), (1.0, 9.0)
    ratio = 0.5

    assert nasion_vertical_offset_mm_v1(anterior, n, po, orbitale, ratio) == pytest.approx(2.0)
    assert nasion_vertical_offset_mm_v1(posterior, n, po, orbitale, ratio) == pytest.approx(-1.0)

    theta = math.radians(-23)
    rotated = nasion_vertical_offset_mm_v1(
        _rotate(anterior, theta), _rotate(n, theta), _rotate(po, theta), _rotate(orbitale, theta), ratio
    )
    assert rotated == pytest.approx(2.0)
    assert nasion_vertical_offset_mm_v1(anterior, None, po, orbitale, ratio) is None
    assert nasion_vertical_offset_mm_v1(anterior, n, po, po, ratio) is None


def test_facial_depth_is_absolute_independent_of_a_b_and_fail_closed():
    s, n, po, orbitale = (1.0, 9.0), (3.0, 7.0), (0.0, 0.0), (10.0, 0.0)
    ratio = 0.5

    assert craniom_facial_depth_mm_v1(s, n, po, orbitale, ratio) == pytest.approx(1.0)
    assert craniom_facial_depth_mm_v1((5.0, 9.0), n, po, orbitale, ratio) == pytest.approx(1.0)
    assert craniom_facial_depth_mm_v1(None, n, po, orbitale, ratio) is None
    assert craniom_facial_depth_mm_v1(s, None, po, orbitale, ratio) is None
    assert craniom_facial_depth_mm_v1(s, n, po, po, ratio) is None
