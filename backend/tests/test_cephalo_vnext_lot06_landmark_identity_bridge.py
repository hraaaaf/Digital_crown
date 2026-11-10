"""Safety regressions for SRPose38-to-canonical identities (synthetic only).

A model hash proves numerical provenance; it does not certify that output
channel N is the clinically named anatomy at that location.
"""
from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_landmark_identity_bridge import (
    CanonicalLandmarkIdentityError,
    project_canonical_landmark_identities,
)
from backend.services.srpose38_contract import (
    SRPOSE38_MODEL_NAME,
    SRPOSE38_MODEL_SHA256,
    SRPOSE38_PIPELINE_VERSION,
)


def _auto(landmark_id: str, *, source: str = "source:synthetic-ceph") -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"landmark:auto:{landmark_id}",
        landmark_id=landmark_id,
        x=10.0,
        y=20.0,
        source_image_ref=source,
        origin=LandmarkOrigin.SRPOSE38_AUTO,
        model_id=SRPOSE38_MODEL_NAME,
        model_sha256=SRPOSE38_MODEL_SHA256,
        pipeline_version=SRPOSE38_PIPELINE_VERSION,
        evidence_refs=[source],
        evidence_status=EvidenceStatus.COMPUTED,
    )


def _manual(landmark_id: str, *, source: str = "source:synthetic-ceph") -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"landmark:manual:{landmark_id}",
        landmark_id=landmark_id,
        x=11.0,
        y=21.0,
        source_image_ref=source,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _attested(item: LandmarkEvidence) -> LandmarkEvidence:
    return item.model_copy(update={
        "validated_by": "synthetic-clinician",
        "validated_at": datetime(2026, 11, 10, tzinfo=timezone.utc),
        "evidence_status": EvidenceStatus.CLINICIAN_VALIDATED,
    })


def _corrected(landmark_id: str = "Po", *, source: str = "source:synthetic-ceph") -> LandmarkEvidence:
    return _attested(
        LandmarkEvidence(
            evidence_id=f"landmark:corrected:{landmark_id}",
            landmark_id=landmark_id,
            x=11.0,
            y=21.0,
            source_image_ref=source,
            origin=LandmarkOrigin.MANUAL_CORRECTED,
            original_auto_x=10.0,
            original_auto_y=20.0,
            evidence_refs=[source],
            validated_by="synthetic-clinician",
            validated_at=datetime(2026, 11, 10, tzinfo=timezone.utc),
            evidence_status=EvidenceStatus.CLINICIAN_VALIDATED,
        )
    )


def test_pinned_srpose_model_hash_does_not_promote_automatic_anatomy():
    current = {name: _auto(name) for name in ("Po", "Co", "Pog", "Gn")}
    projected = project_canonical_landmark_identities(current)
    assert set(projected) == set(current)
    assert not {"Po_anatomic", "Co_anatomic", "Pog_hard", "Gn_anatomic"} & set(projected)


def test_spoofed_clinician_validation_on_auto_still_fails_closed():
    current = {"Po": _attested(_auto("Po"))}
    assert "Po_anatomic" not in project_canonical_landmark_identities(current)


def test_manual_point_without_review_does_not_gain_canonical_identity():
    current = {"Po": _manual("Po")}
    assert "Po_anatomic" not in project_canonical_landmark_identities(
        current, previous_auto_landmarks=[_auto("Po")]
    )


def test_explicit_clinician_attestation_can_project_only_supported_aliases():
    current = {key: _attested(_manual(key)) for key in ("Po", "Co", "Pog", "Gn")}
    projected = project_canonical_landmark_identities(current)
    assert {"Po_anatomic", "Co_anatomic", "Pog_hard"} <= set(projected)
    assert "Gn_anatomic" not in projected
    assert projected["Po_anatomic"].x == projected["Po"].x
    assert projected["Pog_hard"].y == projected["Pog"].y
    assert projected["Po"].landmark_id == "Po"
    assert projected["Po_anatomic"].evidence_status == EvidenceStatus.CLINICIAN_VALIDATED


def test_corrected_point_requires_exact_previous_same_image_and_coordinates():
    current = {"Po": _corrected()}
    projected = project_canonical_landmark_identities(
        current, previous_auto_landmarks=[_auto("Po")]
    )
    assert projected["Po_anatomic"].origin == LandmarkOrigin.MANUAL_CORRECTED
    assert projected["Po_anatomic"].x == 11.0

    bad_source = _auto("Po", source="source:another-synthetic-film")
    assert "Po_anatomic" not in project_canonical_landmark_identities(
        current, previous_auto_landmarks=[bad_source]
    )
    bad_original = _corrected().model_copy(update={"original_auto_x": 10.1})
    assert "Po_anatomic" not in project_canonical_landmark_identities(
        {"Po": bad_original}, previous_auto_landmarks=[_auto("Po")]
    )
    bad_model = _auto("Po").model_copy(update={"model_sha256": "wrong"})
    assert "Po_anatomic" not in project_canonical_landmark_identities(
        current, previous_auto_landmarks=[bad_model]
    )
    assert "Po_anatomic" not in project_canonical_landmark_identities(current)


def test_wrong_provenance_never_promotes_unreviewed_auto():
    bad = _auto("Po").model_copy(update={"model_sha256": "wrong"})
    assert "Po_anatomic" not in project_canonical_landmark_identities({"Po": bad})


def test_unavailable_and_naive_time_manual_are_not_promoted():
    reviewed = _attested(_manual("Po"))
    unavailable = reviewed.model_copy(
        update={"availability_status": AvailabilityStatus.NOT_COMPUTABLE}
    )
    assert "Po_anatomic" not in project_canonical_landmark_identities({"Po": unavailable})
    naive = reviewed.model_copy(update={"validated_at": datetime(2026, 11, 10)})
    assert "Po_anatomic" not in project_canonical_landmark_identities({"Po": naive})


def test_unreviewed_canonical_direct_input_rejected_even_without_legacy_id():
    for canonical_id in ("Po_anatomic", "Co_anatomic", "Pog_hard", "Gn_anatomic", "Pt_Ricketts"):
        with pytest.raises(CanonicalLandmarkIdentityError, match="Unreviewed canonical"):
            project_canonical_landmark_identities({canonical_id: _auto(canonical_id)})


def test_explicit_manually_attested_canonical_input_is_preserved():
    canonical = _attested(_manual("Gn_anatomic"))
    projected = project_canonical_landmark_identities({"Gn_anatomic": canonical})
    assert projected == {"Gn_anatomic": canonical}


def test_preexisting_canonical_identity_collision_fails_closed():
    with pytest.raises(CanonicalLandmarkIdentityError, match="collision"):
        project_canonical_landmark_identities({
            "Po": _auto("Po"),
            "Po_anatomic": _attested(_manual("Po_anatomic")),
        })


def test_canonical_fma_downstream_fails_closed_until_manual_attestation():
    """Real measurement builder must not treat an auto model SHA as anatomic Po."""
    from backend.services.cephalo_canonical_analysis_v2 import (
        materialize_canonical_analysis_v2_measurements,
    )

    coords = {"Po": (0, 8), "Or": (20, 10), "Go": (0, 22), "Me": (16, 21)}

    def _point(item, x, y):
        return item.model_copy(update={"x": float(x), "y": float(y)})

    auto_current = {key: _point(_auto(key), *xy) for key, xy in coords.items()}
    auto_projected = project_canonical_landmark_identities(auto_current)
    assert "Po_anatomic" not in auto_projected
    auto_measures = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:synthetic:auto",
        landmarks=auto_projected,
        mm_per_pixel=0.2,
        calibration_ref="source:synthetic-calibration",
    )
    auto_fma = next(
        item for item in auto_measures
        if item.method_id == "TWEED_FMA_CANONICAL_DEG_V2"
    )
    assert auto_fma.availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert auto_fma.value is None

    reviewed_current = {
        key: _point(_attested(_manual(key)), *xy) for key, xy in coords.items()
    }
    reviewed_projected = project_canonical_landmark_identities(reviewed_current)
    assert "Po_anatomic" in reviewed_projected
    reviewed_measures = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:synthetic:manual",
        landmarks=reviewed_projected,
        mm_per_pixel=0.2,
        calibration_ref="source:synthetic-calibration",
    )
    reviewed_fma = next(
        item for item in reviewed_measures
        if item.method_id == "TWEED_FMA_CANONICAL_DEG_V2"
    )
    assert reviewed_fma.availability_status == AvailabilityStatus.AVAILABLE
    assert reviewed_fma.value is not None


def test_partially_attested_film_does_not_unlock_fma():
    """One reviewed Porion cannot launder three unreviewed SRPose landmarks."""
    from backend.services.cephalo_canonical_analysis_v2 import (
        materialize_canonical_analysis_v2_measurements,
    )

    originals = {
        "Po": _auto("Po").model_copy(update={"x": 0.0, "y": 8.0}),
        "Or": _auto("Or").model_copy(update={"x": 20.0, "y": 10.0}),
        "Go": _auto("Go").model_copy(update={"x": 0.0, "y": 22.0}),
        "Me": _auto("Me").model_copy(update={"x": 16.0, "y": 21.0}),
    }
    originals["Po"] = _attested(_manual("Po")).model_copy(
        update={"x": 0.0, "y": 8.0}
    )

    scientific = project_canonical_landmark_identities(originals)
    assert "Po_anatomic" in scientific
    assert scientific["Po_anatomic"].availability_status == AvailabilityStatus.AVAILABLE
    assert all(
        scientific[key].availability_status == AvailabilityStatus.NOT_COMPUTABLE
        for key in ("Or", "Go", "Me")
    )
    # Projection has no write-through side effects to the persisted input.
    assert all(
        originals[key].availability_status == AvailabilityStatus.AVAILABLE
        for key in originals
    )

    measurements = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:synthetic:partial",
        landmarks=scientific,
        mm_per_pixel=0.2,
        calibration_ref="source:synthetic-calibration",
    )
    fma = next(
        item for item in measurements
        if item.method_id == "TWEED_FMA_CANONICAL_DEG_V2"
    )
    assert fma.availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert fma.value is None


def test_unreviewed_manual_and_unmatched_correction_are_not_canonical_inputs():
    current = {
        "Or": _manual("Or"),
        "Go": _corrected("Go"),
    }
    scientific = project_canonical_landmark_identities(
        current, previous_auto_landmarks=[_auto("Go", source="source:wrong-film")]
    )
    assert scientific["Or"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert scientific["Go"].availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert current["Or"].availability_status == AvailabilityStatus.AVAILABLE


def test_adversarial_mapping_key_must_equal_evidence_landmark_identity():
    """A verified Co must never be promoted to Po_anatomic via a forged map key."""
    with pytest.raises(CanonicalLandmarkIdentityError, match="mapping key"):
        project_canonical_landmark_identities({"Po": _attested(_manual("Co"))})
    with pytest.raises(CanonicalLandmarkIdentityError, match="mapping key"):
        project_canonical_landmark_identities({"Po_anatomic": _attested(_manual("Co"))})


def test_ambiguous_original_auto_lineage_never_selects_the_last_observation():
    """Two competing SRPose records with the same ID cannot attest a correction."""
    previous = [
        _auto("Po"),
        _auto("Po", source="source:synthetic-other-film"),
    ]
    with pytest.raises(CanonicalLandmarkIdentityError, match="Ambiguous original"):
        project_canonical_landmark_identities(
            {"Po": _corrected("Po")}, previous_auto_landmarks=previous,
        )
    # Do not accept the reversed order either.
    with pytest.raises(CanonicalLandmarkIdentityError, match="Ambiguous original"):
        project_canonical_landmark_identities(
            {"Po": _corrected("Po")}, previous_auto_landmarks=list(reversed(previous)),
        )


def test_independently_attested_points_on_two_films_never_unlock_canonical_fma():
    """Clinician stamps alone do not permit combining anatomical films."""
    from backend.services.cephalo_canonical_analysis_v2 import (
        materialize_canonical_analysis_v2_measurements,
    )

    coords = {"Po": (0, 8), "Or": (20, 10), "Go": (0, 22), "Me": (16, 21)}
    current = {
        key: _attested(
            _manual(
                key,
                source=(
                    "source:synthetic-first-film"
                    if key in {"Po", "Or"} else "source:synthetic-other-film"
                ),
            )
        ).model_copy(update={"x": float(x), "y": float(y)})
        for key, (x, y) in coords.items()
    }
    projected = project_canonical_landmark_identities(current)
    assert "Po_anatomic" in projected
    measurements = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:synthetic:cross-film",
        landmarks=projected,
        mm_per_pixel=0.2,
        calibration_ref="source:synthetic-calibration",
    )
    fma = next(
        item for item in measurements
        if item.method_id == "TWEED_FMA_CANONICAL_DEG_V2"
    )
    assert fma.availability_status == AvailabilityStatus.INVALID
    assert fma.value is None
