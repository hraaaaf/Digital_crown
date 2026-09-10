"""Case-level integrity gate for the typed cephalometric evidence graph.

This is a stricter wrapper around ``validate_evidence_graph``. It binds every
patient evidence source to one explicit patient/case context and requires real
ClinicianValidationEvidence records for accepted/edited diagnostic objects and
clinician-selected treatment options.

It does not compute measurements, apply norms, diagnose, or choose treatment.
"""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Tuple

from backend.schemas.cephalo_evidence import (
    ClinicianValidationEvidence,
    DiagnosticHypothesisEvidence,
    ObjectiveEvidence,
    ProblemEvidence,
    ReviewState,
    TreatmentOptionEvidence,
    TreatmentOptionStatus,
    ValidationAction,
)
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
    validate_evidence_graph,
)
from backend.services.cephalo_norm_registry import NormRegistry, registry as default_norm_registry


_ACCEPT_ACTIONS = {ValidationAction.ACCEPT, ValidationAction.EDIT}


def _require_context_value(value: object, name: str) -> None:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise EvidenceGraphValidationError(f"{name} must be explicit and non-empty")


def _validation_index(
    graph: EvidenceGraphSnapshot,
) -> DefaultDict[Tuple[str, str], list[ClinicianValidationEvidence]]:
    indexed: DefaultDict[Tuple[str, str], list[ClinicianValidationEvidence]] = defaultdict(list)
    for validation in graph.validations:
        indexed[(validation.target_type, validation.target_id)].append(validation)
    return indexed


def _require_matching_validation(
    validations: DefaultDict[Tuple[str, str], list[ClinicianValidationEvidence]],
    *,
    target_type: str,
    target_id: str,
    clinician_id: str | None,
    validated_at: object,
) -> None:
    candidates = validations.get((target_type, target_id), [])
    if not any(
        candidate.clinician_id == clinician_id
        and candidate.validated_at == validated_at
        and candidate.action in _ACCEPT_ACTIONS
        for candidate in candidates
    ):
        raise EvidenceGraphValidationError(
            f"{target_type} {target_id} claims clinician acceptance without a matching "
            "ClinicianValidationEvidence audit record"
        )


def validate_case_evidence_graph(
    graph: EvidenceGraphSnapshot,
    *,
    patient_id: int,
    case_id: str,
    norm_registry: NormRegistry = default_norm_registry,
) -> None:
    """Validate graph integrity plus one explicit patient/case boundary.

    The base resolver already enforces globally unique ids and a monotonic typed
    dependency chain (source -> landmark -> construction -> measurement -> ...),
    which prevents backward/self derivation references. This wrapper adds the
    patient/case and clinician-audit invariants needed before the graph can be
    used as a clinical source of truth.
    """

    _require_context_value(patient_id, "patient_id")
    _require_context_value(case_id, "case_id")
    validate_evidence_graph(graph, norm_registry=norm_registry)

    if not graph.sources:
        raise EvidenceGraphValidationError(
            "Case evidence graph requires at least one patient SourceEvidence"
        )

    for source in graph.sources:
        if source.patient_id != patient_id:
            raise EvidenceGraphValidationError(
                f"Source {source.evidence_id} belongs to patient {source.patient_id}, "
                f"expected {patient_id}"
            )
        source_case_id = source.metadata.get("case_id")
        if source_case_id != case_id:
            raise EvidenceGraphValidationError(
                f"Source {source.evidence_id} has case_id {source_case_id!r}, "
                f"expected {case_id!r}"
            )

    validations = _validation_index(graph)

    for diagnosis in graph.diagnoses:
        if diagnosis.state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
            _require_matching_validation(
                validations,
                target_type="diagnosis",
                target_id=diagnosis.diagnosis_id,
                clinician_id=diagnosis.clinician_id,
                validated_at=diagnosis.clinician_validated_at,
            )

    for problem in graph.problems:
        if problem.state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
            _require_matching_validation(
                validations,
                target_type="problem",
                target_id=problem.problem_id,
                clinician_id=problem.clinician_id,
                validated_at=problem.clinician_validated_at,
            )

    for objective in graph.objectives:
        if objective.state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
            _require_matching_validation(
                validations,
                target_type="objective",
                target_id=objective.objective_id,
                clinician_id=objective.clinician_id,
                validated_at=objective.clinician_validated_at,
            )

    for option in graph.treatment_options:
        if option.status == TreatmentOptionStatus.CLINICIAN_SELECTED:
            _require_matching_validation(
                validations,
                target_type="treatment_option",
                target_id=option.option_id,
                clinician_id=option.clinician_id,
                validated_at=option.clinician_selected_at,
            )
