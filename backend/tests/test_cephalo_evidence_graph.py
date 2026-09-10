"""Cross-object integrity tests for the cephalometric evidence graph."""

from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import (
    ClinicianValidationEvidence,
    ConstructionEvidence,
    DiagnosticHypothesisEvidence,
    EvidenceStatus,
    FinalPlanEvidence,
    FindingEvidence,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
    NormativeEvaluationEvidence,
    ObjectiveEvidence,
    ProblemEvidence,
    ReviewState,
    SourceEvidence,
    TreatmentOptionEvidence,
    TreatmentOptionStatus,
    TreatmentPhaseEvidence,
    ValidationAction,
)
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
    validate_evidence_graph,
)


NOW = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)


def _valid_graph() -> EvidenceGraphSnapshot:
    source = SourceEvidence(
        evidence_id="source:ceph:1",
        patient_id=1,
        kind="lateral_ceph",
        source_record_id="record:1",
        recorded_at=NOW,
        operator_id="clinician:1",
    )
    calibration = SourceEvidence(
        evidence_id="source:calibration:1",
        patient_id=1,
        kind="calibration",
        source_record_id="calibration:1",
        recorded_at=NOW,
        operator_id="clinician:1",
    )
    po = LandmarkEvidence(
        evidence_id="landmark:Po",
        landmark_id="Po",
        x=10.0,
        y=20.0,
        source_image_ref="source:ceph:1",
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:ceph:1"],
        evidence_status=EvidenceStatus.OBSERVED,
    )
    orbitale = LandmarkEvidence(
        evidence_id="landmark:Or",
        landmark_id="Or",
        x=30.0,
        y=20.0,
        source_image_ref="source:ceph:1",
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:ceph:1"],
        evidence_status=EvidenceStatus.OBSERVED,
    )
    construction = ConstructionEvidence(
        construction_id="construction:FH_PO_OR_V1",
        definition_id="FH_PO_OR_V1",
        definition_version="1",
        landmark_refs=["landmark:Po", "landmark:Or"],
        geometry={"kind": "axis", "start": "Po", "end": "Or"},
        evidence_refs=["landmark:Po", "landmark:Or"],
    )
    measurement = MeasurementEvidence(
        measurement_id="measurement:U1_FH",
        analysis_id="CRANIOM",
        method_id="U1_TO_FRANKFORT_ANGLE",
        method_version="1",
        value=112.0,
        unit="deg",
        construction_refs=["construction:FH_PO_OR_V1"],
        evidence_refs=["construction:FH_PO_OR_V1"],
    )
    evaluation = NormativeEvaluationEvidence(
        evaluation_id="evaluation:U1_FH",
        measurement_ref="measurement:U1_FH",
        norm_profile_id="CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1",
        norm_profile_version="2010-2011",
        context={"mode": "synthetic_contract_test"},
        reference={"kind": "EXTREME_RANGE", "lower": 97.5, "upper": 130.1},
        source_refs=["CRANIOM_PART2_2011"],
        evidence_refs=["measurement:U1_FH"],
    )
    finding = FindingEvidence(
        finding_id="finding:synthetic",
        domain="dentoalveolar",
        rule_id="SYNTHETIC_TEST_RULE",
        rule_version="1",
        supporting_evidence_refs=["evaluation:U1_FH"],
        statement="Synthetic finding used only to test graph integrity.",
    )
    diagnosis = DiagnosticHypothesisEvidence(
        diagnosis_id="diagnosis:synthetic",
        domain="synthetic",
        supporting_finding_refs=["finding:synthetic"],
        statement="Synthetic diagnosis used only to test graph integrity.",
        state=ReviewState.ACCEPTED,
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
    )
    problem = ProblemEvidence(
        problem_id="problem:synthetic",
        diagnosis_refs=["diagnosis:synthetic"],
        evidence_refs=["diagnosis:synthetic"],
        statement="Synthetic problem.",
        state=ReviewState.ACCEPTED,
    )
    objective = ObjectiveEvidence(
        objective_id="objective:synthetic",
        problem_refs=["problem:synthetic"],
        target="Synthetic target",
        success_criterion="Synthetic criterion",
        state=ReviewState.ACCEPTED,
    )
    option = TreatmentOptionEvidence(
        option_id="option:synthetic",
        objective_refs=["objective:synthetic"],
        required_evidence_refs=["source:ceph:1"],
        status=TreatmentOptionStatus.CLINICIAN_SELECTED,
    )
    validation = ClinicianValidationEvidence(
        validation_id="validation:plan:synthetic",
        clinician_id="clinician:1",
        validated_at=NOW,
        action=ValidationAction.ACCEPT,
        target_type="final_plan",
        target_id="plan:synthetic",
        before_snapshot_hash="before",
        after_snapshot_hash="after",
    )
    plan = FinalPlanEvidence(
        plan_id="plan:synthetic",
        selected_option_ref="option:synthetic",
        validated_diagnosis_refs=["diagnosis:synthetic"],
        validated_problem_refs=["problem:synthetic"],
        validated_objective_refs=["objective:synthetic"],
        phases=[
            TreatmentPhaseEvidence(
                phase_id="phase:synthetic",
                title="Synthetic phase",
                objective_refs=["objective:synthetic"],
            )
        ],
        clinician_id="clinician:1",
        clinician_validated_at=NOW,
        validation_ref="validation:plan:synthetic",
    )
    return EvidenceGraphSnapshot(
        sources=[source, calibration],
        landmarks=[po, orbitale],
        constructions=[construction],
        measurements=[measurement],
        normative_evaluations=[evaluation],
        findings=[finding],
        diagnoses=[diagnosis],
        problems=[problem],
        objectives=[objective],
        treatment_options=[option],
        validations=[validation],
        final_plans=[plan],
    )


def test_complete_synthetic_chain_resolves_without_free_text_as_evidence():
    validate_evidence_graph(_valid_graph())


def test_missing_landmark_reference_is_rejected():
    graph = _valid_graph()
    bad_construction = graph.constructions[0].model_copy(
        update={"landmark_refs": ["landmark:Po", "landmark:missing"]}
    )
    bad_graph = EvidenceGraphSnapshot(
        **{**graph.__dict__, "constructions": [bad_construction]}
    )
    with pytest.raises(EvidenceGraphValidationError, match="landmark:missing"):
        validate_evidence_graph(bad_graph)


def test_missing_normative_source_reference_is_rejected():
    graph = _valid_graph()
    bad_evaluation = graph.normative_evaluations[0].model_copy(
        update={"source_refs": ["UNKNOWN_SOURCE"]}
    )
    bad_graph = EvidenceGraphSnapshot(
        **{**graph.__dict__, "normative_evaluations": [bad_evaluation]}
    )
    with pytest.raises(EvidenceGraphValidationError, match="UNKNOWN_SOURCE"):
        validate_evidence_graph(bad_graph)


def test_final_plan_requires_selected_option_status():
    graph = _valid_graph()
    option = graph.treatment_options[0].model_copy(
        update={"status": TreatmentOptionStatus.EVALUABLE}
    )
    bad_graph = EvidenceGraphSnapshot(
        **{**graph.__dict__, "treatment_options": [option]}
    )
    with pytest.raises(EvidenceGraphValidationError, match="CLINICIAN_SELECTED"):
        validate_evidence_graph(bad_graph)


def test_final_plan_rejects_unvalidated_diagnosis():
    graph = _valid_graph()
    diagnosis = graph.diagnoses[0].model_copy(
        update={
            "state": ReviewState.PROPOSED,
            "clinician_id": None,
            "clinician_validated_at": None,
        }
    )
    bad_graph = EvidenceGraphSnapshot(**{**graph.__dict__, "diagnoses": [diagnosis]})
    with pytest.raises(EvidenceGraphValidationError, match="unvalidated diagnosis"):
        validate_evidence_graph(bad_graph)


def test_final_plan_and_validation_must_have_same_clinician():
    graph = _valid_graph()
    validation = graph.validations[0].model_copy(update={"clinician_id": "clinician:2"})
    bad_graph = EvidenceGraphSnapshot(**{**graph.__dict__, "validations": [validation]})
    with pytest.raises(EvidenceGraphValidationError, match="clinician differs"):
        validate_evidence_graph(bad_graph)
