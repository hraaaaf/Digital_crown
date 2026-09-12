"""R12 problem-list/objective fail-closed golden tests.

The fixtures are synthetic and deliberately non-clinical. They verify lineage,
validation state, missing-data/contradiction propagation, and the R12 boundary
before treatment selection.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ClinicianValidationEvidence,
    DiagnosticHypothesisEvidence,
    FindingEvidence,
    ReviewState,
    SourceEvidence,
    TreatmentOptionEvidence,
    ValidationAction,
)
from backend.schemas.cephalo_r12_problem_objectives import (
    R12ObjectiveEvidence,
    R12ProblemListItem,
)
from backend.services.cephalo_diagnostic_rule_registry import (
    DiagnosticRuleDefinition,
    DiagnosticRuleRegistry,
    FindingRuleDefinition,
)
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
)
from backend.services.cephalo_r12_problem_objectives_safety import (
    R12ProblemObjectiveSnapshot,
    validate_r12_problem_objectives,
)


NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)
FINDING_RULE_ID = "R12_SYNTHETIC_FINDING_TEST_ONLY"
DIAGNOSIS_RULE_ID = "R12_SYNTHETIC_DIAGNOSIS_TEST_ONLY"


def _rule_registry() -> DiagnosticRuleRegistry:
    registry = DiagnosticRuleRegistry()
    registry.register_finding_rule(
        FindingRuleDefinition(
            rule_id=FINDING_RULE_ID,
            version="1",
            domain="synthetic",
            source_ids=("CRANIOM_PART2_2011",),
            description="Synthetic R12 lineage test finding rule only.",
            requires_active_normative_reference=False,
        )
    )
    registry.register_diagnostic_rule(
        DiagnosticRuleDefinition(
            rule_id=DIAGNOSIS_RULE_ID,
            version="1",
            domain="synthetic",
            source_ids=("CRANIOM_PART2_2011",),
            finding_rule_bindings=((FINDING_RULE_ID, "1"),),
            description="Synthetic R12 lineage test diagnostic rule only.",
        )
    )
    return registry


def _graph(
    *,
    diagnosis_state: ReviewState = ReviewState.ACCEPTED,
    include_missing: bool = False,
    include_contradiction: bool = False,
    validate_finding: bool = True,
) -> EvidenceGraphSnapshot:
    source = SourceEvidence(
        evidence_id="source:r12:available",
        patient_id=1,
        kind="synthetic_r12_test",
        source_record_id="record:r12",
        recorded_at=NOW,
        operator_id="clinician:1",
    )
    sources = [source]
    missing_refs = []
    if include_missing:
        missing_source = SourceEvidence(
            evidence_id="source:r12:missing",
            patient_id=1,
            kind="synthetic_missing_context",
            source_record_id="record:r12:missing",
            recorded_at=NOW,
            operator_id="clinician:1",
            availability_status=AvailabilityStatus.MISSING,
        )
        sources.append(missing_source)
        missing_refs = [missing_source.evidence_id]

    finding = FindingEvidence(
        finding_id="finding:r12:synthetic",
        domain="synthetic",
        rule_id=FINDING_RULE_ID,
        rule_version="1",
        supporting_evidence_refs=[source.evidence_id],
        missing_evidence_refs=missing_refs,
        contradictions=["synthetic finding contradiction"] if include_contradiction else [],
        statement="Synthetic R12 finding for contract tests only.",
    )

    clinician_id = None
    clinician_validated_at = None
    if diagnosis_state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
        clinician_id = "clinician:1"
        clinician_validated_at = NOW

    diagnosis = DiagnosticHypothesisEvidence(
        diagnosis_id="diagnosis:r12:synthetic",
        domain="synthetic",
        rule_id=DIAGNOSIS_RULE_ID,
        rule_version="1",
        supporting_finding_refs=[finding.finding_id],
        missing_data_refs=missing_refs,
        contradictions=["synthetic diagnosis contradiction"] if include_contradiction else [],
        statement="Synthetic R12 diagnosis for contract tests only.",
        state=diagnosis_state,
        clinician_id=clinician_id,
        clinician_validated_at=clinician_validated_at,
    )

    validations = []
    if validate_finding:
        validations = [
            ClinicianValidationEvidence(
                validation_id="validation:r12:finding",
                clinician_id="clinician:1",
                validated_at=NOW,
                action=ValidationAction.ACCEPT,
                target_type="finding",
                target_id=finding.finding_id,
                before_snapshot_hash="finding-before",
                after_snapshot_hash="finding-after",
            )
        ]

    return EvidenceGraphSnapshot(
        sources=sources,
        findings=[finding],
        diagnoses=[diagnosis],
        validations=validations,
    )


def _problem(
    graph: EvidenceGraphSnapshot,
    *,
    state: ReviewState = ReviewState.ACCEPTED,
) -> R12ProblemListItem:
    diagnosis = graph.diagnoses[0]
    finding = graph.findings[0]
    missing = sorted(set(diagnosis.missing_data_refs) | set(finding.missing_evidence_refs))
    contradictions = sorted(set(diagnosis.contradictions) | set(finding.contradictions))
    evidence_refs = [diagnosis.diagnosis_id, finding.finding_id, *missing]
    clinician_id = None
    clinician_validated_at = None
    if state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
        clinician_id = "clinician:1"
        clinician_validated_at = NOW
    return R12ProblemListItem(
        problem_id="problem:r12:synthetic",
        diagnosis_refs=[diagnosis.diagnosis_id],
        finding_refs=[finding.finding_id],
        evidence_refs=evidence_refs,
        missing_data_refs=missing,
        contradictions=contradictions,
        statement="Synthetic R12 problem-list item.",
        state=state,
        clinician_id=clinician_id,
        clinician_validated_at=clinician_validated_at,
    )


def _objective(
    problem: R12ProblemListItem,
    *,
    state: ReviewState = ReviewState.ACCEPTED,
) -> R12ObjectiveEvidence:
    evidence_refs = [
        problem.problem_id,
        *problem.diagnosis_refs,
        *problem.finding_refs,
        *problem.missing_data_refs,
    ]
    clinician_id = None
    clinician_validated_at = None
    if state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
        clinician_id = "clinician:1"
        clinician_validated_at = NOW
    return R12ObjectiveEvidence(
        objective_id="objective:r12:synthetic",
        problem_refs=[problem.problem_id],
        diagnosis_refs=problem.diagnosis_refs,
        finding_refs=problem.finding_refs,
        evidence_refs=evidence_refs,
        missing_data_refs=problem.missing_data_refs,
        contradictions=problem.contradictions,
        target="Synthetic non-treatment clinical target.",
        success_criterion="Synthetic observable criterion.",
        state=state,
        clinician_id=clinician_id,
        clinician_validated_at=clinician_validated_at,
    )


def _snapshot(
    graph: EvidenceGraphSnapshot,
    problem: R12ProblemListItem,
    objective: R12ObjectiveEvidence,
) -> R12ProblemObjectiveSnapshot:
    return R12ProblemObjectiveSnapshot(
        diagnostic_graph=graph,
        problems=[problem],
        objectives=[objective],
    )


def _replace_graph(graph: EvidenceGraphSnapshot, **changes) -> EvidenceGraphSnapshot:
    return EvidenceGraphSnapshot(**{**graph.__dict__, **changes})


def test_r12_positive_golden_preserves_exact_validated_lineage():
    graph = _graph()
    problem = _problem(graph)
    objective = _objective(problem)

    validate_r12_problem_objectives(
        _snapshot(graph, problem, objective),
        rule_registry=_rule_registry(),
    )


def test_r12_negative_golden_rejects_problem_from_unvalidated_hypothesis():
    graph = _graph(diagnosis_state=ReviewState.PROPOSED)
    problem = _problem(graph)
    objective = _objective(problem)

    with pytest.raises(EvidenceGraphValidationError, match="unvalidated diagnosis"):
        validate_r12_problem_objectives(
            _snapshot(graph, problem, objective),
            rule_registry=_rule_registry(),
        )


def test_r12_rejects_problem_from_unvalidated_finding():
    graph = _graph(validate_finding=False)
    problem = _problem(graph)
    objective = _objective(problem)

    with pytest.raises(EvidenceGraphValidationError, match="unvalidated finding"):
        validate_r12_problem_objectives(
            _snapshot(graph, problem, objective),
            rule_registry=_rule_registry(),
        )


def test_r12_missing_golden_requires_exact_propagation_to_problem_and_objective():
    graph = _graph(include_missing=True)
    problem = _problem(graph)
    objective = _objective(problem)

    validate_r12_problem_objectives(
        _snapshot(graph, problem, objective),
        rule_registry=_rule_registry(),
    )

    bad_problem = problem.model_copy(
        update={
            "missing_data_refs": [],
            "evidence_refs": [graph.diagnoses[0].diagnosis_id, graph.findings[0].finding_id],
        }
    )
    with pytest.raises(EvidenceGraphValidationError, match="missing_data_refs"):
        validate_r12_problem_objectives(
            _snapshot(graph, bad_problem, objective),
            rule_registry=_rule_registry(),
        )

    bad_objective = objective.model_copy(
        update={
            "missing_data_refs": [],
            "evidence_refs": [
                problem.problem_id,
                *problem.diagnosis_refs,
                *problem.finding_refs,
            ],
        }
    )
    with pytest.raises(EvidenceGraphValidationError, match="missing_data_refs"):
        validate_r12_problem_objectives(
            _snapshot(graph, problem, bad_objective),
            rule_registry=_rule_registry(),
        )


def test_r12_contradiction_golden_propagates_without_silent_drop():
    graph = _graph(include_contradiction=True)
    problem = _problem(graph)
    objective = _objective(problem)

    validate_r12_problem_objectives(
        _snapshot(graph, problem, objective),
        rule_registry=_rule_registry(),
    )

    bad_objective = objective.model_copy(update={"contradictions": []})
    with pytest.raises(EvidenceGraphValidationError, match="contradictions"):
        validate_r12_problem_objectives(
            _snapshot(graph, problem, bad_objective),
            rule_registry=_rule_registry(),
        )


def test_r12_objective_cannot_derive_from_unvalidated_problem():
    graph = _graph()
    problem = _problem(graph, state=ReviewState.PROPOSED)
    objective = _objective(problem)

    with pytest.raises(EvidenceGraphValidationError, match="unvalidated problem"):
        validate_r12_problem_objectives(
            _snapshot(graph, problem, objective),
            rule_registry=_rule_registry(),
        )


def test_r12_rejects_treatment_layer_leakage():
    graph = _graph()
    problem = _problem(graph)
    objective = _objective(problem)
    option = TreatmentOptionEvidence(
        option_id="option:r13:not_allowed_in_r12",
        objective_refs=[objective.objective_id],
        required_evidence_refs=[graph.sources[0].evidence_id],
    )
    graph_with_treatment = _replace_graph(graph, treatment_options=[option])

    with pytest.raises(EvidenceGraphValidationError, match="cannot contain treatment options"):
        validate_r12_problem_objectives(
            _snapshot(graph_with_treatment, problem, objective),
            rule_registry=_rule_registry(),
        )


def test_r12_contracts_forbid_treatment_specific_extra_fields():
    graph = _graph()
    problem = _problem(graph)

    with pytest.raises(ValidationError):
        R12ObjectiveEvidence(
            objective_id="objective:r12:unsafe-extra",
            problem_refs=[problem.problem_id],
            diagnosis_refs=problem.diagnosis_refs,
            finding_refs=problem.finding_refs,
            evidence_refs=[problem.problem_id, *problem.diagnosis_refs, *problem.finding_refs],
            target="Synthetic target.",
            success_criterion="Synthetic criterion.",
            indication_refs=["indication:not-r12"],
        )
