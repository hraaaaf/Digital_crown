"""R13 therapeutic-option fail-closed golden tests.

Fixtures are synthetic and deliberately non-clinical. They test provenance,
source/rule locking, missing-data and contradiction propagation,
contraindication blocking, and clinician-only option decisions.
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
    ValidationAction,
)
from backend.schemas.cephalo_r12_problem_objectives import (
    R12ObjectiveEvidence,
    R12ProblemListItem,
)
from backend.schemas.cephalo_r13_therapeutic_options import (
    R13_CONTRAINDICATION_CONTRACT_VERSION,
    R13_INDICATION_CONTRACT_VERSION,
    R13TreatmentOptionEvidence,
    R13TreatmentOptionStatus,
    R13TherapeuticCriterionEvidence,
    R13TherapeuticSourceRef,
    TherapeuticCriterionState,
    TherapeuticCriterionType,
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
from backend.services.cephalo_r12_problem_objectives_safety import R12ProblemObjectiveSnapshot
from backend.services.cephalo_r13_therapeutic_safety import (
    R13TherapeuticSnapshot,
    validate_r13_therapeutic_options,
)
from backend.services.cephalo_therapeutic_rule_registry import (
    TherapeuticCriterionRuleDefinition,
    TherapeuticOptionRuleDefinition,
    TherapeuticRuleRegistry,
    TherapeuticSourceDefinition,
    TherapeuticSourceType,
)


NOW = datetime(2026, 9, 12, 13, 0, tzinfo=timezone.utc)
FINDING_RULE_ID = "R13_SYNTHETIC_FINDING_TEST_ONLY"
DIAGNOSIS_RULE_ID = "R13_SYNTHETIC_DIAGNOSIS_TEST_ONLY"
INDICATION_RULE_ID = "R13_SYNTHETIC_INDICATION_TEST_ONLY"
CONTRAINDICATION_RULE_ID = "R13_SYNTHETIC_CONTRAINDICATION_TEST_ONLY"
OPTION_RULE_ID = "R13_SYNTHETIC_OPTION_TEST_ONLY"
THERAPEUTIC_SOURCE_ID = "R13_SYNTHETIC_SOURCE_TEST_ONLY"
THERAPEUTIC_SOURCE_VERSION = "1"
CONTEXT = {"population": "synthetic-test-only", "setting": "unit-test"}


def _diagnostic_registry() -> DiagnosticRuleRegistry:
    registry = DiagnosticRuleRegistry()
    registry.register_finding_rule(
        FindingRuleDefinition(
            rule_id=FINDING_RULE_ID,
            version="1",
            domain="synthetic",
            source_ids=("CRANIOM_PART2_2011",),
            description="Synthetic R13 lineage test finding rule only.",
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
            description="Synthetic R13 lineage test diagnostic rule only.",
        )
    )
    return registry


def _therapeutic_registry() -> TherapeuticRuleRegistry:
    registry = TherapeuticRuleRegistry()
    registry.register_source(
        TherapeuticSourceDefinition(
            source_id=THERAPEUTIC_SOURCE_ID,
            version=THERAPEUTIC_SOURCE_VERSION,
            source_type=TherapeuticSourceType.CLINICAL_GUIDELINE,
            citation="Synthetic R13 test source; not clinical guidance.",
            context=CONTEXT,
            reviewed_by="synthetic-reviewer",
            reviewed_at=NOW,
            review_reference="synthetic-review:test-only",
            approved_for_clinical_rules=True,
        )
    )
    source_binding = ((THERAPEUTIC_SOURCE_ID, THERAPEUTIC_SOURCE_VERSION),)
    registry.register_criterion_rule(
        TherapeuticCriterionRuleDefinition(
            rule_id=INDICATION_RULE_ID,
            version="1",
            criterion_type=TherapeuticCriterionType.INDICATION,
            source_bindings=source_binding,
            required_context_keys=("population", "setting"),
            description="Synthetic indication rule only.",
            reviewed_by="synthetic-reviewer",
            reviewed_at=NOW,
            review_reference="synthetic-review:test-only",
        )
    )
    registry.register_criterion_rule(
        TherapeuticCriterionRuleDefinition(
            rule_id=CONTRAINDICATION_RULE_ID,
            version="1",
            criterion_type=TherapeuticCriterionType.CONTRAINDICATION,
            source_bindings=source_binding,
            required_context_keys=("population", "setting"),
            description="Synthetic contraindication rule only.",
            reviewed_by="synthetic-reviewer",
            reviewed_at=NOW,
            review_reference="synthetic-review:test-only",
        )
    )
    registry.register_option_rule(
        TherapeuticOptionRuleDefinition(
            rule_id=OPTION_RULE_ID,
            version="1",
            source_bindings=source_binding,
            indication_rule_bindings=((INDICATION_RULE_ID, "1"),),
            contraindication_rule_bindings=((CONTRAINDICATION_RULE_ID, "1"),),
            required_context_keys=("population", "setting"),
            label="Synthetic test option",
            description="Synthetic treatment option rule only; no clinical meaning.",
            reviewed_by="synthetic-reviewer",
            reviewed_at=NOW,
            review_reference="synthetic-review:test-only",
        )
    )
    return registry


def _graph(
    *,
    include_missing: bool = False,
    include_contradiction: bool = False,
    validate_finding: bool = True,
) -> EvidenceGraphSnapshot:
    source = SourceEvidence(
        evidence_id="source:r13:available",
        patient_id=1,
        kind="synthetic_r13_test",
        source_record_id="record:r13",
        recorded_at=NOW,
        operator_id="clinician:1",
    )
    sources = [source]
    missing_refs = []
    if include_missing:
        missing_source = SourceEvidence(
            evidence_id="source:r13:missing",
            patient_id=1,
            kind="synthetic_missing_context",
            source_record_id="record:r13:missing",
            recorded_at=NOW,
            operator_id="clinician:1",
            availability_status=AvailabilityStatus.MISSING,
        )
        sources.append(missing_source)
        missing_refs = [missing_source.evidence_id]

    finding = FindingEvidence(
        finding_id="finding:r13:synthetic",
        domain="synthetic",
        rule_id=FINDING_RULE_ID,
        rule_version="1",
        supporting_evidence_refs=[source.evidence_id],
        missing_evidence_refs=missing_refs,
        contradictions=["synthetic upstream contradiction"] if include_contradiction else [],
        statement="Synthetic R13 finding for contract tests only.",
    )
    diagnosis = DiagnosticHypothesisEvidence(
        diagnosis_id="diagnosis:r13:synthetic",
        domain="synthetic",
        rule_id=DIAGNOSIS_RULE_ID,
        rule_version="1",
        supporting_finding_refs=[finding.finding_id],
        missing_data_refs=missing_refs,
        contradictions=["synthetic upstream contradiction"] if include_contradiction else [],
        statement="Synthetic R13 diagnosis for contract tests only.",
        state=ReviewState.ACCEPTED,
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
    )
    validations = []
    if validate_finding:
        validations.append(
            ClinicianValidationEvidence(
                validation_id="validation:r13:finding",
                clinician_id="clinician:1",
                validated_at=NOW,
                action=ValidationAction.ACCEPT,
                target_type="finding",
                target_id=finding.finding_id,
                before_snapshot_hash="finding-before",
                after_snapshot_hash="finding-after",
            )
        )
    return EvidenceGraphSnapshot(
        sources=sources,
        findings=[finding],
        diagnoses=[diagnosis],
        validations=validations,
    )


def _r12(
    *,
    include_missing: bool = False,
    include_contradiction: bool = False,
    objective_state: ReviewState = ReviewState.ACCEPTED,
    validate_finding: bool = True,
) -> R12ProblemObjectiveSnapshot:
    graph = _graph(
        include_missing=include_missing,
        include_contradiction=include_contradiction,
        validate_finding=validate_finding,
    )
    diagnosis = graph.diagnoses[0]
    finding = graph.findings[0]
    missing = sorted(set(diagnosis.missing_data_refs) | set(finding.missing_evidence_refs))
    contradictions = sorted(set(diagnosis.contradictions) | set(finding.contradictions))
    problem = R12ProblemListItem(
        problem_id="problem:r13:synthetic",
        diagnosis_refs=[diagnosis.diagnosis_id],
        finding_refs=[finding.finding_id],
        evidence_refs=[diagnosis.diagnosis_id, finding.finding_id, *missing],
        missing_data_refs=missing,
        contradictions=contradictions,
        statement="Synthetic R13 upstream problem.",
        state=ReviewState.ACCEPTED,
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
    )
    objective_clinician = "clinician:1" if objective_state in {ReviewState.ACCEPTED, ReviewState.EDITED} else None
    objective_validated_at = NOW if objective_clinician else None
    objective = R12ObjectiveEvidence(
        objective_id="objective:r13:synthetic",
        problem_refs=[problem.problem_id],
        diagnosis_refs=problem.diagnosis_refs,
        finding_refs=problem.finding_refs,
        evidence_refs=[
            problem.problem_id,
            *problem.diagnosis_refs,
            *problem.finding_refs,
            *problem.missing_data_refs,
        ],
        missing_data_refs=problem.missing_data_refs,
        contradictions=problem.contradictions,
        target="Synthetic target.",
        success_criterion="Synthetic observable criterion.",
        state=objective_state,
        clinician_id=objective_clinician,
        clinician_validated_at=objective_validated_at,
    )
    return R12ProblemObjectiveSnapshot(
        diagnostic_graph=graph,
        problems=[problem],
        objectives=[objective],
    )


def _source_refs():
    return [
        R13TherapeuticSourceRef(
            source_id=THERAPEUTIC_SOURCE_ID,
            source_version=THERAPEUTIC_SOURCE_VERSION,
        )
    ]


def _criteria(
    r12: R12ProblemObjectiveSnapshot,
    *,
    contraindication_satisfied: bool = False,
    block_indication_for_missing: bool = False,
):
    objective = r12.objectives[0]
    required = [objective.objective_id]
    indication_missing = []
    if block_indication_for_missing:
        indication_missing = list(objective.missing_data_refs)
        required.extend(indication_missing)
    indication = R13TherapeuticCriterionEvidence(
        criterion_id="criterion:r13:indication",
        contract_version=R13_INDICATION_CONTRACT_VERSION,
        criterion_type=TherapeuticCriterionType.INDICATION,
        rule_id=INDICATION_RULE_ID,
        rule_version="1",
        source_refs=_source_refs(),
        context=CONTEXT,
        required_evidence_refs=required,
        missing_data_refs=indication_missing,
        statement="Synthetic indication evaluation.",
        state=(
            TherapeuticCriterionState.BLOCKED
            if indication_missing
            else TherapeuticCriterionState.SATISFIED
        ),
    )
    contraindication = R13TherapeuticCriterionEvidence(
        criterion_id="criterion:r13:contraindication",
        contract_version=R13_CONTRAINDICATION_CONTRACT_VERSION,
        criterion_type=TherapeuticCriterionType.CONTRAINDICATION,
        rule_id=CONTRAINDICATION_RULE_ID,
        rule_version="1",
        source_refs=_source_refs(),
        context=CONTEXT,
        required_evidence_refs=[objective.objective_id],
        statement="Synthetic contraindication evaluation.",
        state=(
            TherapeuticCriterionState.SATISFIED
            if contraindication_satisfied
            else TherapeuticCriterionState.NOT_SATISFIED
        ),
    )
    return [indication, contraindication]


def _option(
    r12: R12ProblemObjectiveSnapshot,
    criteria,
    *,
    status: R13TreatmentOptionStatus = R13TreatmentOptionStatus.EVALUABLE,
    blocking_gates=None,
    clinician_id=None,
    clinician_decided_at=None,
    decision_validation_ref=None,
) -> R13TreatmentOptionEvidence:
    objective = r12.objectives[0]
    problem_refs = list(objective.problem_refs)
    diagnosis_refs = list(objective.diagnosis_refs)
    finding_refs = list(objective.finding_refs)
    evidence_refs = [objective.objective_id, *objective.evidence_refs]
    return R13TreatmentOptionEvidence(
        option_id="option:r13:synthetic",
        rule_id=OPTION_RULE_ID,
        rule_version="1",
        source_refs=_source_refs(),
        context=CONTEXT,
        objective_refs=[objective.objective_id],
        problem_refs=problem_refs,
        diagnosis_refs=diagnosis_refs,
        finding_refs=finding_refs,
        evidence_refs=evidence_refs,
        missing_data_refs=objective.missing_data_refs,
        contradictions=objective.contradictions,
        indication_refs=[criteria[0].criterion_id],
        contraindication_refs=[criteria[1].criterion_id],
        blocking_gates=list(blocking_gates or []),
        label="Synthetic test option",
        status=status,
        clinician_id=clinician_id,
        clinician_decided_at=clinician_decided_at,
        decision_validation_ref=decision_validation_ref,
    )


def _validate(snapshot: R13TherapeuticSnapshot, therapeutic_registry=None):
    validate_r13_therapeutic_options(
        snapshot,
        diagnostic_rule_registry=_diagnostic_registry(),
        therapeutic_rule_registry=therapeutic_registry or _therapeutic_registry(),
    )


def test_r13_positive_golden_keeps_exact_r12_lineage_and_does_not_auto_select():
    r12 = _r12()
    criteria = _criteria(r12)
    option = _option(r12, criteria)
    snapshot = R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option])

    _validate(snapshot)

    assert option.status == R13TreatmentOptionStatus.EVALUABLE
    assert option.clinician_id is None
    assert option.decision_validation_ref is None


def test_r13_production_registry_is_fail_closed_and_empty():
    empty = TherapeuticRuleRegistry()
    r12 = _r12()
    criteria = _criteria(r12)
    option = _option(r12, criteria)

    with pytest.raises(EvidenceGraphValidationError, match="unregistered therapeutic rule"):
        _validate(
            R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option]),
            therapeutic_registry=empty,
        )


def test_r13_rejects_option_from_unvalidated_objective():
    r12 = _r12(objective_state=ReviewState.PROPOSED)
    criteria = _criteria(r12)
    option = _option(r12, criteria)

    with pytest.raises(EvidenceGraphValidationError, match="unvalidated objective"):
        _validate(R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option]))


def test_r13_reexecutes_r12_and_rejects_unvalidated_finding_upstream():
    r12 = _r12(validate_finding=False)
    criteria = _criteria(r12)
    option = _option(r12, criteria)

    with pytest.raises(EvidenceGraphValidationError, match="unvalidated finding"):
        _validate(R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option]))


def test_r13_missing_data_golden_is_propagated_and_blocks_evaluation():
    r12 = _r12(include_missing=True)
    criteria = _criteria(r12, block_indication_for_missing=True)
    missing_ref = r12.objectives[0].missing_data_refs[0]
    gates = [
        f"missing:{missing_ref}",
        f"indication:{criteria[0].criterion_id}:BLOCKED",
    ]
    option = _option(
        r12,
        criteria,
        status=R13TreatmentOptionStatus.BLOCKED,
        blocking_gates=gates,
    )

    _validate(R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option]))

    tampered = option.model_copy(update={"missing_data_refs": []})
    with pytest.raises(EvidenceGraphValidationError, match="missing_data_refs"):
        _validate(
            R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[tampered])
        )


def test_r13_contradiction_golden_remains_visible_and_blocks_option():
    r12 = _r12(include_contradiction=True)
    criteria = _criteria(r12)
    contradiction = r12.objectives[0].contradictions[0]
    option = _option(
        r12,
        criteria,
        status=R13TreatmentOptionStatus.BLOCKED,
        blocking_gates=[f"contradiction:{contradiction}"],
    )

    _validate(R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option]))

    tampered = option.model_copy(update={"contradictions": []})
    with pytest.raises(EvidenceGraphValidationError, match="contradictions"):
        _validate(
            R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[tampered])
        )


def test_r13_satisfied_contraindication_cannot_be_silently_neutralized():
    r12 = _r12()
    criteria = _criteria(r12, contraindication_satisfied=True)
    gate = f"contraindication:{criteria[1].criterion_id}:SATISFIED"
    option = _option(
        r12,
        criteria,
        status=R13TreatmentOptionStatus.BLOCKED,
        blocking_gates=[gate],
    )

    _validate(R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option]))

    tampered = option.model_copy(
        update={"status": R13TreatmentOptionStatus.EVALUABLE, "blocking_gates": []}
    )
    with pytest.raises(EvidenceGraphValidationError, match="blocking_gates"):
        _validate(
            R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[tampered])
        )


def test_r13_option_lineage_must_exactly_match_selected_objectives():
    r12 = _r12()
    criteria = _criteria(r12)
    option = _option(r12, criteria)
    tampered = option.model_copy(update={"finding_refs": ["finding:invented"]})

    with pytest.raises(EvidenceGraphValidationError, match="finding_refs"):
        _validate(
            R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[tampered])
        )


def test_r13_rule_source_version_and_context_are_not_implicit():
    r12 = _r12()
    criteria = _criteria(r12)
    bad_source = R13TherapeuticSourceRef(
        source_id=THERAPEUTIC_SOURCE_ID,
        source_version="wrong-version",
    )
    tampered_criterion = criteria[0].model_copy(update={"source_refs": [bad_source]})

    with pytest.raises(EvidenceGraphValidationError, match="source_refs"):
        _validate(
            R13TherapeuticSnapshot(
                r12_snapshot=r12,
                criteria=[tampered_criterion, criteria[1]],
                options=[_option(r12, criteria)],
            )
        )

    tampered_context = criteria[0].model_copy(update={"context": {"population": "synthetic"}})
    with pytest.raises(EvidenceGraphValidationError, match="required context"):
        _validate(
            R13TherapeuticSnapshot(
                r12_snapshot=r12,
                criteria=[tampered_context, criteria[1]],
                options=[_option(r12, criteria)],
            )
        )


def test_r13_clinician_selection_requires_matching_audit_record():
    r12 = _r12()
    criteria = _criteria(r12)
    validation = ClinicianValidationEvidence(
        validation_id="validation:r13:option-decision",
        clinician_id="clinician:1",
        validated_at=NOW,
        action=ValidationAction.ACCEPT,
        target_type="treatment_option",
        target_id="option:r13:synthetic",
        before_snapshot_hash="option-before",
        after_snapshot_hash="option-after",
    )
    option = _option(
        r12,
        criteria,
        status=R13TreatmentOptionStatus.CLINICIAN_SELECTED,
        clinician_id="clinician:1",
        clinician_decided_at=NOW,
        decision_validation_ref=validation.validation_id,
    )

    _validate(
        R13TherapeuticSnapshot(
            r12_snapshot=r12,
            criteria=criteria,
            options=[option],
            option_validations=[validation],
        )
    )

    wrong_validation = validation.model_copy(update={"action": ValidationAction.REJECT})
    with pytest.raises(EvidenceGraphValidationError, match="requires ACCEPT/EDIT"):
        _validate(
            R13TherapeuticSnapshot(
                r12_snapshot=r12,
                criteria=criteria,
                options=[option],
                option_validations=[wrong_validation],
            )
        )


def test_r13_contract_forbids_clinician_selected_without_audit_fields():
    r12 = _r12()
    criteria = _criteria(r12)
    objective = r12.objectives[0]

    with pytest.raises(ValidationError, match="complete audit fields"):
        R13TreatmentOptionEvidence(
            option_id="option:r13:unsafe-selection",
            rule_id=OPTION_RULE_ID,
            rule_version="1",
            source_refs=_source_refs(),
            context=CONTEXT,
            objective_refs=[objective.objective_id],
            problem_refs=objective.problem_refs,
            diagnosis_refs=objective.diagnosis_refs,
            finding_refs=objective.finding_refs,
            evidence_refs=[objective.objective_id, *objective.evidence_refs],
            indication_refs=[criteria[0].criterion_id],
            contraindication_refs=[criteria[1].criterion_id],
            label="Synthetic test option",
            status=R13TreatmentOptionStatus.CLINICIAN_SELECTED,
        )
