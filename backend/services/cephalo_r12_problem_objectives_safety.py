"""R12 fail-closed validation for cephalometric problem lists and objectives.

R12 consumes the certified R11 diagnostic graph and adds only two layers:
problem-list items and clinical objectives. It does not activate any clinical
rule, normative threshold, indication, contraindication, treatment option, or
final treatment plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence, Set

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ReviewState,
    ValidationAction,
)
from backend.schemas.cephalo_r12_problem_objectives import (
    R12ObjectiveEvidence,
    R12ProblemListItem,
)
from backend.services.cephalo_diagnostic_rule_registry import (
    DiagnosticRuleRegistry,
    registry as default_diagnostic_rule_registry,
)
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
)
from backend.services.cephalo_norm_registry import (
    NormRegistry,
    registry as default_norm_registry,
)
from backend.services.cephalo_r11_diagnostic_safety import validate_r11_diagnostic_graph


@dataclass(frozen=True)
class R12ProblemObjectiveSnapshot:
    diagnostic_graph: EvidenceGraphSnapshot
    problems: Sequence[R12ProblemListItem] = ()
    objectives: Sequence[R12ObjectiveEvidence] = ()


def _require_exact_refs(
    actual: Iterable[str], expected: Set[str], *, context: str, field: str
) -> None:
    actual_set = set(actual)
    if actual_set == expected:
        return
    missing = sorted(expected - actual_set)
    extra = sorted(actual_set - expected)
    details = []
    if missing:
        details.append(f"missing={','.join(missing)}")
    if extra:
        details.append(f"extra={','.join(extra)}")
    raise EvidenceGraphValidationError(
        f"{context} {field} must exactly match upstream provenance ({'; '.join(details)})"
    )


def _require_refs(refs: Iterable[str], allowed: Set[str], *, context: str) -> None:
    missing = sorted(set(refs) - allowed)
    if missing:
        raise EvidenceGraphValidationError(
            f"{context} references missing object(s): {', '.join(missing)}"
        )


def _upstream_ids(graph: EvidenceGraphSnapshot) -> Set[str]:
    groups = (
        (graph.sources, "evidence_id"),
        (graph.landmarks, "evidence_id"),
        (graph.constructions, "construction_id"),
        (graph.measurements, "measurement_id"),
        (graph.normative_evaluations, "evaluation_id"),
        (graph.findings, "finding_id"),
        (graph.diagnoses, "diagnosis_id"),
        (graph.validations, "validation_id"),
    )
    result: Set[str] = set()
    for items, attr in groups:
        result.update(getattr(item, attr) for item in items)
    return result


def _latest_validation_actions_by_finding(graph: EvidenceGraphSnapshot) -> Dict[str, ValidationAction]:
    latest = {}
    for validation in graph.validations:
        if validation.target_type != "finding":
            continue
        current = latest.get(validation.target_id)
        if current is None or validation.validated_at > current.validated_at:
            latest[validation.target_id] = validation
        elif validation.validated_at == current.validated_at and validation.action != current.action:
            raise EvidenceGraphValidationError(
                f"R12 finding {validation.target_id} has conflicting validation actions at the same timestamp"
            )
    return {target_id: validation.action for target_id, validation in latest.items()}


def validate_r12_problem_objectives(
    snapshot: R12ProblemObjectiveSnapshot,
    *,
    norm_registry: NormRegistry = default_norm_registry,
    rule_registry: DiagnosticRuleRegistry = default_diagnostic_rule_registry,
) -> None:
    """Validate R12 lineage and stop strictly before treatment selection.

    The R11 graph remains authoritative for scientific evidence, findings and
    diagnostic hypotheses. R12 accepts only explicitly clinician-validated
    findings and clinician-validated diagnoses as sources for problem-list
    items, and only clinician-validated R12 problems as sources for objectives.
    Missing data and contradictions must be propagated exactly rather than being
    silently dropped.
    """

    graph = snapshot.diagnostic_graph

    if graph.problems or graph.objectives:
        raise EvidenceGraphValidationError(
            "R12 diagnostic_graph must stop at diagnoses; use the dedicated R12 problem/objective contracts"
        )
    if graph.treatment_options or graph.final_plans:
        raise EvidenceGraphValidationError(
            "R12 cannot contain treatment options, indications/contraindications, or final plans"
        )

    validate_r11_diagnostic_graph(
        graph,
        norm_registry=norm_registry,
        rule_registry=rule_registry,
    )

    findings = {item.finding_id: item for item in graph.findings}
    diagnoses = {item.diagnosis_id: item for item in graph.diagnoses}
    finding_ids = set(findings)
    diagnosis_ids = set(diagnoses)
    upstream_ids = _upstream_ids(graph)
    latest_finding_validation_actions = _latest_validation_actions_by_finding(graph)

    problems: Dict[str, R12ProblemListItem] = {}
    for problem in snapshot.problems:
        if problem.problem_id in upstream_ids or problem.problem_id in problems:
            raise EvidenceGraphValidationError(
                f"R12 problem id must be globally unique: {problem.problem_id}"
            )
        problems[problem.problem_id] = problem

        _require_refs(
            problem.diagnosis_refs,
            diagnosis_ids,
            context=f"R12 problem {problem.problem_id} diagnosis_refs",
        )

        selected_diagnoses = [diagnoses[item] for item in problem.diagnosis_refs]
        unvalidated = sorted(
            item.diagnosis_id
            for item in selected_diagnoses
            if item.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}
        )
        if unvalidated:
            raise EvidenceGraphValidationError(
                f"R12 problem {problem.problem_id} cannot derive from unvalidated diagnosis: "
                + ", ".join(unvalidated)
            )

        expected_findings: Set[str] = set()
        expected_missing: Set[str] = set()
        expected_contradictions: Set[str] = set()
        for diagnosis in selected_diagnoses:
            expected_findings.update(diagnosis.supporting_finding_refs)
            expected_findings.update(diagnosis.opposing_finding_refs)
            expected_missing.update(diagnosis.missing_data_refs)
            expected_contradictions.update(diagnosis.contradictions)

        _require_refs(
            expected_findings,
            finding_ids,
            context=f"R12 problem {problem.problem_id} finding lineage",
        )

        for finding_id in expected_findings:
            finding = findings[finding_id]
            if finding.availability_status != AvailabilityStatus.AVAILABLE:
                raise EvidenceGraphValidationError(
                    f"R12 problem {problem.problem_id} cannot derive from unavailable finding {finding_id}"
                )
            if latest_finding_validation_actions.get(finding_id) not in {
                ValidationAction.ACCEPT,
                ValidationAction.EDIT,
            }:
                raise EvidenceGraphValidationError(
                    f"R12 problem {problem.problem_id} cannot derive from unvalidated finding {finding_id}"
                )
            expected_missing.update(finding.missing_evidence_refs)
            expected_contradictions.update(finding.contradictions)

        _require_exact_refs(
            problem.finding_refs,
            expected_findings,
            context=f"R12 problem {problem.problem_id}",
            field="finding_refs",
        )
        _require_exact_refs(
            problem.missing_data_refs,
            expected_missing,
            context=f"R12 problem {problem.problem_id}",
            field="missing_data_refs",
        )
        _require_exact_refs(
            problem.contradictions,
            expected_contradictions,
            context=f"R12 problem {problem.problem_id}",
            field="contradictions",
        )

        expected_evidence = set(problem.diagnosis_refs) | expected_findings | expected_missing
        _require_exact_refs(
            problem.evidence_refs,
            expected_evidence,
            context=f"R12 problem {problem.problem_id}",
            field="evidence_refs",
        )

    problem_ids = set(problems)
    objectives: Dict[str, R12ObjectiveEvidence] = {}
    for objective in snapshot.objectives:
        if (
            objective.objective_id in upstream_ids
            or objective.objective_id in problem_ids
            or objective.objective_id in objectives
        ):
            raise EvidenceGraphValidationError(
                f"R12 objective id must be globally unique: {objective.objective_id}"
            )
        objectives[objective.objective_id] = objective

        _require_refs(
            objective.problem_refs,
            problem_ids,
            context=f"R12 objective {objective.objective_id} problem_refs",
        )
        selected_problems = [problems[item] for item in objective.problem_refs]
        unvalidated_problems = sorted(
            item.problem_id
            for item in selected_problems
            if item.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}
        )
        if unvalidated_problems:
            raise EvidenceGraphValidationError(
                f"R12 objective {objective.objective_id} cannot derive from unvalidated problem: "
                + ", ".join(unvalidated_problems)
            )

        expected_diagnoses: Set[str] = set()
        expected_findings = set()
        expected_missing = set()
        expected_contradictions = set()
        for problem in selected_problems:
            expected_diagnoses.update(problem.diagnosis_refs)
            expected_findings.update(problem.finding_refs)
            expected_missing.update(problem.missing_data_refs)
            expected_contradictions.update(problem.contradictions)

        _require_exact_refs(
            objective.diagnosis_refs,
            expected_diagnoses,
            context=f"R12 objective {objective.objective_id}",
            field="diagnosis_refs",
        )
        _require_exact_refs(
            objective.finding_refs,
            expected_findings,
            context=f"R12 objective {objective.objective_id}",
            field="finding_refs",
        )
        _require_exact_refs(
            objective.missing_data_refs,
            expected_missing,
            context=f"R12 objective {objective.objective_id}",
            field="missing_data_refs",
        )
        _require_exact_refs(
            objective.contradictions,
            expected_contradictions,
            context=f"R12 objective {objective.objective_id}",
            field="contradictions",
        )

        expected_evidence = (
            set(objective.problem_refs)
            | expected_diagnoses
            | expected_findings
            | expected_missing
        )
        _require_exact_refs(
            objective.evidence_refs,
            expected_evidence,
            context=f"R12 objective {objective.objective_id}",
            field="evidence_refs",
        )
