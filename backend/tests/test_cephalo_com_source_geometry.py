"""Contract tests for source-specific COM/Tweed/Ricketts geometry recovery."""
from __future__ import annotations

import datetime

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_com_source_geometry import (
    RICKETTS_1981_FMA_DEFINITION_ID,
    TWEED_SOURCE_EXACT_GEOMETRY_BLOCKER,
    adapt_ricketts_1981_fma_measurement,
    materialize_ricketts_1981_fma_construction,
    ricketts_1981_fma_deg_v1,
)

UTC = datetime.timezone.utc


def _auto(landmark_id: str, x: float, y: float, *, image: str = "img:1") -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"lm:{landmark_id}",
        landmark_id=landmark_id,
        x=x,
        y=y,
        source_image_ref=image,
        origin=LandmarkOrigin.SRPOSE38_AUTO,
        model_id="srpose38-test",
        model_sha256="a" * 64,
        pipeline_version="test-v1",
        evidence_refs=["source:test"],
        evidence_status=EvidenceStatus.OBSERVED,
        availability_status=AvailabilityStatus.AVAILABLE,
    )


def _manual_subgo(
    x: float,
    y: float,
    *,
    image: str = "img:1",
    validated: bool = True,
) -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id="lm:SubGo",
        landmark_id="SubGo",
        x=x,
        y=y,
        source_image_ref=image,
        origin=LandmarkOrigin.MANUAL,
        validated_by="clinician:test" if validated else None,
        validated_at=datetime.datetime(2026, 9, 12, 12, 0, tzinfo=UTC) if validated else None,
        evidence_refs=["source:test"],
        evidence_status=(
            EvidenceStatus.CLINICIAN_VALIDATED if validated else EvidenceStatus.OBSERVED
        ),
        availability_status=AvailabilityStatus.AVAILABLE,
    )


def _base_landmarks(*, include_subgo: bool = True, subgo_image: str = "img:1") -> dict[str, LandmarkEvidence]:
    landmarks = {
        "Po": _auto("Po", 0.0, 0.0),
        "Or": _auto("Or", 10.0, 0.0),
        "Me": _auto("Me", 10.0, 20.0),
        # Go is intentionally present to prove that it never substitutes for SubGo.
        "Go": _auto("Go", 0.0, 20.0),
    }
    if include_subgo:
        landmarks["SubGo"] = _manual_subgo(0.0, 10.0, image=subgo_image)
    return landmarks


def test_ricketts_1981_fma_geometry_computes_with_validated_manual_subgo():
    construction = materialize_ricketts_1981_fma_construction(
        _base_landmarks(), construction_namespace="case:1"
    )

    assert construction.definition_id == RICKETTS_1981_FMA_DEFINITION_ID
    assert construction.availability_status == AvailabilityStatus.AVAILABLE
    assert construction.missing_landmark_ids == []
    assert construction.geometry["computed_angle_deg"] == pytest.approx(45.0)
    assert construction.geometry["mandibular_plane"] == "SubGo-Me"
    assert construction.geometry["patient_classification_active"] is False
    assert construction.geometry["subgo_evidence_ref"] == "lm:SubGo"

    measurement = adapt_ricketts_1981_fma_measurement(
        construction, measurement_namespace="case:1"
    )
    assert measurement.value == pytest.approx(45.0)
    assert measurement.unit == "deg"
    assert measurement.availability_status == AvailabilityStatus.AVAILABLE
    assert measurement.analysis_id == "RICKETTS_1981"


def test_go_never_substitutes_for_missing_subgo():
    construction = materialize_ricketts_1981_fma_construction(
        _base_landmarks(include_subgo=False), construction_namespace="case:missing"
    )

    assert "Go" in _base_landmarks(include_subgo=False)
    assert construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert construction.missing_landmark_ids == ["SubGo"]
    assert "computed_angle_deg" not in construction.geometry

    measurement = adapt_ricketts_1981_fma_measurement(
        construction, measurement_namespace="case:missing"
    )
    assert measurement.value is None
    assert measurement.availability_status == AvailabilityStatus.NOT_COMPUTABLE


def test_manual_subgo_requires_explicit_clinician_validation():
    landmarks = _base_landmarks()
    landmarks["SubGo"] = _manual_subgo(0.0, 10.0, validated=False)

    with pytest.raises(ValueError, match="CLINICIAN_VALIDATED"):
        materialize_ricketts_1981_fma_construction(
            landmarks, construction_namespace="case:unvalidated"
        )


def test_automatic_subgo_is_rejected_even_if_coordinates_exist():
    landmarks = _base_landmarks(include_subgo=False)
    landmarks["SubGo"] = _auto("SubGo", 0.0, 10.0)

    with pytest.raises(ValueError, match="source-specific manual landmark"):
        materialize_ricketts_1981_fma_construction(
            landmarks, construction_namespace="case:auto-subgo"
        )


def test_cross_image_source_specific_geometry_is_invalid():
    construction = materialize_ricketts_1981_fma_construction(
        _base_landmarks(subgo_image="img:other"), construction_namespace="case:cross"
    )
    assert construction.availability_status == AvailabilityStatus.INVALID
    assert "computed_angle_deg" not in construction.geometry


def test_degenerate_source_specific_axis_is_invalid():
    landmarks = _base_landmarks()
    landmarks["Or"] = _auto("Or", 0.0, 0.0)
    construction = materialize_ricketts_1981_fma_construction(
        landmarks, construction_namespace="case:degenerate"
    )
    assert construction.availability_status == AvailabilityStatus.INVALID


def test_ricketts_geometry_primitive_rejects_nonfinite_or_degenerate_inputs():
    assert ricketts_1981_fma_deg_v1((0.0, 0.0), (0.0, 0.0), (0.0, 1.0), (1.0, 1.0)) is None
    assert ricketts_1981_fma_deg_v1((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (float("nan"), 2.0)) is None


def test_tweed_source_exact_geometry_stays_blocked_instead_of_using_go_me():
    blocker = TWEED_SOURCE_EXACT_GEOMETRY_BLOCKER
    assert blocker["status"] == "BLOCKED_SOURCE_SPECIFIC_GEOMETRY"
    assert blocker["mandibular_plane_requirement"] == "tangent_to_lower_border_of_mandible"
    forbidden = set(blocker["forbidden_substitutions"])
    assert "Go-Me_as_Tweed_mandibular_plane" in forbidden
    assert "Go-Gn_as_Tweed_mandibular_plane" in forbidden
    assert "generic_Po-Or_as_source_exact_Tweed_FH_without_proof" in forbidden
