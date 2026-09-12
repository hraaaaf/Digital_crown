"""R14 final-clinical-validation goldens.

All fixtures are synthetic and non-clinical. R14 tests only provenance,
blocking, and human-validation invariants; they do not encode treatment rules.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas.cephalo_evidence import ClinicianValidationEvidence, ValidationAction
from backend.schemas.cephalo_r13_therapeutic_options import R13TreatmentOptionStatus
from backend.schemas.cephalo_r14_final_validation import (
    R14FinalClinicalStatus,
    R14FinalClinicalStrategyEvidence,
)
from backend.services.cephalo_evidence_graph import EvidenceGraphValidationError
from backend.services.cephalo_r13_therapeutic_safety import R13TherapeuticSnapshot
from backend.services.cephalo_r14_final_validation_safety import (
    R14FinalClinicalSnapshot,
    validate_r14_final_clinical_validation,
)
from backend.tests.test_cephalo_r13_therapeutic_safety import (
    NOW,
    _criteria,
    _diagnostic_registry,
    _option,
    _r12,
    _therapeutic_registry,
)


def _option_decision(option_id: str) -> ClinicianValidationEvidence:
    return ClinicianValidationEvidence(
        validation_id="validation:r13:option:selected",
        clinician_id="clinician:1",
        validated_at=NOW,
        action=ValidationAction.ACCEPT,
        target_type="treatment_option",
        target_id=option_id,
        before_snapshot_hash="r13-option-before",
        after_snapshot_hash="r13-option-after",
    )


def _selected_r13() -> R13TherapeuticSnapshot:
    r12 = _r12()
    criteria = _criteria(r12)
    option_id = "option:r13:synthetic"
    decision = _option_decision(option_id)
    option = _option(
        r12,
        criteria,
        status=R13TreatmentOptionStatus.CLINICIAN_SELECTED,
        clinician_id="clinician:1",
        clinician_decided_at=NOW,
        decision_validation_ref=decision.validation_id,
    )
    return R13TherapeuticSnapshot(
        r12_snapshot=r12,
        criteria=criteria,
        options=[option],
        option_validations=[decision],
    )


def _evaluable_r13() -> R13TherapeuticSnapshot:
    r12 = _r12()
    criteria = _criteria(r12)
    option = _option(r12, criteria, status=R13TreatmentOptionStatus.EVALUABLE)
    return R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option])


def _blocked_r13() -> R13TherapeuticSnapshot:
    r12 = _r12(include_missing=True)
    criteria = _criteria(r12, block_indication_for_missing=True)
    gates = [
        "missing:source:r13:missing",
        "indication:criterion:r13:indication:BLOCKED",
    ]
    option = _option(
        r12,
        criteria,
        status=R13TreatmentOptionStatus.BLOCKED,
        blocking_gates=gates,
    )
    return R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option])


def _contradictory_r13() -> R13TherapeuticSnapshot:
    r12 = _r12(include_contradiction=True)
    criteria = _criteria(r12)
    option = _option(
        r12,
        criteria,
        status=R13TreatmentOptionStatus.BLOCKED,
        blocking_gates=["contradiction:synthetic upstream contradiction"],
    )
    return R13TherapeuticSnapshot(r12_snapshot=r12, criteria=criteria, options=[option])


def _strategy(
    r13: R13TherapeuticSnapshot,
    *,
    status: R14FinalClinicalStatus,
    blocking_gates=None,
    clinician_id=None,
    clinician_validated_at=None,
    final_validation_ref=None,
) -> R14FinalClinicalStrategyEvidence:
    option = r13.options[0]
    criterion_refs = [*option.indication_refs, *option.contraindication_refs]
    source_map = {
        (item.source_id, item.source_version): item for item in option.source_refs
    }
    criteria = {item.criterion_id: item for item in r13.criteria}
    for criterion_id in criterion_refs:
        for source in criteria[criterion_id].source_refs:
            source_map[(source.source_id, source.source_version)] = source
    option_validation_refs = (
        [option.decision_validation_ref] if option.decision_validation_ref is not None else []
    )
    return R14FinalClinicalStrategyEvidence(
        strategy_id="strategy:r14:synthetic",
        option_refs=[option.option_id],
        option_validation_refs=option_validation_refs,
        criterion_refs=criterion_refs,
        source_refs=list(source_map.values()),
        objective_refs=list(option.objective_refs),
        problem_refs=list(option.problem_refs),
        diagnosis_refs=list(option.diagnosis_refs),
        finding_refs=list(option.finding_refs),
        evidence_refs=[option.option_id, *option.evidence_refs],
        missing_data_refs=list(option.missing_data_refs),
        contradictions=list(option.contradictions),
        blocking_gates=list(blocking_gates or []),
        status=status,
        clinician_id=clinician_id,
        clinician_validated_at=clinician_validated_at,
        final_validation_ref=final_validation_ref,
    )


def _final_validation(*, target_type: str = "final_clinical_strategy"):
    return ClinicianValidationEvidence(
        validation_id="validation:r14:final",
        clinician_id="clinician:1",
        validated_at=NOW,
        action=ValidationAction.ACCEPT,
        target_type=target_type,
        target_id="strategy:r14:synthetic",
        before_snapshot_hash="r14-strategy-before",
        after_snapshot_hash="r14-strategy-after",
    )


def _validate(snapshot: R14FinalClinicalSnapshot):
    validate_r14_final_clinical_validation(
        snapshot,
        diagnostic_rule_registry=_diagnostic_registry(),
        therapeutic_rule_registry=_therapeutic_registry(),
    )


def test_r14_positive_golden_requires_selected_r13_option_and_final_clinician_validation():
    r13 = _selected_r13()
    validation = _final_validation()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.CLINICIAN_VALIDATED,
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
        final_validation_ref=validation.validation_id,
    )

    _validate(
        R14FinalClinicalSnapshot(
            r13_snapshot=r13,
            strategies=[strategy],
            final_validations=[validation],
        )
    )

    assert strategy.status == R14FinalClinicalStatus.CLINICIAN_VALIDATED
    assert strategy.option_refs == ["option:r13:synthetic"]
    assert strategy.option_validation_refs == ["validation:r13:option:selected"]
    assert strategy.final_validation_ref == validation.validation_id


def test_r14_evaluable_r13_option_cannot_be_auto_promoted_to_final_state():
    r13 = _evaluable_r13()
    validation = _final_validation()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.CLINICIAN_VALIDATED,
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
        final_validation_ref=validation.validation_id,
    )

    with pytest.raises(EvidenceGraphValidationError, match="blocking_gates must exactly match"):
        _validate(
            R14FinalClinicalSnapshot(
                r13_snapshot=r13,
                strategies=[strategy],
                final_validations=[validation],
            )
        )


def test_r14_evaluable_option_is_representable_only_as_explicitly_blocked():
    r13 = _evaluable_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.BLOCKED,
        blocking_gates=["r13:option:r13:synthetic:clinician_selection_required"],
    )

    _validate(R14FinalClinicalSnapshot(r13_snapshot=r13, strategies=[strategy]))
    assert strategy.final_validation_ref is None


def test_r14_preserves_r13_missing_data_and_blocking_gates_without_drop():
    r13 = _blocked_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.BLOCKED,
        blocking_gates=[
            "missing:source:r13:missing",
            "r13:option:r13:synthetic:missing:source:r13:missing",
            "r13:option:r13:synthetic:indication:criterion:r13:indication:BLOCKED",
        ],
    )

    _validate(R14FinalClinicalSnapshot(r13_snapshot=r13, strategies=[strategy]))
    assert strategy.missing_data_refs == ["source:r13:missing"]


def test_r14_preserves_upstream_contradiction_and_keeps_it_blocking():
    r13 = _contradictory_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.BLOCKED,
        blocking_gates=[
            "contradiction:synthetic upstream contradiction",
            "r13:option:r13:synthetic:contradiction:synthetic upstream contradiction",
        ],
    )

    _validate(R14FinalClinicalSnapshot(r13_snapshot=r13, strategies=[strategy]))
    assert strategy.contradictions == ["synthetic upstream contradiction"]


def test_r14_rejects_silent_drop_of_missing_data():
    r13 = _blocked_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.BLOCKED,
        blocking_gates=[
            "missing:source:r13:missing",
            "r13:option:r13:synthetic:missing:source:r13:missing",
            "r13:option:r13:synthetic:indication:criterion:r13:indication:BLOCKED",
        ],
    )
    tampered = strategy.model_copy(update={"missing_data_refs": []})

    with pytest.raises(EvidenceGraphValidationError, match="missing_data_refs must exactly match"):
        _validate(R14FinalClinicalSnapshot(r13_snapshot=r13, strategies=[tampered]))


def test_r14_rejects_provenance_tampering_below_r13():
    r13 = _selected_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION,
    )
    tampered = strategy.model_copy(update={"finding_refs": ["finding:tampered"]})

    with pytest.raises(EvidenceGraphValidationError, match="finding_refs must exactly match"):
        _validate(R14FinalClinicalSnapshot(r13_snapshot=r13, strategies=[tampered]))


def test_r14_rejects_drop_of_r13_option_decision_validation_provenance():
    r13 = _selected_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION,
    )
    tampered = strategy.model_copy(update={"option_validation_refs": []})

    with pytest.raises(EvidenceGraphValidationError, match="option_validation_refs must exactly match"):
        _validate(R14FinalClinicalSnapshot(r13_snapshot=r13, strategies=[tampered]))


def test_r14_final_state_rejects_unresolved_validation_reference():
    r13 = _selected_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.CLINICIAN_VALIDATED,
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
        final_validation_ref="validation:r14:missing",
    )

    with pytest.raises(EvidenceGraphValidationError, match="final_validation_ref does not resolve"):
        _validate(R14FinalClinicalSnapshot(r13_snapshot=r13, strategies=[strategy]))


def test_r14_final_validation_must_target_the_strategy():
    r13 = _selected_r13()
    validation = _final_validation(target_type="treatment_option")
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.CLINICIAN_VALIDATED,
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
        final_validation_ref=validation.validation_id,
    )

    with pytest.raises(EvidenceGraphValidationError, match="must target that strategy"):
        _validate(
            R14FinalClinicalSnapshot(
                r13_snapshot=r13,
                strategies=[strategy],
                final_validations=[validation],
            )
        )


def test_r14_orphan_final_validation_is_rejected():
    r13 = _selected_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION,
    )

    with pytest.raises(EvidenceGraphValidationError, match="must be referenced"):
        _validate(
            R14FinalClinicalSnapshot(
                r13_snapshot=r13,
                strategies=[strategy],
                final_validations=[_final_validation()],
            )
        )


def test_r14_reexecutes_r13_and_rejects_invalid_upstream_option_audit():
    r13 = _selected_r13()
    invalid_r13 = R13TherapeuticSnapshot(
        r12_snapshot=r13.r12_snapshot,
        criteria=r13.criteria,
        options=r13.options,
        option_validations=[],
    )
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION,
    )

    with pytest.raises(EvidenceGraphValidationError, match="decision_validation_ref does not resolve"):
        _validate(R14FinalClinicalSnapshot(r13_snapshot=invalid_r13, strategies=[strategy]))


def test_r14_schema_forbids_free_text_strategy_or_sequencing_fields():
    r13 = _selected_r13()
    strategy = _strategy(
        r13,
        status=R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION,
    )
    payload = strategy.model_dump()
    payload["strategy_statement"] = "forbidden-free-text-treatment-content"
    payload["sequencing"] = ["forbidden-in-r14"]

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        R14FinalClinicalStrategyEvidence.model_validate(payload)


def test_r14_final_clinician_timestamp_must_be_timezone_aware():
    r13 = _selected_r13()
    with pytest.raises(ValidationError, match="timezone-aware"):
        _strategy(
            r13,
            status=R14FinalClinicalStatus.CLINICIAN_VALIDATED,
            clinician_id="clinician:1",
            clinician_validated_at=datetime(2026, 9, 12, 15, 0),
            final_validation_ref="validation:r14:final",
        )
