"""R14 fail-closed validation for final clinical strategy state.

The validator re-runs R13 first, preserves exact R13->R12->R11 lineage, and
never promotes an evaluable R13 option into a final clinical state. A final R14
state exists only after a traceable clinician validation action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence, Set, Tuple

from backend.schemas.cephalo_evidence import ClinicianValidationEvidence, ValidationAction
from backend.schemas.cephalo_r13_therapeutic_options import R13TreatmentOptionStatus
from backend.schemas.cephalo_r14_final_validation import (
    R14FinalClinicalStatus,
    R14FinalClinicalStrategyEvidence,
)
from backend.services.cephalo_diagnostic_rule_registry import (
    DiagnosticRuleRegistry,
    registry as default_diagnostic_rule_registry,
)
from backend.services.cephalo_evidence_graph import EvidenceGraphValidationError
from backend.services.cephalo_norm_registry import NormRegistry, registry as default_norm_registry
from backend.services.cephalo_r13_therapeutic_safety import (
    R13TherapeuticSnapshot,
    validate_r13_therapeutic_options,
)
from backend.services.cephalo_therapeutic_rule_registry import (
    TherapeuticRuleRegistry,
    registry as default_therapeutic_rule_registry,
)


SourceKey = Tuple[str, str]


@dataclass(frozen=True)
class R14FinalClinicalSnapshot:
    r13_snapshot: R13TherapeuticSnapshot
    strategies: Sequence[R14FinalClinicalStrategyEvidence] = ()
    final_validations: Sequence[ClinicianValidationEvidence] = ()


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
        f"{context} {field} must exactly match R13 provenance ({'; '.join(details)})"
    )


def _require_exact_sources(actual, expected: Set[SourceKey], *, context: str) -> None:
    actual_set = {(item.source_id, item.source_version) for item in actual}
    if actual_set == expected:
        return
    missing = sorted(expected - actual_set)
    extra = sorted(actual_set - expected)
    details = []
    if missing:
        details.append(
            "missing=" + ",".join(f"{source_id}@{version}" for source_id, version in missing)
        )
    if extra:
        details.append(
            "extra=" + ",".join(f"{source_id}@{version}" for source_id, version in extra)
        )
    raise EvidenceGraphValidationError(
        f"{context} source_refs must exactly match R13 provenance ({'; '.join(details)})"
    )


def _r13_global_ids(snapshot: R13TherapeuticSnapshot) -> Set[str]:
    r12 = snapshot.r12_snapshot
    graph = r12.diagnostic_graph
    return {
        *(item.evidence_id for item in graph.sources),
        *(item.evidence_id for item in graph.landmarks),
        *(item.construction_id for item in graph.constructions),
        *(item.measurement_id for item in graph.measurements),
        *(item.evaluation_id for item in graph.normative_evaluations),
        *(item.finding_id for item in graph.findings),
        *(item.diagnosis_id for item in graph.diagnoses),
        *(item.validation_id for item in graph.validations),
        *(item.problem_id for item in r12.problems),
        *(item.objective_id for item in r12.objectives),
        *(item.criterion_id for item in snapshot.criteria),
        *(item.option_id for item in snapshot.options),
        *(item.validation_id for item in snapshot.option_validations),
    }


def _is_timezone_aware(value) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def validate_r14_final_clinical_validation(
    snapshot: R14FinalClinicalSnapshot,
    *,
    norm_registry: NormRegistry = default_norm_registry,
    diagnostic_rule_registry: DiagnosticRuleRegistry = default_diagnostic_rule_registry,
    therapeutic_rule_registry: TherapeuticRuleRegistry = default_therapeutic_rule_registry,
) -> None:
    """Validate final clinical strategy state without autonomous treatment choice."""

    validate_r13_therapeutic_options(
        snapshot.r13_snapshot,
        norm_registry=norm_registry,
        diagnostic_rule_registry=diagnostic_rule_registry,
        therapeutic_rule_registry=therapeutic_rule_registry,
    )

    r13 = snapshot.r13_snapshot
    global_ids = _r13_global_ids(r13)
    criteria = {item.criterion_id: item for item in r13.criteria}
    options = {item.option_id: item for item in r13.options}

    strategy_ids: Set[str] = set()
    for strategy in snapshot.strategies:
        if strategy.strategy_id in global_ids or strategy.strategy_id in strategy_ids:
            raise EvidenceGraphValidationError(
                f"R14 strategy id must be globally unique: {strategy.strategy_id}"
            )
        strategy_ids.add(strategy.strategy_id)

    validation_index: Dict[str, ClinicianValidationEvidence] = {}
    for validation in snapshot.final_validations:
        if (
            validation.validation_id in global_ids
            or validation.validation_id in strategy_ids
            or validation.validation_id in validation_index
        ):
            raise EvidenceGraphValidationError(
                f"R14 final validation id must be globally unique: {validation.validation_id}"
            )
        if not _is_timezone_aware(validation.validated_at):
            raise EvidenceGraphValidationError(
                f"R14 final validation {validation.validation_id} timestamp must be timezone-aware"
            )
        validation_index[validation.validation_id] = validation

    referenced_validation_ids: Set[str] = set()
    for strategy in snapshot.strategies:
        missing_options = sorted(set(strategy.option_refs) - set(options))
        if missing_options:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} references missing R13 option(s): "
                + ", ".join(missing_options)
            )
        selected_options = [options[item] for item in strategy.option_refs]

        expected_option_validations: Set[str] = set()
        expected_criteria: Set[str] = set()
        expected_sources: Set[SourceKey] = set()
        expected_objectives: Set[str] = set()
        expected_problems: Set[str] = set()
        expected_diagnoses: Set[str] = set()
        expected_findings: Set[str] = set()
        expected_evidence: Set[str] = set(strategy.option_refs)
        expected_missing: Set[str] = set()
        expected_contradictions: Set[str] = set()
        expected_blockers: Set[str] = set()

        for option in selected_options:
            if option.decision_validation_ref is not None:
                expected_option_validations.add(option.decision_validation_ref)
            expected_criteria.update(option.indication_refs)
            expected_criteria.update(option.contraindication_refs)
            expected_sources.update(
                (item.source_id, item.source_version) for item in option.source_refs
            )
            expected_objectives.update(option.objective_refs)
            expected_problems.update(option.problem_refs)
            expected_diagnoses.update(option.diagnosis_refs)
            expected_findings.update(option.finding_refs)
            expected_evidence.update(option.evidence_refs)
            expected_missing.update(option.missing_data_refs)
            expected_contradictions.update(option.contradictions)

            if option.status == R13TreatmentOptionStatus.EVALUABLE:
                expected_blockers.add(f"r13:{option.option_id}:clinician_selection_required")
            elif option.status == R13TreatmentOptionStatus.CLINICIAN_REJECTED:
                expected_blockers.add(f"r13:{option.option_id}:clinician_rejected")
            elif option.status == R13TreatmentOptionStatus.BLOCKED:
                expected_blockers.update(
                    f"r13:{option.option_id}:{gate}" for gate in option.blocking_gates
                )

        unresolved_criteria = sorted(expected_criteria - set(criteria))
        if unresolved_criteria:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} references missing R13 criterion(s): "
                + ", ".join(unresolved_criteria)
            )
        for criterion_id in expected_criteria:
            criterion = criteria[criterion_id]
            expected_sources.update(
                (item.source_id, item.source_version) for item in criterion.source_refs
            )

        expected_blockers.update(f"missing:{item}" for item in expected_missing)
        expected_blockers.update(f"contradiction:{item}" for item in expected_contradictions)

        _require_exact_refs(
            strategy.option_validation_refs,
            expected_option_validations,
            context=f"R14 strategy {strategy.strategy_id}",
            field="option_validation_refs",
        )
        _require_exact_refs(
            strategy.criterion_refs,
            expected_criteria,
            context=f"R14 strategy {strategy.strategy_id}",
            field="criterion_refs",
        )
        _require_exact_sources(
            strategy.source_refs,
            expected_sources,
            context=f"R14 strategy {strategy.strategy_id}",
        )
        _require_exact_refs(
            strategy.objective_refs,
            expected_objectives,
            context=f"R14 strategy {strategy.strategy_id}",
            field="objective_refs",
        )
        _require_exact_refs(
            strategy.problem_refs,
            expected_problems,
            context=f"R14 strategy {strategy.strategy_id}",
            field="problem_refs",
        )
        _require_exact_refs(
            strategy.diagnosis_refs,
            expected_diagnoses,
            context=f"R14 strategy {strategy.strategy_id}",
            field="diagnosis_refs",
        )
        _require_exact_refs(
            strategy.finding_refs,
            expected_findings,
            context=f"R14 strategy {strategy.strategy_id}",
            field="finding_refs",
        )
        _require_exact_refs(
            strategy.evidence_refs,
            expected_evidence,
            context=f"R14 strategy {strategy.strategy_id}",
            field="evidence_refs",
        )
        _require_exact_refs(
            strategy.missing_data_refs,
            expected_missing,
            context=f"R14 strategy {strategy.strategy_id}",
            field="missing_data_refs",
        )
        _require_exact_refs(
            strategy.contradictions,
            expected_contradictions,
            context=f"R14 strategy {strategy.strategy_id}",
            field="contradictions",
        )
        _require_exact_refs(
            strategy.blocking_gates,
            expected_blockers,
            context=f"R14 strategy {strategy.strategy_id}",
            field="blocking_gates",
        )

        if expected_blockers:
            if strategy.status != R14FinalClinicalStatus.BLOCKED:
                raise EvidenceGraphValidationError(
                    f"R14 strategy {strategy.strategy_id} with unresolved gates must remain BLOCKED"
                )
            continue

        if strategy.status == R14FinalClinicalStatus.BLOCKED:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} cannot remain BLOCKED without a blocking gate"
            )
        if strategy.status == R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION:
            continue

        assert strategy.final_validation_ref is not None
        validation = validation_index.get(strategy.final_validation_ref)
        if validation is None:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} final_validation_ref does not resolve"
            )
        referenced_validation_ids.add(validation.validation_id)
        if validation.target_type != "final_clinical_strategy" or validation.target_id != strategy.strategy_id:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} final validation must target that strategy"
            )
        if strategy.status == R14FinalClinicalStatus.CLINICIAN_VALIDATED:
            if validation.action not in {ValidationAction.ACCEPT, ValidationAction.EDIT}:
                raise EvidenceGraphValidationError(
                    f"R14 validated strategy {strategy.strategy_id} requires ACCEPT/EDIT validation"
                )
        elif strategy.status == R14FinalClinicalStatus.CLINICIAN_REJECTED:
            if validation.action != ValidationAction.REJECT:
                raise EvidenceGraphValidationError(
                    f"R14 rejected strategy {strategy.strategy_id} requires REJECT validation"
                )
        else:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} has unsupported final status {strategy.status.value}"
            )
        if validation.clinician_id != strategy.clinician_id:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} clinician differs from final validation"
            )
        if validation.validated_at != strategy.clinician_validated_at:
            raise EvidenceGraphValidationError(
                f"R14 strategy {strategy.strategy_id} timestamp differs from final validation"
            )

    orphan_validations = sorted(set(validation_index) - referenced_validation_ids)
    if orphan_validations:
        raise EvidenceGraphValidationError(
            "R14 final validations must be referenced by a final clinician decision: "
            + ", ".join(orphan_validations)
        )
