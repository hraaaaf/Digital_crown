"""Versioned geometric conventions for the currently supported CRANIOM runtime.

This registry binds a construction identifier to one explicit geometric frame,
operation, landmark vocabulary and source set. It intentionally contains no
norm, interpretation, diagnosis or treatment rule.

Unsupported conventions are registered as blocked contracts so they cannot be
silently approximated with a different landmark or reference frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


CRANIOM_SOURCE_REFERENCES: tuple[str, ...] = (
    "doi:10.1051/odfen/2010406",
    "doi:10.1051/odfen/2011104",
)
DOWNS_MANDIBULAR_PLANE_SOURCE_REFERENCES: tuple[str, ...] = (
    "doi:10.1016/0002-9416(48)90015-3",
)
CRANIOM_L1_DOWNS_SOURCE_REFERENCES: tuple[str, ...] = (
    *CRANIOM_SOURCE_REFERENCES,
    *DOWNS_MANDIBULAR_PLANE_SOURCE_REFERENCES,
)


@dataclass(frozen=True)
class GeometricConventionSpec:
    convention_id: str
    construction_definition_id: str | None
    clinical_label: str
    reference_frame_id: str | None
    operation: str
    required_landmark_ids: tuple[str, ...]
    source_references: tuple[str, ...]
    constructable: bool
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.convention_id.strip():
            raise ValueError("convention_id must be non-empty")
        if not self.clinical_label.strip():
            raise ValueError("clinical_label must be non-empty")
        if not self.operation.strip():
            raise ValueError("operation must be non-empty")
        if not self.source_references:
            raise ValueError("geometric convention requires source references")
        if self.constructable:
            if not self.construction_definition_id:
                raise ValueError("constructable convention requires definition id")
            if not self.reference_frame_id:
                raise ValueError("constructable convention requires reference frame")
            if not self.required_landmark_ids:
                raise ValueError("constructable convention requires landmarks")
            if self.blocked_reason is not None:
                raise ValueError("constructable convention cannot declare blocked_reason")
        elif not self.blocked_reason:
            raise ValueError("blocked convention requires an explicit reason")


_ACTIVE_CONVENTIONS: tuple[GeometricConventionSpec, ...] = (
    GeometricConventionSpec(
        convention_id="CRANIOM_SITUATION_A_FH_V1",
        construction_definition_id="CRANIOM_A_TO_N_VERTICAL_V1",
        clinical_label="Situation A",
        reference_frame_id="FH_PO_OR_V1",
        operation="signed AP distance from N-perpendicular-to-Frankfort to A",
        required_landmark_ids=("A", "N", "Po", "Or"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=True,
    ),
    GeometricConventionSpec(
        convention_id="CRANIOM_SITUATION_B_FH_V1",
        construction_definition_id="CRANIOM_B_TO_N_VERTICAL_V1",
        clinical_label="Situation B",
        reference_frame_id="FH_PO_OR_V1",
        operation="signed AP distance from N-perpendicular-to-Frankfort to B",
        required_landmark_ids=("B", "N", "Po", "Or"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=True,
    ),
    GeometricConventionSpec(
        convention_id="CRANIOM_AB_PRIME_FH_V1",
        construction_definition_id="CRANIOM_AB_PRIME_V1",
        clinical_label="A'B'",
        reference_frame_id="FH_PO_OR_V1",
        operation=(
            "construct McNamara as the perpendicular to Frankfort through N; "
            "construct parallels through A and B; intersect those parallels with "
            "Frankfort at A' and B'; measure signed A'B' along Frankfort, positive "
            "when A is anterior to B"
        ),
        required_landmark_ids=("A", "B", "N", "Po", "Or"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=True,
    ),
    GeometricConventionSpec(
        convention_id="CRANIOM_FACIAL_DEPTH_FH_V1",
        construction_definition_id="CRANIOM_S_TO_N_VERTICAL_DEPTH_V1",
        clinical_label="Profondeur faciale",
        reference_frame_id="FH_PO_OR_V1",
        operation="absolute AP distance from N-perpendicular-to-Frankfort to S",
        required_landmark_ids=("S", "N", "Po", "Or"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=True,
    ),
    GeometricConventionSpec(
        convention_id="CRANIOM_U1_FRANKFORT_ANGLE_V1",
        construction_definition_id="CRANIOM_U1_TO_FRANKFORT_V1",
        clinical_label="Incisive supérieure / Frankfort",
        reference_frame_id="FH_PO_OR_V1",
        operation="clinical obtuse angle between U1 apex-to-incisal long axis and Frankfort Po-to-Or",
        required_landmark_ids=("U1_apex", "U1_incisal", "Po", "Or"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=True,
    ),
    GeometricConventionSpec(
        convention_id="CRANIOM_L1_DOWNS_ANGLE_V1",
        construction_definition_id="CRANIOM_L1_TO_DOWNS_MP_V1",
        clinical_label="Incisive inférieure / plan mandibulaire de Downs",
        reference_frame_id="DOWNS_MP_GO_ME_V1",
        operation="clinical obtuse angle between L1 apex-to-incisal long axis and Downs mandibular plane Go-to-Me",
        required_landmark_ids=("L1_apex", "L1_incisal", "Go", "Me"),
        source_references=CRANIOM_L1_DOWNS_SOURCE_REFERENCES,
        constructable=True,
    ),
    GeometricConventionSpec(
        convention_id="CRANIOM_INTERINCISAL_ANGLE_V1",
        construction_definition_id="CRANIOM_U1_L1_INTERINCISAL_V1",
        clinical_label="Angle inter-incisif",
        reference_frame_id="U1_L1_LONG_AXES_V1",
        operation="larger supplementary angle between U1 and L1 apex-to-incisal long axes",
        required_landmark_ids=("U1_apex", "U1_incisal", "L1_apex", "L1_incisal"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=True,
    ),
)


_BLOCKED_CONVENTIONS: tuple[GeometricConventionSpec, ...] = (
    GeometricConventionSpec(
        convention_id="CRANIOM_AB_DOUBLE_PRIME_HORIZONTAL_GAZE_V1",
        construction_definition_id=None,
        clinical_label="A''B''",
        reference_frame_id=None,
        operation="projection on a validated horizontal-gaze / natural-head-position reference",
        required_landmark_ids=("A", "B"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=False,
        blocked_reason="HORIZONTAL_GAZE_NHP_PROTOCOL_NOT_AVAILABLE_IN_RUNTIME",
    ),
    GeometricConventionSpec(
        convention_id="CRANIOM_GI_GS_MANDIBULAR_FRAME_V1",
        construction_definition_id=None,
        clinical_label="CRANIOM mandibular Gi/Gs frame",
        reference_frame_id=None,
        operation="Gi/Gs-dependent mandibular construction",
        required_landmark_ids=("Gi", "Gs"),
        source_references=CRANIOM_SOURCE_REFERENCES,
        constructable=False,
        blocked_reason="GI_GS_LANDMARKS_NOT_AVAILABLE_IN_SRPOSE38_RUNTIME",
    ),
)


ACTIVE_CRANIOM_CONVENTIONS: Mapping[str, GeometricConventionSpec] = {
    spec.construction_definition_id: spec
    for spec in _ACTIVE_CONVENTIONS
    if spec.construction_definition_id is not None
}

BLOCKED_CRANIOM_CONVENTIONS: Mapping[str, GeometricConventionSpec] = {
    spec.convention_id: spec for spec in _BLOCKED_CONVENTIONS
}


def get_active_craniom_convention(definition_id: str) -> GeometricConventionSpec:
    """Resolve one constructable CRANIOM convention, failing closed if unknown."""

    try:
        return ACTIVE_CRANIOM_CONVENTIONS[definition_id]
    except KeyError as exc:
        raise ValueError(
            f"No active geometric convention registered for {definition_id}"
        ) from exc


def geometric_convention_metadata(definition_id: str) -> dict[str, object]:
    """Return immutable scientific provenance materialized into ConstructionEvidence."""

    spec = get_active_craniom_convention(definition_id)
    return {
        "convention_id": spec.convention_id,
        "clinical_label": spec.clinical_label,
        "reference_frame_id": spec.reference_frame_id,
        "operation": spec.operation,
        "source_references": list(spec.source_references),
    }
