"""R11 schema tests for explicit missing-data states."""

import pytest
from pydantic import ValidationError

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    DiagnosticHypothesisEvidence,
    FindingEvidence,
    ReviewState,
)


def test_r11_not_computable_finding_can_exist_without_positive_evidence():
    finding = FindingEvidence(
        finding_id="finding:missing:r11",
        domain="skeletal",
        rule_id="R11_SYNTHETIC_TEST_ONLY",
        rule_version="1",
        supporting_evidence_refs=[],
        missing_evidence_refs=["measurement:missing:r11"],
        statement="Synthetic missing-data finding.",
        availability_status=AvailabilityStatus.NOT_COMPUTABLE,
    )
    assert finding.supporting_evidence_refs == []
    assert finding.missing_evidence_refs == ["measurement:missing:r11"]


def test_r11_available_finding_requires_positive_evidence():
    with pytest.raises(ValidationError, match="Available finding requires supporting evidence"):
        FindingEvidence(
            finding_id="finding:unsafe:r11",
            domain="skeletal",
            rule_id="R11_SYNTHETIC_TEST_ONLY",
            rule_version="1",
            supporting_evidence_refs=[],
            statement="Synthetic invalid available finding.",
        )


def test_r11_unavailable_finding_requires_explicit_missing_refs():
    with pytest.raises(ValidationError, match="explicit missing evidence refs"):
        FindingEvidence(
            finding_id="finding:opaque:r11",
            domain="skeletal",
            rule_id="R11_SYNTHETIC_TEST_ONLY",
            rule_version="1",
            supporting_evidence_refs=[],
            statement="Synthetic invalid unavailable finding.",
            availability_status=AvailabilityStatus.NOT_COMPUTABLE,
        )


def test_r11_insufficient_data_diagnosis_can_exist_without_supporting_finding():
    diagnosis = DiagnosticHypothesisEvidence(
        diagnosis_id="diagnosis:insufficient:r11",
        domain="skeletal",
        supporting_finding_refs=[],
        missing_data_refs=["measurement:missing:r11"],
        statement="Synthetic insufficient-data hypothesis.",
        state=ReviewState.INSUFFICIENT_DATA,
    )
    assert diagnosis.supporting_finding_refs == []
    assert diagnosis.state == ReviewState.INSUFFICIENT_DATA


def test_r11_insufficient_data_diagnosis_requires_missing_refs():
    with pytest.raises(ValidationError, match="explicit missing data refs"):
        DiagnosticHypothesisEvidence(
            diagnosis_id="diagnosis:opaque:r11",
            domain="skeletal",
            supporting_finding_refs=[],
            statement="Synthetic invalid insufficient-data hypothesis.",
            state=ReviewState.INSUFFICIENT_DATA,
        )


def test_r11_proposed_diagnosis_requires_supporting_findings():
    with pytest.raises(ValidationError, match="requires supporting findings"):
        DiagnosticHypothesisEvidence(
            diagnosis_id="diagnosis:unsupported:r11",
            domain="skeletal",
            supporting_finding_refs=[],
            missing_data_refs=["measurement:missing:r11"],
            statement="Synthetic unsupported hypothesis.",
            state=ReviewState.PROPOSED,
        )
