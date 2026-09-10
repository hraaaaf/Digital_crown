"""Materialize versioned CRANIOM constructions from typed landmark evidence.

This layer records deterministic geometric dependencies only. It does not
compute norms, interpret measurements, diagnose patients or select treatment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    LandmarkEvidence,
)


@dataclass(frozen=True)
class _ConstructionSpec:
    definition_id: str
    required_landmark_ids: tuple[str, ...]
    geometry: Mapping[str, str]
    definition_version: str = "1"


_CRANIOM_LINEAR_CONSTRUCTIONS: Sequence[_ConstructionSpec] = (
    _ConstructionSpec(
        definition_id="CRANIOM_A_TO_N_VERTICAL_V1",
        required_landmark_ids=("A", "N", "Po", "Or"),
        geometry={
            "kind": "signed_axis_distance",
            "axis_definition": "FH_PO_OR_V1",
            "origin_landmark": "N",
            "target_landmark": "A",
            "coordinate_space": "source_image_pixels",
        },
    ),
    _ConstructionSpec(
        definition_id="CRANIOM_B_TO_N_VERTICAL_V1",
        required_landmark_ids=("B", "N", "Po", "Or"),
        geometry={
            "kind": "signed_axis_distance",
            "axis_definition": "FH_PO_OR_V1",
            "origin_landmark": "N",
            "target_landmark": "B",
            "coordinate_space": "source_image_pixels",
        },
    ),
    _ConstructionSpec(
        definition_id="CRANIOM_AB_PRIME_V1",
        required_landmark_ids=("A", "B", "Po", "Or"),
        geometry={
            "kind": "signed_projected_distance",
            "axis_definition": "FH_PO_OR_V1",
            "posterior_landmark": "B",
            "anterior_landmark": "A",
            "coordinate_space": "source_image_pixels",
        },
    ),
    _ConstructionSpec(
        definition_id="CRANIOM_S_TO_N_VERTICAL_DEPTH_V1",
        required_landmark_ids=("S", "N", "Po", "Or"),
        geometry={
            "kind": "absolute_axis_distance",
            "axis_definition": "FH_PO_OR_V1",
            "origin_landmark": "N",
            "target_landmark": "S",
            "coordinate_space": "source_image_pixels",
        },
    ),
)


def _collect_dependencies(
    landmarks: Mapping[str, LandmarkEvidence],
    required_ids: tuple[str, ...],
) -> tuple[list[str], list[str], set[str]]:
    refs: list[str] = []
    unavailable: list[str] = []
    source_images: set[str] = set()

    for landmark_id in required_ids:
        landmark = landmarks.get(landmark_id)
        if landmark is None:
            unavailable.append(landmark_id)
            continue
        if landmark.landmark_id != landmark_id:
            raise ValueError(
                f"Landmark mapping key {landmark_id} resolves to {landmark.landmark_id}"
            )
        refs.append(landmark.evidence_id)
        source_images.add(landmark.source_image_ref)
        if landmark.availability_status != AvailabilityStatus.AVAILABLE:
            unavailable.append(landmark_id)

    if len(refs) != len(set(refs)):
        raise ValueError("A construction cannot reuse one evidence id for distinct landmarks")
    return refs, unavailable, source_images


def materialize_craniom_linear_constructions(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    construction_namespace: str,
) -> dict[str, ConstructionEvidence]:
    """Create typed construction evidence for the certified CRANIOM linear set.

    Missing or unavailable landmarks produce a materialized ``NOT_COMPUTABLE``
    construction rather than a fabricated landmark reference. Landmarks from
    different source images produce ``INVALID`` construction evidence.
    """

    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    materialized: dict[str, ConstructionEvidence] = {}
    for spec in _CRANIOM_LINEAR_CONSTRUCTIONS:
        refs, unavailable, source_images = _collect_dependencies(
            landmarks, spec.required_landmark_ids
        )

        availability = AvailabilityStatus.AVAILABLE
        geometry = dict(spec.geometry)
        if unavailable:
            availability = AvailabilityStatus.NOT_COMPUTABLE
            geometry = {}
        elif len(source_images) != 1:
            availability = AvailabilityStatus.INVALID
            geometry = {}
        else:
            geometry["source_image_ref"] = next(iter(source_images))

        materialized[spec.definition_id] = ConstructionEvidence(
            construction_id=f"{construction_namespace}:{spec.definition_id}",
            definition_id=spec.definition_id,
            definition_version=spec.definition_version,
            landmark_refs=refs,
            missing_landmark_ids=unavailable,
            geometry=geometry,
            evidence_refs=refs,
            availability_status=availability,
        )

    return materialized


CRANIOM_LINEAR_REQUIRED_LANDMARKS = {
    spec.definition_id: spec.required_landmark_ids
    for spec in _CRANIOM_LINEAR_CONSTRUCTIONS
}
