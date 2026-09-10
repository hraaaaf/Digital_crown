"""Case-boundary tests for the cephalometric evidence graph."""

from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import (
    ClinicianValidationEvidence,
    DiagnosticHypothesisEvidence,
    EvidenceStatus,
    FindingEvidence,
    ObjectiveEvidence,
    ProblemEvidence,
    ReviewState,
    SourceEvidence,
    TreatmentOptionEvidence,
    TreatmentOptionStatus,
    ValidationAction,
)
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
)


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
PATIENT_ID = 7
CASE_ID = "case:orthodontic:7:1"
CLINICIAN_ID = "clinician:1"


def _source(
    *,
    evidence_id: str = "source:ceph:1",
    patient_id: int = PATIENT_ID,
    case_id: str | None = CASE_ID,
) -> SourceEvidence:
    metadata = {} if case_id is None else {"case_id": case_id}
    return SourceEvidence(
        evidence_id=evidence_id,
        patient_id=patient_id,
        kind="lateral_ceph",
        source_record_id=f"record:{evidence_id}",
        recorded_at=NOW,
        operator_id=CLINICIAN_ID,
        metadata=metadata,
    )


def _finding() -> FindingEvidence:
    return FindingEvidence(
        finding_id="finding:1",
        domain="synthetic",
        rule_id="SYNTHETIC_INTEGRITY_ONLY",
        rule_version="1",
        supporting_evidence_refs=["source:ceph:1"],
        statement="Synthetic finding for graph-integrity tests only.",
        evidence_status=EvidenceStatus.INTERPRETED,
    )


def _diagnosis(*, state: ReviewState = ReviewState.PROPOSED) -> DiagnosticHypothesisEvidence:
    kwargs = {}
    if state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
        kwargs = {"clinician_id": CLINICIAN_ID, "clinician_validated_at": NOW}
    return DiagnosticHypothesisEvidence(
        diagnosis_id="diagnosis:1",
        domain="synthetic",
        supporting_finding_refs=["finding:1"],
        statement="Synthetic diagnosis for graph-integrity tests only.",
        state=state,
        **kwargs,
    )


def _problem(*, state: ReviewState = ReviewState.PROPOSED) -> ProblemEvidence:
    kwargs = {}
    if state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
        kwargs = {"clinician_id": CLINICIAN_ID, "clinician_validated_at": NOW}
    return ProblemEvidence(
        problem_id="problem:1",
        diagnosis_refs=["diagnosis:1"],
        evidence_refs=["diagnosis:1"],
        statement="Synthetic problem for graph-integrity tests only.",
        state=state,
        **kwargs,
    )


def _objective(*, state: ReviewState = ReviewState.PROPOSED) -> ObjectiveEvidence:
    kwargs = {}
    if state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
        kwargs = {"clinician_id": CLINICIAN_ID, "clinician_validated_at": NOW}
    return ObjectiveEvidence(
        objective_id="objective:1",
        problem_refs=["problem:1"],
        target="Synthetic target",
        success_criterion="Synthetic success criterion",
        state=state,
        **kwargs,
    )


def _option(*, selected: bool = False) -> TreatmentOptionEvidence:
    kwargs = {}
    status = TreatmentOptionStatus.EVALUABLE
    if selected:
        status = TreatmentOptionStatus.CLINICIAN_SELECTED
        kwargs = {"clinician_id": CLINICIAN_ID, "clinician_selected_at": NOW}
    return TreatmentOptionEvidence(
        option_id="option:1",
        objective_refs=["objective:1"],
        required_evidence_refs=["source:ceph:1"],
        status=status,
        **kwargs,
    )


def _validation(
    target_type: str,
    target_id: str,
    *,
    clinician_id: str = CLINICIAN_ID,
    action: ValidationAction = ValidationAction.ACCEPT,
) -> ClinicianValidationEvidence:
    return ClinicianValidationEvidence(
        validation_id=f"validation:{target_type}:{target_id}",
        clinician_id=clinician_id,
        validated_at=NOW,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_snapshot_hash="before",
        after_snapshot_hash="after",
    )


def _validate(graph: EvidenceGraphSnapshot) -> None:
    validate_case_evidence_graph(graph, patient_id=PATIENT_ID, case_id=CASE_ID)


def test_explicit_patient_case_source_passes():
    _validate(EvidenceGraphSnapshot(sources=[_source()]))


def test_graph_without_patient_source_fails_closed():
    with pytest.raises(EvidenceGraphValidationError, match="requires at least one"):
        _validate(EvidenceGraphSnapshot())


def test_cross_patient_source_is_rejected():
    graph = EvidenceGraphSnapshot(
        sources=[_source(), _source(evidence_id="source:foreign", patient_id=999)]
    )
    with pytest.raises(EvidenceGraphValidationError, match="belongs to patient 999"):
        _validate(graph)


def test_missing_case_id_is_rejected():
    graph = EvidenceGraphSnapshot(sources=[_source(case_id=None)])
    with pytest.raises(EvidenceGraphValidationError, match="has case_id None"):
        _validate(graph)


def test_mixed_case_sources_are_rejected():
    graph = EvidenceGraphSnapshot(
        sources=[_source(), _source(evidence_id="source:other-case", case_id="case:other")]
    )
    with pytest.raises(EvidenceGraphValidationError, match="case:other"):
        _validate(graph)


def test_accepted_diagnosis_requires_matching_validation_node():
    graph = EvidenceGraphSnapshot(
        sources=[_source()],
        findings=[_finding()],
        diagnoses=[_diagnosis(state=ReviewState.ACCEPTED)],
    )
    with pytest.raises(EvidenceGraphValidationError, match="without a matching"):
        _validate(graph)


def test_accepted_diagnosis_with_exact_audit_node_passes():
    graph = EvidenceGraphSnapshot(
        sources=[_source()],
        findings=[_finding()],
        diagnoses=[_diagnosis(state=ReviewState.ACCEPTED)],
        validations=[_validation("diagnosis", "diagnosis:1")],
    )
    _validate(graph)


def test_accepted_diagnosis_rejects_wrong_clinician_or_rejected_audit():
    base = dict(
        sources=[_source()],
        findings=[_finding()],
        diagnoses=[_diagnosis(state=ReviewState.ACCEPTED)],
    )
    wrong_clinician = EvidenceGraphSnapshot(
        **base,
        validations=[_validation("diagnosis", "diagnosis:1", clinician_id="clinician:2")],
    )
    with pytest.raises(EvidenceGraphValidationError, match="without a matching"):
        _validate(wrong_clinician)

    rejected = EvidenceGraphSnapshot(
        **base,
        validations=[_validation("diagnosis", "diagnosis:1", action=ValidationAction.REJECT)],
    )
    with pytest.raises(EvidenceGraphValidationError, match="without a matching"):
        _validate(rejected)


def test_accepted_problem_and_objective_each_require_real_audit_node():
    problem_graph = EvidenceGraphSnapshot(
        sources=[_source()],
        findings=[_finding()],
        diagnoses=[_diagnosis()],
        problems=[_problem(state=ReviewState.ACCEPTED)],
    )
    with pytest.raises(EvidenceGraphValidationError, match="problem problem:1"):
        _validate(problem_graph)

    objective_graph = EvidenceGraphSnapshot(
        sources=[_source()],
        findings=[_finding()],
        diagnoses=[_diagnosis()],
        problems=[_problem()],
        objectives=[_objective(state=ReviewState.ACCEPTED)],
    )
    with pytest.raises(EvidenceGraphValidationError, match="objective objective:1"):
        _validate(objective_graph)


def test_selected_treatment_option_requires_real_audit_node():
    graph = EvidenceGraphSnapshot(
        sources=[_source()],
        findings=[_finding()],
        diagnoses=[_diagnosis()],
        problems=[_problem()],
        objectives=[_objective()],
        treatment_options=[_option(selected=True)],
    )
    with pytest.raises(EvidenceGraphValidationError, match="treatment_option option:1"):
        _validate(graph)


def test_selected_treatment_option_with_matching_audit_passes():
    graph = EvidenceGraphSnapshot(
        sources=[_source()],
        findings=[_finding()],
        diagnoses=[_diagnosis()],
        problems=[_problem()],
        objectives=[_objective()],
        treatment_options=[_option(selected=True)],
        validations=[_validation("treatment_option", "option:1")],
    )
    _validate(graph)
