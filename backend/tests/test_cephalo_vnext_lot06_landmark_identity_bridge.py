from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_landmark_identity_bridge import (
    CanonicalLandmarkIdentityError,
    project_canonical_landmark_identities,
)
from backend.services.srpose38_contract import (
    SRPOSE38_MODEL_NAME,
    SRPOSE38_MODEL_SHA256,
    SRPOSE38_PIPELINE_VERSION,
)


def _auto(landmark_id: str) -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"landmark:auto:{landmark_id}",
        landmark_id=landmark_id,
        x=10.0,
        y=20.0,
        source_image_ref="source:ceph",
        origin=LandmarkOrigin.SRPOSE38_AUTO,
        model_id=SRPOSE38_MODEL_NAME,
        model_sha256=SRPOSE38_MODEL_SHA256,
        pipeline_version=SRPOSE38_PIPELINE_VERSION,
        evidence_refs=["source:ceph"],
        evidence_status=EvidenceStatus.COMPUTED,
    )


def _manual(landmark_id: str) -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"landmark:manual:{landmark_id}",
        landmark_id=landmark_id,
        x=11.0,
        y=21.0,
        source_image_ref="source:ceph",
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:ceph"],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def test_certified_srpose_points_gain_additive_canonical_identities():
    projected = project_canonical_landmark_identities(
        {key: _auto(key) for key in ("Po", "Co", "Gn", "Pog")}
    )
    assert set(("Po_anatomic", "Co_anatomic", "Gn_anatomic", "Pog_hard")).issubset(projected)
    assert projected["Po_anatomic"].x == projected["Po"].x
    assert projected["Pog_hard"].y == projected["Pog"].y
    assert projected["Po"].landmark_id == "Po"


def test_manual_revision_requires_certified_auto_predecessor():
    current = {"Po": _manual("Po")}
    assert "Po_anatomic" not in project_canonical_landmark_identities(current)
    projected = project_canonical_landmark_identities(
        current, previous_auto_landmarks=[_auto("Po")]
    )
    assert projected["Po_anatomic"].x == 11.0
    assert projected["Po_anatomic"].origin == LandmarkOrigin.MANUAL


def test_wrong_model_provenance_fails_closed():
    bad = _auto("Po").model_copy(update={"model_sha256": "wrong"})
    projected = project_canonical_landmark_identities({"Po": bad})
    assert "Po_anatomic" not in projected


def test_preexisting_canonical_identity_collision_fails_closed():
    with pytest.raises(CanonicalLandmarkIdentityError):
        project_canonical_landmark_identities(
            {"Po": _auto("Po"), "Po_anatomic": _manual("Po_anatomic")}
        )
