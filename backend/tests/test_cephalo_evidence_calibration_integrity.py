"""Calibration-source integrity gate for the case-bound evidence graph."""

from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import (
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
    SourceEvidence,
)
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import (
    EvidenceGraphSnapshot,
    EvidenceGraphValidationError,
)


NOW = datetime(2026, 9, 10, 12, 45, tzinfo=timezone.utc)
CASE_ID = "case:calibration-gate"


def test_calibration_ref_must_resolve_to_calibration_source_kind():
    ceph = SourceEvidence(
        evidence_id="source:ceph",
        patient_id=1,
        kind="lateral_ceph",
        source_record_id="record:ceph",
        recorded_at=NOW,
        metadata={"case_id": CASE_ID},
    )
    fake_calibration = SourceEvidence(
        evidence_id="source:not-calibration",
        patient_id=1,
        kind="lateral_ceph",
        source_record_id="record:not-calibration",
        recorded_at=NOW,
        metadata={"case_id": CASE_ID},
    )
    landmark = LandmarkEvidence(
        evidence_id="landmark:A",
        landmark_id="A",
        x=10.0,
        y=20.0,
        source_image_ref=ceph.evidence_id,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[ceph.evidence_id],
        evidence_status=EvidenceStatus.OBSERVED,
    )
    measurement = MeasurementEvidence(
        measurement_id="measurement:linear",
        analysis_id="TEST",
        method_id="TEST_LINEAR",
        method_version="1",
        value=1.0,
        unit="mm",
        landmark_refs=[landmark.evidence_id],
        calibration_ref=fake_calibration.evidence_id,
        requires_calibration=True,
        evidence_refs=[landmark.evidence_id, fake_calibration.evidence_id],
    )
    graph = EvidenceGraphSnapshot(
        sources=[ceph, fake_calibration],
        landmarks=[landmark],
        measurements=[measurement],
    )

    with pytest.raises(EvidenceGraphValidationError, match="kind='calibration'"):
        validate_case_evidence_graph(graph, patient_id=1, case_id=CASE_ID)
