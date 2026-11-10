"""Fail-closed canonical landmark identity projection for Cephalo LOT06.

A pinned SRPose38 SHA certifies *file provenance*, not anatomical identity.
Canonical aliases are produced only for explicitly clinician-attested manual
landmarks. Existing persisted/runtime IDs are not renamed or migrated.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
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


def _has_pinned_srpose_provenance(item: LandmarkEvidence) -> bool:
    """Check numeric model provenance only; never claim anatomical validation."""
    return (
        item.origin == LandmarkOrigin.SRPOSE38_AUTO
        and item.model_id == SRPOSE38_MODEL_NAME
        and item.model_sha256 == SRPOSE38_MODEL_SHA256
        and item.pipeline_version == SRPOSE38_PIPELINE_VERSION
    )


def _is_explicitly_clinician_attested(item: LandmarkEvidence) -> bool:
    """Unreviewed auto/missing points cannot gain canonical anatomical aliases."""
    return (
        item.origin in {LandmarkOrigin.MANUAL, LandmarkOrigin.MANUAL_CORRECTED}
        and item.availability_status == AvailabilityStatus.AVAILABLE
        and item.evidence_status == EvidenceStatus.CLINICIAN_VALIDATED
        and isinstance(item.validated_by, str)
        and bool(item.validated_by.strip())
        and item.validated_at is not None
        and item.validated_at.tzinfo is not None
        and item.validated_at.utcoffset() is not None
    )


def _manual_correction_has_matched_predecessor(
    item: LandmarkEvidence,
    previous_auto: Mapping[str, LandmarkEvidence],
) -> bool:
    """Bind corrections to a same-ID, same-image original observation."""
    if item.origin != LandmarkOrigin.MANUAL_CORRECTED:
        return False
    previous = previous_auto.get(item.landmark_id)
    return (
        previous is not None
        and _has_pinned_srpose_provenance(previous)
        and previous.source_image_ref == item.source_image_ref
        and item.original_auto_x is not None
        and item.original_auto_y is not None
        and abs(previous.x - item.original_auto_x) <= 1e-6
        and abs(previous.y - item.original_auto_y) <= 1e-6
    )


def project_canonical_landmark_identities(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    previous_auto_landmarks: Sequence[LandmarkEvidence] = (),
) -> dict[str, LandmarkEvidence]:
    """Return additive canonical identity aliases without mutating legacy points."""
    previous_auto = {item.landmark_id: item for item in previous_auto_landmarks}
    # The scientific view is deliberately narrower than the persisted legacy
    # points. Preserve all IDs/coordinates in the legacy snapshot, while blocking
    # calculations based on any unreviewed channel, even when OTHER inputs
    # (e.g. Porion) have been manually attested.
    projected: dict[str, LandmarkEvidence] = {}
    for key, item in landmarks.items():
        reviewed = _is_explicitly_clinician_attested(item)
        if reviewed and item.origin == LandmarkOrigin.MANUAL_CORRECTED:
            reviewed = _manual_correction_has_matched_predecessor(item, previous_auto)
        projected[key] = (
            item if reviewed else item.model_copy(
                update={"availability_status": AvailabilityStatus.NOT_COMPUTABLE}
            )
        )

    # Reject pre-labelled canonical inputs that lack human attestation as well.
    # This prevents an automatic point arriving under a canonical ID directly.
    canonical_ids = set(CANONICAL_LANDMARK_ALIASES.values())
    canonical_ids.update(EXPLICIT_ONLY_CANONICAL_IDENTITIES)
    for canonical_id in canonical_ids.intersection(landmarks):
        if not _is_explicitly_clinician_attested(landmarks[canonical_id]):
            raise CanonicalLandmarkIdentityError(
                f"Unreviewed canonical identity {canonical_id} is not allowed"
            )

    for legacy_id, canonical_id in CANONICAL_LANDMARK_ALIASES.items():
        item = landmarks.get(legacy_id)
        if item is None:
            continue
        if canonical_id in landmarks:
            raise CanonicalLandmarkIdentityError(
                f"Input already contains canonical identity {canonical_id}; "
                "legacy/canonical collision is not allowed"
            )
        # Source-checkpoint provenance alone never establishes anatomy.
        # An explicitly reviewed manual point carries a clinician assertion;
        # a correction must also match the original same-image observation.
        if not _is_explicitly_clinician_attested(item):
            continue
        if (
            item.origin == LandmarkOrigin.MANUAL_CORRECTED
            and not _manual_correction_has_matched_predecessor(item, previous_auto)
        ):
            continue

        payload = item.model_dump()
        payload["landmark_id"] = canonical_id
        payload["evidence_id"] = f"{item.evidence_id}:canonical:{canonical_id}"
        projected[canonical_id] = LandmarkEvidence.model_validate(payload)

    return projected
