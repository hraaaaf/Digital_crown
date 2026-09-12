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
from backend.services.cephalo_craniom_angular import (
    craniom_interincisal_deg_v1,
    craniom_l1_downs_deg_v1,
    craniom_u1_frankfort_deg_v1,
)
from backend.services.cephalo_geometric_conventions import (
    geometric_convention_metadata,
    get_active_craniom_convention,
)
from backend.services.cephalo_mcnamara_evidence import materialize_mcnamara_constructions
from backend.services.cephalo_ricketts_evidence import materialize_ricketts_constructions


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
        required_landmark_ids=("A", "B", "N", "Po", "Or"),
        geometry={
            "kind": "signed_clinical_projected_distance",
            "axis_definition": "FH_PO_OR_V1",
            "mcnamara_origin_landmark": "N",
            "mcnamara_relation": "perpendicular_to_FH",
            "a_prime_construction": "parallel_to_McNamara_through_A_intersect_FH",
            "b_prime_construction": "parallel_to_McNamara_through_B_intersect_FH",
            "posterior_landmark": "B",
            "anterior_landmark": "A",
            "positive_direction": "A_anterior_to_B_along_Po_to_Or",
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

_CRANIOM_ANGULAR_CONSTRUCTIONS: Sequence[_ConstructionSpec] = (
    _ConstructionSpec(
        definition_id="CRANIOM_U1_TO_FRANKFORT_V1",
        required_landmark_ids=("U1_apex", "U1_incisal", "Po", "Or"),
        geometry={
            "kind": "directed_clinical_angle",
            "axis_definition": "FH_PO_OR_V1",
            "tooth_axis_start": "U1_apex",
            "tooth_axis_end": "U1_incisal",
            "reference_axis_start": "Po",
            "reference_axis_end": "Or",
            "angle_convention": "clinical_obtuse_v1",
            "coordinate_space": "source_image_pixels",
        },
    ),
    _ConstructionSpec(
        definition_id="CRANIOM_L1_TO_DOWNS_MP_V1",
        required_landmark_ids=("L1_apex", "L1_incisal", "Go", "Me"),
        geometry={
            "kind": "directed_clinical_angle",
            "axis_definition": "DOWNS_MP_GO_ME_V1",
            "tooth_axis_start": "L1_apex",
            "tooth_axis_end": "L1_incisal",
            "reference_axis_start": "Go",
            "reference_axis_end": "Me",
            "angle_convention": "clinical_obtuse_v1",
            "coordinate_space": "source_image_pixels",
        },
    ),
    _ConstructionSpec(
        definition_id="CRANIOM_U1_L1_INTERINCISAL_V1",
        required_landmark_ids=("U1_apex", "U1_incisal", "L1_apex", "L1_incisal"),
        geometry={
            "kind": "interaxial_clinical_angle",
            "axis_definition": "U1_L1_LONG_AXES_V1",
            "upper_axis_start": "U1_apex",
            "upper_axis_end": "U1_incisal",
            "lower_axis_start": "L1_apex",
            "lower_axis_end": "L1_incisal",
            "angle_convention": "larger_supplementary_v1",
            "coordinate_space": "source_image_pixels",
        },
    ),
)

_CRANIOM_CONSTRUCTIONS: Sequence[_ConstructionSpec] = (
    *_CRANIOM_LINEAR_CONSTRUCTIONS,
    *_CRANIOM_ANGULAR_CONSTRUCTIONS,
)


def _validate_construction_specs_against_conventions() -> None:
    """Fail import-time if executable geometry drifts from its convention."""

    for spec in _CRANIOM_CONSTRUCTIONS:
        convention = get_active_craniom_convention(spec.definition_id)
        if convention.required_landmark_ids != spec.required_landmark_ids:
            raise RuntimeError(
                f"Geometric convention landmark drift for {spec.definition_id}"
            )
        if convention.reference_frame_id != spec.geometry.get("axis_definition"):
            raise RuntimeError(
                f"Geometric convention reference-frame drift for {spec.definition_id}"
            )


_validate_construction_specs_against_conventions()


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


def _convention_only_geometry(definition_id: str) -> dict[str, object]:
    return {"geometric_convention": geometric_convention_metadata(definition_id)}


def _materialize_computed_geometry(
    spec: _ConstructionSpec,
    landmarks: Mapping[str, LandmarkEvidence],
    geometry: dict[str, object],
) -> bool:
    """Attach calibration-independent patient geometry; return False if degenerate."""

    if spec.definition_id == "CRANIOM_U1_TO_FRANKFORT_V1":
        value = craniom_u1_frankfort_deg_v1(
            (landmarks["U1_apex"].x, landmarks["U1_apex"].y),
            (landmarks["U1_incisal"].x, landmarks["U1_incisal"].y),
            (landmarks["Po"].x, landmarks["Po"].y),
            (landmarks["Or"].x, landmarks["Or"].y),
        )
    elif spec.definition_id == "CRANIOM_L1_TO_DOWNS_MP_V1":
        value = craniom_l1_downs_deg_v1(
            (landmarks["L1_apex"].x, landmarks["L1_apex"].y),
            (landmarks["L1_incisal"].x, landmarks["L1_incisal"].y),
            (landmarks["Go"].x, landmarks["Go"].y),
            (landmarks["Me"].x, landmarks["Me"].y),
        )
    elif spec.definition_id == "CRANIOM_U1_L1_INTERINCISAL_V1":
        value = craniom_interincisal_deg_v1(
            (landmarks["U1_apex"].x, landmarks["U1_apex"].y),
            (landmarks["U1_incisal"].x, landmarks["U1_incisal"].y),
            (landmarks["L1_apex"].x, landmarks["L1_apex"].y),
            (landmarks["L1_incisal"].x, landmarks["L1_incisal"].y),
        )
    else:
        return True

    if value is None:
        return False
    geometry["computed_angle_deg"] = round(value, 1)
    return True


def materialize_craniom_constructions(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    construction_namespace: str,
) -> dict[str, ConstructionEvidence]:
    if not isinstance(construction_namespace, str) or not construction_namespace.strip():
        raise ValueError("construction_namespace must be non-empty")

    materialized: dict[str, ConstructionEvidence] = {}
    for spec in _CRANIOM_CONSTRUCTIONS:
        refs, unavailable, source_images = _collect_dependencies(
            landmarks, spec.required_landmark_ids
        )

        availability = AvailabilityStatus.AVAILABLE
        geometry: dict[str, object] = dict(spec.geometry)
        if unavailable:
            availability = AvailabilityStatus.NOT_COMPUTABLE
            geometry = _convention_only_geometry(spec.definition_id)
        elif len(source_images) != 1:
            availability = AvailabilityStatus.INVALID
            geometry = _convention_only_geometry(spec.definition_id)
        else:
            geometry["source_image_ref"] = next(iter(source_images))
            geometry["geometric_convention"] = geometric_convention_metadata(
                spec.definition_id
            )
            if not _materialize_computed_geometry(spec, landmarks, geometry):
                availability = AvailabilityStatus.INVALID
                geometry = _convention_only_geometry(spec.definition_id)

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


def materialize_craniom_linear_constructions(
    landmarks: Mapping[str, LandmarkEvidence],
    *,
    construction_namespace: str,
) -> dict[str, ConstructionEvidence]:
    materialized = materialize_craniom_constructions(
        landmarks, construction_namespace=construction_namespace
    )
    materialized.update(
        materialize_mcnamara_constructions(
            landmarks,
            construction_namespace=f"{construction_namespace}:r8",
        )
    )
    materialized.update(
        materialize_ricketts_constructions(
            landmarks,
            construction_namespace=f"{construction_namespace}:r9",
        )
    )
    return materialized


CRANIOM_LINEAR_REQUIRED_LANDMARKS = {
    spec.definition_id: spec.required_landmark_ids
    for spec in _CRANIOM_LINEAR_CONSTRUCTIONS
}
CRANIOM_ANGULAR_REQUIRED_LANDMARKS = {
    spec.definition_id: spec.required_landmark_ids
    for spec in _CRANIOM_ANGULAR_CONSTRUCTIONS
}
CRANIOM_REQUIRED_LANDMARKS = {
    **CRANIOM_LINEAR_REQUIRED_LANDMARKS,
    **CRANIOM_ANGULAR_REQUIRED_LANDMARKS,
}
