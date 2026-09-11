from __future__ import annotations

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services.cephalo_construction_evidence_adapter import (
    CRANIOM_REQUIRED_LANDMARKS,
    materialize_craniom_linear_constructions,
)
from backend.services.cephalo_geometric_conventions import (
    ACTIVE_CRANIOM_CONVENTIONS,
    BLOCKED_CRANIOM_CONVENTIONS,
    CRANIOM_SOURCE_REFERENCES,
    get_active_craniom_convention,
)


def _landmark(landmark_id: str, x: float, y: float, *, source_image_ref: str = "img:1") -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"lm:{landmark_id}",
        landmark_id=landmark_id,
        x=x,
        y=y,
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["src:1"],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _complete_landmarks() -> dict[str, LandmarkEvidence]:
    return {
        "A": _landmark("A", 20.0, 30.0),
        "B": _landmark("B", 15.0, 45.0),
        "N": _landmark("N", 10.0, 10.0),
        "Po": _landmark("Po", 0.0, 50.0),
        "Or": _landmark("Or", 100.0, 50.0),
        "S": _landmark("S", 5.0, 20.0),
        "U1_apex": _landmark("U1_apex", 40.0, 20.0),
        "U1_incisal": _landmark("U1_incisal", 50.0, 45.0),
    }


def test_every_executable_craniom_construction_has_one_active_convention() -> None:
    assert set(ACTIVE_CRANIOM_CONVENTIONS) == set(CRANIOM_REQUIRED_LANDMARKS)
    for definition_id, required_landmarks in CRANIOM_REQUIRED_LANDMARKS.items():
        convention = get_active_craniom_convention(definition_id)
        assert convention.constructable is True
        assert convention.required_landmark_ids == required_landmarks
        assert convention.reference_frame_id == "FH_PO_OR_V1"
        assert convention.source_references == CRANIOM_SOURCE_REFERENCES


def test_ab_prime_is_explicitly_frankfort_and_not_ab_double_prime() -> None:
    convention = get_active_craniom_convention("CRANIOM_AB_PRIME_V1")
    assert convention.clinical_label == "A'B'"
    assert convention.convention_id == "CRANIOM_AB_PRIME_FH_V1"
    assert convention.reference_frame_id == "FH_PO_OR_V1"
    assert "DOUBLE_PRIME" not in convention.convention_id

    blocked = BLOCKED_CRANIOM_CONVENTIONS[
        "CRANIOM_AB_DOUBLE_PRIME_HORIZONTAL_GAZE_V1"
    ]
    assert blocked.constructable is False
    assert blocked.construction_definition_id is None
    assert blocked.blocked_reason == "HORIZONTAL_GAZE_NHP_PROTOCOL_NOT_AVAILABLE_IN_RUNTIME"


def test_gi_gs_contract_is_blocked_without_landmark_substitution() -> None:
    blocked = BLOCKED_CRANIOM_CONVENTIONS["CRANIOM_GI_GS_MANDIBULAR_FRAME_V1"]
    assert blocked.constructable is False
    assert blocked.required_landmark_ids == ("Gi", "Gs")
    assert "Go" not in blocked.required_landmark_ids
    assert "Ar" not in blocked.required_landmark_ids
    assert blocked.blocked_reason == "GI_GS_LANDMARKS_NOT_AVAILABLE_IN_SRPOSE38_RUNTIME"


def test_r4_u1_frankfort_convention_is_explicit_and_source_bound() -> None:
    convention = get_active_craniom_convention("CRANIOM_U1_TO_FRANKFORT_V1")
    assert convention.convention_id == "CRANIOM_U1_FRANKFORT_ANGLE_V1"
    assert convention.clinical_label == "Incisive supérieure / Frankfort"
    assert convention.required_landmark_ids == ("U1_apex", "U1_incisal", "Po", "Or")
    assert convention.reference_frame_id == "FH_PO_OR_V1"
    assert convention.source_references == CRANIOM_SOURCE_REFERENCES


def test_unknown_craniom_construction_fails_closed() -> None:
    with pytest.raises(ValueError, match="No active geometric convention"):
        get_active_craniom_convention("CRANIOM_UNKNOWN_V1")


def test_materialized_available_construction_carries_r3_convention_provenance() -> None:
    constructions = materialize_craniom_linear_constructions(
        _complete_landmarks(), construction_namespace="analysis:1"
    )

    ab_prime = constructions["CRANIOM_AB_PRIME_V1"]
    provenance = ab_prime.geometry["geometric_convention"]
    assert provenance["convention_id"] == "CRANIOM_AB_PRIME_FH_V1"
    assert provenance["clinical_label"] == "A'B'"
    assert provenance["reference_frame_id"] == "FH_PO_OR_V1"
    assert provenance["source_references"] == list(CRANIOM_SOURCE_REFERENCES)


def test_not_computable_construction_keeps_convention_but_withholds_patient_geometry() -> None:
    landmarks = _complete_landmarks()
    del landmarks["A"]

    construction = materialize_craniom_linear_constructions(
        landmarks, construction_namespace="analysis:1"
    )["CRANIOM_AB_PRIME_V1"]

    assert construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE
    assert construction.missing_landmark_ids == ["A"]
    assert set(construction.geometry) == {"geometric_convention"}
    provenance = construction.geometry["geometric_convention"]
    assert provenance["convention_id"] == "CRANIOM_AB_PRIME_FH_V1"
    assert provenance["reference_frame_id"] == "FH_PO_OR_V1"


def test_invalid_cross_image_construction_keeps_convention_but_withholds_patient_geometry() -> None:
    landmarks = _complete_landmarks()
    landmarks["Or"] = _landmark("Or", 100.0, 50.0, source_image_ref="img:2")

    construction = materialize_craniom_linear_constructions(
        landmarks, construction_namespace="analysis:1"
    )["CRANIOM_AB_PRIME_V1"]

    assert construction.availability_status == AvailabilityStatus.INVALID
    assert set(construction.geometry) == {"geometric_convention"}
    provenance = construction.geometry["geometric_convention"]
    assert provenance["convention_id"] == "CRANIOM_AB_PRIME_FH_V1"
