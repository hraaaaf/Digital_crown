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
    ricketts_1981_fma_deg_v2,
)

UTC = datetime.timezone.utc


def _manual_source_point(
    landmark_id: str,
    x: float,
    y: float,
    *,
    image: str = "img:1",
    validated: bool = True,
) -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"lm:{landmark_id}",
        landmark_id=landmark_id,
        x=x,
        y=y,
        source_image_ref=image,
        origin=LandmarkOrigin.MANUAL,
        validated_by="clinician:test" if validated else None,
        validated_at=(
            datetime.datetime(2026, 9, 12, 12, 0, tzinfo=UTC) if validated else None
        ),
        evidence_refs=["source:test"],
        evidence_status=(
            EvidenceStatus.CLINICIAN_VALIDATED if validated else EvidenceStatus.OBSERVED
        ),
        availability_status=AvailabilityStatus.AVAILABLE,
    )


def _auto(landmark_id: str, x: float, y: float, *, image: str = "img:1") -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"auto:{landmark_id}",
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


def _ricketts_landmarks(*, cross_image: bool = False) -> dict[str, LandmarkEvidence]:
    return {
        "RickettsTruePo": _manual_source_point("RickettsTruePo", 0.0, 0.0),
        "RickettsTrueOr": _manual_source_point("RickettsTrueOr", 10.0, 0.0),
        "RickettsSubGo": _manual_source_point(
            "RickettsSubGo", 0.0, 10.0, image="img:other" if cross_image else "img:1"
        ),
        "RickettsMe": _manual_source_point("RickettsMe", 10.0, 20.0),
    }


def test_ricketts_1981_fma_computes_only_with_validated_source_specific_points():
    construction = materialize_ricketts_1981_fma_construction(
        _ricketts_landmarks(), construction_namespace="case:1"
    )

    assert construction.definition_id == RICKETTS_1981_FMA_DEFINITION_ID
    assert construction.definition_version == "2"
    assert construction.availability_status == AvailabilityStatus.AVAILABLE
    assert construction.missing_landmark_ids == []
    assert construction.geometry["computed_angle_deg"] == pytest.approx(45.0)
    assert construction.geometry["frankfort_plane"] == "RickettsTruePo-RickettsTrueOr"
    assert construction.geometry["mandibular_plane"] == "RickettsSubGo-RickettsMe"
    assert construction.geometry["patient_classification_active"] is False

    measurement = adapt_ricketts_1981_fma_measurement(
        construction, measurement_namespace="case:1"
    )
    assert measurement.value == pytest.approx(45.0)
    assert measurement.unit == "deg"
    assert measurement.availability_status == AvailabilityStatus.AVAILABLE
    assert measurement.analysis_id == "RICKETTS_1981"
    assert measurement.method_version == "2"


def test_generic_srpose38_po_or_go_me_never_substitute_for_ricketts_source_points():
    generic = {
        "Po": _auto("Po", 0.0, 0.0),
        "Or": _auto("Or", 10.0, 0.0),
        "Go": _auto("Go", 0.0, 10.0),
        "Me": _auto("Me", 10.0, 20.0),
    }

    construction = materialize_ricketts_1981_fma_construction(
        generic, construction_namespace="case:generic"
    )

    assert construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert construction.missing_landmark_ids == [
        "RickettsTruePo",
        "RickettsTrueOr",
        "RickettsSubGo",
        "RickettsMe",
    ]
    assert "computed_angle_deg" not in construction.geometry


def test_source_specific_ricketts_point_requires_explicit_validation():
    landmarks = _ricketts_landmarks()
    landmarks["RickettsSubGo"] = _manual_source_point(
        "RickettsSubGo", 0.0, 10.0, validated=False
    )

    with pytest.raises(ValueError, match="CLINICIAN_VALIDATED"):
        materialize_ricketts_1981_fma_construction(
            landmarks, construction_namespace="case:unvalidated"
        )


def test_automatic_source_named_point_is_rejected_even_if_coordinates_exist():
    landmarks = _ricketts_landmarks()
    landmarks["RickettsTruePo"] = _auto("RickettsTruePo", 0.0, 0.0)

    with pytest.raises(ValueError, match="source-specific MANUAL landmark"):
        materialize_ricketts_1981_fma_construction(
            landmarks, construction_namespace="case:auto"
        )


def test_cross_image_source_specific_geometry_is_invalid():
    construction = materialize_ricketts_1981_fma_construction(
        _ricketts_landmarks(cross_image=True), construction_namespace="case:cross"
    )
    assert construction.availability_status == AvailabilityStatus.INVALID
    assert "computed_angle_deg" not in construction.geometry


def test_degenerate_source_specific_axis_is_invalid():
    landmarks = _ricketts_landmarks()
    landmarks["RickettsTrueOr"] = _manual_source_point("RickettsTrueOr", 0.0, 0.0)
    construction = materialize_ricketts_1981_fma_construction(
        landmarks, construction_namespace="case:degenerate"
    )
    assert construction.availability_status == AvailabilityStatus.INVALID


def test_ricketts_geometry_primitive_is_non_oriented_and_fail_closed():
    assert ricketts_1981_fma_deg_v2(
        (0.0, 0.0), (10.0, 0.0), (0.0, 10.0), (10.0, 20.0)
    ) == pytest.approx(45.0)
    assert ricketts_1981_fma_deg_v2(
        (10.0, 0.0), (0.0, 0.0), (0.0, 10.0), (10.0, 20.0)
    ) == pytest.approx(45.0)
    assert ricketts_1981_fma_deg_v2(
        (0.0, 0.0), (0.0, 0.0), (0.0, 1.0), (1.0, 1.0)
    ) is None
    assert ricketts_1981_fma_deg_v2(
        (0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (float("nan"), 2.0)
    ) is None


def test_tweed_source_exact_geometry_stays_blocked_instead_of_using_convenience_lines():
    blocker = TWEED_SOURCE_EXACT_GEOMETRY_BLOCKER
    assert blocker["status"] == "BLOCKED_SOURCE_SPECIFIC_GEOMETRY"
    assert blocker["mandibular_plane_requirement"] == "source_specific_lower_border_tangent"
    assert "doi:10.1016/0096-6347(46)90001-4" in blocker["source_refs"]
    forbidden = set(blocker["forbidden_substitutions"])
    assert "Go-Me_as_Tweed_mandibular_plane" in forbidden
    assert "Go-Gn_as_Tweed_mandibular_plane" in forbidden
    assert "generic_Po-Or_as_source_exact_Tweed_FH_without_proof" in forbidden
