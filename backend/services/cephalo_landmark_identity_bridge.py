"""Fail-closed canonical landmark identity projection for Cephalo LOT06.

Legacy persisted/runtime IDs remain untouched. New scientific consumers may use
explicit canonical identities only when the underlying legacy point comes from
the certified SRPose38 contract, or when a manual revision can be traced to a
previous certified SRPose38 observation of the same legacy ID.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from backend.schemas.cephalo_evidence import LandmarkEvidence, LandmarkOrigin
from backend.services.srpose38_contract import (
    SRPOSE38_MODEL_NAME,
    SRPOSE38_MODEL_SHA256,
    SRPOSE38_PIPELINE_VERSION,
)

CANONICAL_LANDMARK_ALIASES: dict[str, str] = {
    "Po": "Po_anatomic",
    "Co": "Co_anatomic",
    "Pog": "Pog_hard",
}

EXPLICIT_ONLY_CANONICAL_IDENTITIES = frozenset({"Gn_anatomic", "Pt_Ricketts"})


class CanonicalLandmarkIdentityError(ValueError):
    pass


def _is_certified_srpose(item: LandmarkEvidence) -> bool:
    return (
        item.origin == LandmarkOrigin.SRPOSE38_AUTO
        and item.model_id == SRPOSE38_MODEL_NAME
        and item.model_sha256 == SRPOSE38_MODEL_SHA256
        and item.pipeline_version == SRPOSE38_PIPELINE_VERSION
    )


def _manual_has_certified_predecessor(
    item: LandmarkEvidence,
    previous_auto: Mapping[str, LandmarkEvidence],
) -> bool:
    if item.origin not in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}:
        return False
    previous = previous_auto.get(item.landmark_id)
    return previous is not None and _is_certified_srpose(previous)


def project_canonical_landmark_identities(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    previous_auto_landmarks: Sequence[LandmarkEvidence] = (),
) -> dict[str, LandmarkEvidence]:
    """Return additive canonical identity aliases without mutating legacy points."""
    projected = dict(landmarks)
    previous_auto = {item.landmark_id: item for item in previous_auto_landmarks}

    for legacy_id, canonical_id in CANONICAL_LANDMARK_ALIASES.items():
        item = landmarks.get(legacy_id)
        if item is None:
            continue
        if canonical_id in landmarks:
            raise CanonicalLandmarkIdentityError(
                f"Input already contains canonical identity {canonical_id}; "
                "legacy/canonical collision is not allowed"
            )
        if not (
            _is_certified_srpose(item)
            or _manual_has_certified_predecessor(item, previous_auto)
        ):
            continue

        payload = item.model_dump()
        payload["landmark_id"] = canonical_id
        payload["evidence_id"] = f"{item.evidence_id}:canonical:{canonical_id}"
        projected[canonical_id] = LandmarkEvidence.model_validate(payload)

    return projected
