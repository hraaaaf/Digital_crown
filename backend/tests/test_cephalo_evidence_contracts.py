"""Fail-closed contract tests for the cephalometric evidence graph."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    DiagnosticHypothesisEvidence,
    FinalPlanEvidence,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
    NormativeEvaluationEvidence,
    ReviewState,
    TreatmentOptionEvidence,
    TreatmentOptionStatus,
    TreatmentPhaseEvidence,
)


NOW = datetime(2026, 9, 10, 9, 0, tzinfo=timezone.utc)


def test_available_construction_requires_real_landmark_refs_and_geometry():
    with pytest.raises(ValidationError, match="landmark evidence refs"):
        ConstructionEvidence(
            construction_id="construction:fh",
            definition_id="FH_PO_OR_V1",
            definition_version="1",
            geometry={"kind": "axis"},
        )
    with pytest.raises(ValidationError, match="explicit geometry"):
        ConstructionEvidence(
            construction_id="construction:fh",
            definition_id="FH_PO_OR_V1",
            definition_version="1",
            landmark_refs=["landmark:Po", "landmark:Or"],
        )


def test_unavailable_construction_can_record_missing_landmarks_without_fake_refs():
    construction = ConstructionEvidence(
        construction_id="construction:fh:missing",
        definition_id="FH_PO_OR_V1",
        definition_version="1",
        landmark_refs=[],
        missing_landmark_ids=["Po", "Or"],
        geometry={},
        evidence_refs=[],
        availability_status=AvailabilityStatus.NOT_COMPUTABLE,
    )
    assert construction.landmark_refs == []
    assert construction.missing_landmark_ids == ["Po", "Or"]
    assert construction.availability_status == AvailabilityStatus.NOT_COMPUTABLE


def test_available_construction_cannot_claim_missing_landmarks():
    with pytest.raises(ValidationError, match="cannot declare missing"):
        ConstructionEvidence(
            construction_id="construction:fh",
            definition_id="FH_PO_OR_V1",
            definition_version="1",
            landmark_refs=["landmark:Po"],
            missing_landmark_ids=["Or"],
            geometry={"kind": "axis"},
        )


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


def test_linear_measurement_requires_calibration_reference_when_available():
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


def test_uncalibrated_linear_measurement_can_be_explicitly_not_computable():
    measurement = MeasurementEvidence(
        measurement_id="m2:not-computable",
        analysis_id="COM",
        method_id="CRANIOM_AB_PRIME_V1",
        method_version="1",
        value=None,
        unit="mm",
        construction_refs=["construction:ab-prime"],
        calibration_ref=None,
        requires_calibration=True,
        availability_status=AvailabilityStatus.NOT_COMPUTABLE,
        evidence_refs=["construction:ab-prime"],
    )
    assert measurement.value is None
    assert measurement.calibration_ref is None
    assert measurement.availability_status == AvailabilityStatus.NOT_COMPUTABLE


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


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_measurement_rejects_nonfinite_patient_value(value):
    with pytest.raises(ValidationError):
        MeasurementEvidence(
            measurement_id="m4",
            analysis_id="COM",
            method_id="CRANIOM_AB_PRIME_V1",
            method_version="1",
            value=value,
            unit="mm",
            construction_refs=["construction:ab-prime"],
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


@pytest.mark.parametrize("x,y", [(float("nan"), 1.0), (1.0, float("inf"))])
def test_landmark_rejects_nonfinite_coordinates(x, y):
    with pytest.raises(ValidationError):
        LandmarkEvidence(
            evidence_id="lm:N",
            landmark_id="N",
            x=x,
            y=y,
            source_image_ref="ceph:1",
            origin=LandmarkOrigin.MANUAL,
            evidence_refs=["source:ceph:1"],
            evidence_status="OBSERVED",
        )


def test_normative_evaluation_requires_explicit_reference():
    with pytest.raises(ValidationError):
        NormativeEvaluationEvidence(
            evaluation_id="norm:1",
            measurement_ref="m1",
            norm_profile_id="CRANIOM_ADULT_SAMPLE",
            norm_profile_version="1",
            reference={},
            source_refs=["doi:10.1051/odfen/2010406"],
            evidence_refs=["m1"],
        )


def test_normative_classification_requires_versioned_rule():
    with pytest.raises(ValidationError):
        NormativeEvaluationEvidence(
            evaluation_id="norm:2",
            measurement_ref="m1",
            norm_profile_id="CRANIOM_ADULT_SAMPLE",
            norm_profile_version="1",
            reference={"kind": "method_specific_range"},
            classification="within_reference",
            source_refs=["doi:10.1051/odfen/2010406"],
            evidence_refs=["m1"],
        )


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
