"""R13 fail-closed validation for sourced therapeutic options.

R13 consumes a certified R12 snapshot, evaluates only explicitly registered
therapeutic criteria/options, preserves exact upstream lineage, and never builds
a final plan. Option selection/rejection is a clinician action with a dedicated
audit record; the validator never selects an option by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence, Set, Tuple

from backend.schemas.cephalo_evidence import (
    ClinicianValidationEvidence,
    ReviewState,
    ValidationAction,
)
from backend.schemas.cephalo_r13_therapeutic_options import (
    R13TreatmentOptionEvidence,
    R13TreatmentOptionStatus,
    R13TherapeuticCriterionEvidence,
    TherapeuticCriterionState,
    TherapeuticCriterionType,
)
from backend.services.cephalo_diagnostic_rule_registry import (
    DiagnosticRuleRegistry,
    registry as default_diagnostic_rule_registry,
)
from backend.services.cephalo_evidence_graph import EvidenceGraphValidationError
from backend.services.cephalo_norm_registry import (
    NormRegistry,
    registry as default_norm_registry,
)
from backend.services.cephalo_r12_problem_objectives_safety import (
    R12ProblemObjectiveSnapshot,
    validate_r12_problem_objectives,
)
from backend.services.cephalo_therapeutic_rule_registry import (
    RuleKey,
    SourceKey,
    TherapeuticRuleRegistry,
    registry as default_therapeutic_rule_registry,
)


@dataclass(frozen=True)
class R13TherapeuticSnapshot:
    r12_snapshot: R12ProblemObjectiveSnapshot
    criteria: Sequence[R13TherapeuticCriterionEvidence] = ()
    options: Sequence[R13TreatmentOptionEvidence] = ()
    option_validations: Sequence[ClinicianValidationEvidence] = ()


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


def _source_keys(items) -> Set[SourceKey]:
    return {(item.source_id, item.source_version) for item in items}


def _rule_keys(items: Iterable[R13TherapeuticCriterionEvidence]) -> Set[RuleKey]:
    return {(item.rule_id, item.rule_version) for item in items}


def _require_context_keys(context: Dict[str, str], keys: Tuple[str, ...], *, label: str) -> None:
    missing = sorted(set(keys) - set(context))
    if missing:
        raise EvidenceGraphValidationError(
            f"{label} is missing required context key(s): {', '.join(missing)}"
        )


def _planning_ids(snapshot: R12ProblemObjectiveSnapshot) -> Set[str]:
    graph = snapshot.diagnostic_graph
    result = {
        *(item.evidence_id for item in graph.sources),
        *(item.evidence_id for item in graph.landmarks),
        *(item.construction_id for item in graph.constructions),
        *(item.measurement_id for item in graph.measurements),
        *(item.evaluation_id for item in graph.normative_evaluations),
        *(item.finding_id for item in graph.findings),
        *(item.diagnosis_id for item in graph.diagnoses),
        *(item.problem_id for item in snapshot.problems),
        *(item.objective_id for item in snapshot.objectives),
    }
    return result


def _global_upstream_ids(snapshot: R12ProblemObjectiveSnapshot) -> Set[str]:
    graph = snapshot.diagnostic_graph
    result = _planning_ids(snapshot)
    result.update(item.validation_id for item in graph.validations)
    return result


def validate_r13_therapeutic_options(
    snapshot: R13TherapeuticSnapshot,
    *,
    norm_registry: NormRegistry = default_norm_registry,
    diagnostic_rule_registry: DiagnosticRuleRegistry = default_diagnostic_rule_registry,
    therapeutic_rule_registry: TherapeuticRuleRegistry = default_therapeutic_rule_registry,
) -> None:
    """Validate R13 without prescribing, sequencing, or constructing a final plan."""

    validate_r12_problem_objectives(
        snapshot.r12_snapshot,
        norm_registry=norm_registry,
        rule_registry=diagnostic_rule_registry,
    )

    r12 = snapshot.r12_snapshot
    planning_ids = _planning_ids(r12)
    global_ids = _global_upstream_ids(r12)
    problems = {item.problem_id: item for item in r12.problems}
    objectives = {item.objective_id: item for item in r12.objectives}

    criteria: Dict[str, R13TherapeuticCriterionEvidence] = {}
    for criterion in snapshot.criteria:
        if criterion.criterion_id in global_ids or criterion.criterion_id in criteria:
            raise EvidenceGraphValidationError(
                f"R13 criterion id must be globally unique: {criterion.criterion_id}"
            )
        criteria[criterion.criterion_id] = criterion

        rule = therapeutic_rule_registry.get_criterion_rule(
            criterion.rule_id, criterion.rule_version
        )
        if rule is None:
            raise EvidenceGraphValidationError(
                f"R13 criterion {criterion.criterion_id} uses unregistered therapeutic rule "
                f"{criterion.rule_id}@{criterion.rule_version}"
            )
        if criterion.criterion_type != rule.criterion_type:
            raise EvidenceGraphValidationError(
                f"R13 criterion {criterion.criterion_id} type does not match registry rule"
            )
        if _source_keys(criterion.source_refs) != set(rule.source_bindings):
            raise EvidenceGraphValidationError(
                f"R13 criterion {criterion.criterion_id} source_refs must exactly match registered rule sources"
            )
        _require_context_keys(
            criterion.context,
            rule.required_context_keys,
            label=f"R13 criterion {criterion.criterion_id}",
        )
        _require_refs(
            criterion.required_evidence_refs,
            planning_ids,
            context=f"R13 criterion {criterion.criterion_id} required_evidence_refs",
        )
        _require_refs(
            criterion.missing_data_refs,
            set(criterion.required_evidence_refs),
            context=f"R13 criterion {criterion.criterion_id} missing_data_refs",
        )

    option_validation_index: Dict[str, ClinicianValidationEvidence] = {}
    for validation in snapshot.option_validations:
        if validation.validation_id in global_ids or validation.validation_id in option_validation_index:
            raise EvidenceGraphValidationError(
                f"R13 option validation id must be globally unique: {validation.validation_id}"
            )
        option_validation_index[validation.validation_id] = validation

    options: Dict[str, R13TreatmentOptionEvidence] = {}
    referenced_validation_ids: Set[str] = set()
    for option in snapshot.options:
        if option.option_id in global_ids or option.option_id in criteria or option.option_id in options:
            raise EvidenceGraphValidationError(
                f"R13 option id must be globally unique: {option.option_id}"
            )
        options[option.option_id] = option

        rule = therapeutic_rule_registry.get_option_rule(option.rule_id, option.rule_version)
        if rule is None:
            raise EvidenceGraphValidationError(
                f"R13 option {option.option_id} uses unregistered therapeutic option rule "
                f"{option.rule_id}@{option.rule_version}"
            )
        if option.label != rule.label:
            raise EvidenceGraphValidationError(
                f"R13 option {option.option_id} label must exactly match registered option rule"
            )
        if _source_keys(option.source_refs) != set(rule.source_bindings):
            raise EvidenceGraphValidationError(
                f"R13 option {option.option_id} source_refs must exactly match registered rule sources"
            )
        _require_context_keys(
            option.context,
            rule.required_context_keys,
            label=f"R13 option {option.option_id}",
        )
        _require_refs(
            option.objective_refs,
            set(objectives),
            context=f"R13 option {option.option_id} objective_refs",
        )

        selected_objectives = [objectives[item] for item in option.objective_refs]
        unvalidated_objectives = sorted(
            item.objective_id
            for item in selected_objectives
            if item.state not in {ReviewState.ACCEPTED, ReviewState.EDITED}
        )
        if unvalidated_objectives:
            raise EvidenceGraphValidationError(
                f"R13 option {option.option_id} cannot derive from unvalidated objective: "
                + ", ".join(unvalidated_objectives)
            )

        expected_problems: Set[str] = set()
        expected_diagnoses: Set[str] = set()
        expected_findings: Set[str] = set()
        expected_missing: Set[str] = set()
        expected_contradictions: Set[str] = set()
        expected_evidence: Set[str] = set(option.objective_refs)
        for objective in selected_objectives:
            expected_problems.update(objective.problem_refs)
            expected_diagnoses.update(objective.diagnosis_refs)
            expected_findings.update(objective.finding_refs)
            expected_missing.update(objective.missing_data_refs)
            expected_contradictions.update(objective.contradictions)
            expected_evidence.update(objective.evidence_refs)

        _require_exact_refs(
            option.problem_refs,
            expected_problems,
            context=f"R13 option {option.option_id}",
            field="problem_refs",
        )
        _require_exact_refs(
            option.diagnosis_refs,
            expected_diagnoses,
            context=f"R13 option {option.option_id}",
            field="diagnosis_refs",
        )
        _require_exact_refs(
            option.finding_refs,
            expected_findings,
            context=f"R13 option {option.option_id}",
            field="finding_refs",
        )
        _require_exact_refs(
            option.missing_data_refs,
            expected_missing,
            context=f"R13 option {option.option_id}",
            field="missing_data_refs",
        )
        _require_exact_refs(
            option.contradictions,
            expected_contradictions,
            context=f"R13 option {option.option_id}",
            field="contradictions",
        )
        _require_exact_refs(
            option.evidence_refs,
            expected_evidence,
            context=f"R13 option {option.option_id}",
            field="evidence_refs",
        )

        selected_indications = []
        selected_contraindications = []
        _require_refs(
            option.indication_refs,
            set(criteria),
            context=f"R13 option {option.option_id} indication_refs",
        )
        _require_refs(
            option.contraindication_refs,
            set(criteria),
            context=f"R13 option {option.option_id} contraindication_refs",
        )
        for criterion_id in option.indication_refs:
            criterion = criteria[criterion_id]
            if criterion.criterion_type != TherapeuticCriterionType.INDICATION:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} indication_refs contains non-indication {criterion_id}"
                )
            selected_indications.append(criterion)
        for criterion_id in option.contraindication_refs:
            criterion = criteria[criterion_id]
            if criterion.criterion_type != TherapeuticCriterionType.CONTRAINDICATION:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} contraindication_refs contains non-contraindication {criterion_id}"
                )
            selected_contraindications.append(criterion)

        if _rule_keys(selected_indications) != set(rule.indication_rule_bindings):
            raise EvidenceGraphValidationError(
                f"R13 option {option.option_id} indications must exactly match registered option rule bindings"
            )
        if _rule_keys(selected_contraindications) != set(rule.contraindication_rule_bindings):
            raise EvidenceGraphValidationError(
                f"R13 option {option.option_id} contraindications must exactly match registered option rule bindings"
            )

        for criterion in selected_indications + selected_contraindications:
            outside_lineage = sorted(set(criterion.required_evidence_refs) - expected_evidence)
            if outside_lineage:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} criterion {criterion.criterion_id} uses evidence outside objective lineage: "
                    + ", ".join(outside_lineage)
                )
            outside_missing = sorted(set(criterion.missing_data_refs) - expected_missing)
            if outside_missing:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} criterion {criterion.criterion_id} introduces missing data outside R12 lineage: "
                    + ", ".join(outside_missing)
                )
            outside_contradictions = sorted(
                set(criterion.contradictions) - expected_contradictions
            )
            if outside_contradictions:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} criterion {criterion.criterion_id} introduces contradiction outside R12 lineage: "
                    + ", ".join(outside_contradictions)
                )

        blockers: Set[str] = set()
        blockers.update(f"missing:{item}" for item in expected_missing)
        blockers.update(f"contradiction:{item}" for item in expected_contradictions)
        blockers.update(
            f"indication:{item.criterion_id}:{item.state.value}"
            for item in selected_indications
            if item.state != TherapeuticCriterionState.SATISFIED
        )
        blockers.update(
            f"contraindication:{item.criterion_id}:{item.state.value}"
            for item in selected_contraindications
            if item.state != TherapeuticCriterionState.NOT_SATISFIED
        )
        _require_exact_refs(
            option.blocking_gates,
            blockers,
            context=f"R13 option {option.option_id}",
            field="blocking_gates",
        )

        if blockers:
            if option.status != R13TreatmentOptionStatus.BLOCKED:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} with unsatisfied gates must remain BLOCKED"
                )
        elif option.status == R13TreatmentOptionStatus.BLOCKED:
            raise EvidenceGraphValidationError(
                f"R13 option {option.option_id} cannot remain BLOCKED without a blocking gate"
            )

        if option.status in {
            R13TreatmentOptionStatus.CLINICIAN_SELECTED,
            R13TreatmentOptionStatus.CLINICIAN_REJECTED,
        }:
            assert option.decision_validation_ref is not None
            validation = option_validation_index.get(option.decision_validation_ref)
            if validation is None:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} decision_validation_ref does not resolve"
                )
            referenced_validation_ids.add(validation.validation_id)
            if validation.target_type != "treatment_option" or validation.target_id != option.option_id:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} decision validation must target that option"
                )
            if option.status == R13TreatmentOptionStatus.CLINICIAN_SELECTED:
                if validation.action not in {ValidationAction.ACCEPT, ValidationAction.EDIT}:
                    raise EvidenceGraphValidationError(
                        f"R13 selected option {option.option_id} requires ACCEPT/EDIT validation"
                    )
            elif validation.action != ValidationAction.REJECT:
                raise EvidenceGraphValidationError(
                    f"R13 rejected option {option.option_id} requires REJECT validation"
                )
            if validation.clinician_id != option.clinician_id:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} clinician differs from decision validation"
                )
            if validation.validated_at != option.clinician_decided_at:
                raise EvidenceGraphValidationError(
                    f"R13 option {option.option_id} decision timestamp differs from validation"
                )

    orphan_validations = sorted(set(option_validation_index) - referenced_validation_ids)
    if orphan_validations:
        raise EvidenceGraphValidationError(
            "R13 option validations must be referenced by a clinician decision: "
            + ", ".join(orphan_validations)
        )
