"""Fail-closed contract tests for the cephalometric evidence graph."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    DiagnosticHypothesisEvidence,
    FinalPlanEvidence,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
    ReviewState,
    TreatmentOptionEvidence,
    TreatmentOptionStatus,
    TreatmentPhaseEvidence,
)


NOW = datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)


def test_measurement_requires_geometric_dependencies():
    with pytest.raises(ValidationError):
        MeasurementEvidence(
            measurement_id="m1",
            analysis_id="COM",
            method_id="CRANIOM_AB_PRIME_V1",
            method_version="1",
            value=4.2,
            unit="mm",
            evidence_refs=["source:ceph:1"],
        )


def test_linear_measurement_requires_calibration_reference():
    with pytest.raises(ValidationError):
        MeasurementEvidence(
            measurement_id="m2",
            analysis_id="COM",
            method_id="CRANIOM_AB_PRIME_V1",
            method_version="1",
            value=4.2,
            unit="mm",
            construction_refs=["construction:ab-prime"],
            requires_calibration=True,
            evidence_refs=["source:ceph:1"],
        )


def test_unavailable_measurement_cannot_carry_patient_value():
    with pytest.raises(ValidationError):
        MeasurementEvidence(
            measurement_id="m3",
            analysis_id="COM",
            method_id="CRANIOM_AB_PRIME_V1",
            method_version="1",
            value=4.2,
            unit="mm",
            construction_refs=["construction:ab-prime"],
            availability_status=AvailabilityStatus.NOT_COMPUTABLE,
            evidence_refs=["source:ceph:1"],
        )


def test_manual_landmark_correction_preserves_auto_coordinate_and_audit():
    with pytest.raises(ValidationError):
        LandmarkEvidence(
            evidence_id="lm:A",
            landmark_id="A",
            x=123.4,
            y=456.7,
            source_image_ref="ceph:1",
            origin=LandmarkOrigin.MANUAL_CORRECTED,
            evidence_refs=["source:ceph:1"],
            evidence_status="CLINICIAN_VALIDATED",
        )

    corrected = LandmarkEvidence(
        evidence_id="lm:A",
        landmark_id="A",
        x=123.4,
        y=456.7,
        source_image_ref="ceph:1",
        origin=LandmarkOrigin.MANUAL_CORRECTED,
        original_auto_x=120.0,
        original_auto_y=450.0,
        validated_by="clinician:1",
        validated_at=NOW,
        evidence_refs=["source:ceph:1"],
        evidence_status="CLINICIAN_VALIDATED",
    )
    assert corrected.original_auto_x == 120.0
    assert corrected.validated_by == "clinician:1"


def test_accepted_diagnosis_requires_clinician_validation():
    with pytest.raises(ValidationError):
        DiagnosticHypothesisEvidence(
            diagnosis_id="dx:1",
            domain="skeletal_sagittal",
            supporting_finding_refs=["finding:1"],
            statement="Hypothèse diagnostique test",
            state=ReviewState.ACCEPTED,
        )


def test_treatment_option_with_missing_gate_is_blocked():
    with pytest.raises(ValidationError):
        TreatmentOptionEvidence(
            option_id="tx:1",
            objective_refs=["obj:1"],
            required_evidence_refs=["panoramic:1"],
            missing_gates=["periodontal_status"],
            status=TreatmentOptionStatus.EVALUABLE,
        )

    blocked = TreatmentOptionEvidence(
        option_id="tx:1",
        objective_refs=["obj:1"],
        required_evidence_refs=["panoramic:1"],
        missing_gates=["periodontal_status"],
        status=TreatmentOptionStatus.BLOCKED_INSUFFICIENT_DATA,
    )
    assert blocked.status == TreatmentOptionStatus.BLOCKED_INSUFFICIENT_DATA


def test_final_plan_requires_explicit_clinician_gate():
    phase = TreatmentPhaseEvidence(
        phase_id="phase:1",
        title="Phase test",
        objective_refs=["obj:1"],
    )

    with pytest.raises(ValidationError):
        FinalPlanEvidence.model_validate(
            {
                "plan_id": "plan:1",
                "selected_option_ref": "tx:1",
                "validated_diagnosis_refs": ["dx:1"],
                "validated_problem_refs": ["problem:1"],
                "validated_objective_refs": ["obj:1"],
                "phases": [phase.model_dump()],
                "validation_ref": "validation:1",
            }
        )
