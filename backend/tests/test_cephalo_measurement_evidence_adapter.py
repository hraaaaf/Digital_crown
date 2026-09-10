"""Runtime-to-evidence adapter tests for certified CRANIOM linear geometry."""

from datetime import datetime, timezone

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    ConstructionEvidence,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
    SourceEvidence,
)
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot
from backend.services.cephalo_measurement_evidence_adapter import (
    CephaloMeasurementEvidenceAdapterError,
    adapt_craniom_linear_measurements,
)


NOW = datetime(2026, 9, 10, 12, 30, tzinfo=timezone.utc)
CASE_ID = "case:adapter:1"
PATIENT_ID = 11
ANALYSIS_ID = "analysis:42"
CALIBRATION_REF = "source:calibration:42"

CONSTRUCTION_REFS = {
    "Situation_A": "construction:42:situation-a",
    "Situation_B": "construction:42:situation-b",
    "Decalage_A_B": "construction:42:ab-prime",
    "Profondeur_Faciale": "construction:42:facial-depth",
}

METHODS = {
    "Situation_A": "CRANIOM_A_TO_N_VERTICAL_V1",
    "Situation_B": "CRANIOM_B_TO_N_VERTICAL_V1",
    "Decalage_A_B": "CRANIOM_AB_PRIME_V1",
    "Profondeur_Faciale": "CRANIOM_S_TO_N_VERTICAL_DEPTH_V1",
}


def _points():
    return {
        "S": (10.0, 10.0),
        "N": (20.0, 10.0),
        "Po": (0.0, 20.0),
        "Or": (20.0, 20.0),
        "A": (24.0, 28.0),
        "B": (22.0, 38.0),
        "Go": (5.0, 50.0),
        "Me": (25.0, 55.0),
        "U1a": (20.0, 25.0),
        "U1i": (24.0, 35.0),
        "L1a": (20.0, 48.0),
        "L1i": (23.0, 38.0),
    }


def _runtime_result(mm_per_pixel=0.2):
    return CephaloEngine(mm_per_pixel=mm_per_pixel).calculate_metrics(_points())


def _adapt(result=None, calibration_ref=CALIBRATION_REF, construction_refs=None):
    return adapt_craniom_linear_measurements(
        result or _runtime_result(),
        analysis_instance_id=ANALYSIS_ID,
        construction_refs=construction_refs or CONSTRUCTION_REFS,
        calibration_ref=calibration_ref,
    )


def test_adapter_emits_only_four_certified_craniom_linear_measurements():
    measurements = _adapt()

    assert len(measurements) == 4
    by_field = {
        measurement.measurement_id.rsplit(":", 1)[-1]: measurement
        for measurement in measurements
    }
    assert set(by_field) == set(CONSTRUCTION_REFS)

    for field, measurement in by_field.items():
        assert measurement.analysis_id == "CRANIOM"
        assert measurement.method_id == METHODS[field]
        assert measurement.method_version == "1"
        assert measurement.unit == "mm"
        assert measurement.value is not None
        assert measurement.availability_status == AvailabilityStatus.AVAILABLE
        assert measurement.construction_refs == [CONSTRUCTION_REFS[field]]
        assert measurement.calibration_ref == CALIBRATION_REF
        assert measurement.requires_calibration is True
        assert measurement.evidence_refs == [CONSTRUCTION_REFS[field], CALIBRATION_REF]


def test_missing_runtime_values_remain_not_computable_never_zero():
    result = _runtime_result(mm_per_pixel=None)
    measurements = _adapt(result=result, calibration_ref=None)

    assert len(measurements) == 4
    for measurement in measurements:
        assert measurement.value is None
        assert measurement.availability_status == AvailabilityStatus.NOT_COMPUTABLE
        assert measurement.calibration_ref is None
        assert measurement.requires_calibration is True


def test_available_value_without_calibration_evidence_is_rejected():
    with pytest.raises(
        CephaloMeasurementEvidenceAdapterError,
        match="without calibration_ref",
    ):
        _adapt(calibration_ref=None)


def test_available_value_with_inconsistent_runtime_ratio_is_rejected():
    result = _runtime_result()
    bad_metadata = result.analysis_metadata.model_copy(update={"pixel_ratio": None})
    inconsistent = result.model_copy(update={"analysis_metadata": bad_metadata})

    with pytest.raises(
        CephaloMeasurementEvidenceAdapterError,
        match="without valid mm/pixel calibration",
    ):
        _adapt(result=inconsistent)


def test_adapter_rejects_non_craniom_runtime_payload():
    result = _runtime_result()
    wrong_metadata = result.analysis_metadata.model_copy(update={"type": "STEINER"})
    wrong = result.model_copy(update={"analysis_metadata": wrong_metadata})

    with pytest.raises(CephaloMeasurementEvidenceAdapterError, match="COM_Skeletal"):
        _adapt(result=wrong)


def test_adapter_refuses_to_invent_missing_construction_reference():
    incomplete = dict(CONSTRUCTION_REFS)
    del incomplete["Decalage_A_B"]

    with pytest.raises(
        CephaloMeasurementEvidenceAdapterError,
        match="Missing explicit construction ref for Decalage_A_B",
    ):
        _adapt(construction_refs=incomplete)


def test_adapter_output_resolves_in_patient_case_graph():
    ceph_source = SourceEvidence(
        evidence_id="source:ceph:42",
        patient_id=PATIENT_ID,
        kind="lateral_ceph",
        source_record_id="record:ceph:42",
        recorded_at=NOW,
        metadata={"case_id": CASE_ID},
    )
    calibration_source = SourceEvidence(
        evidence_id=CALIBRATION_REF,
        patient_id=PATIENT_ID,
        kind="calibration",
        source_record_id="record:calibration:42",
        recorded_at=NOW,
        metadata={"case_id": CASE_ID},
    )

    landmark_ids = ["S", "N", "Po", "Or", "A", "B"]
    landmarks = [
        LandmarkEvidence(
            evidence_id=f"landmark:42:{landmark_id}",
            landmark_id=landmark_id,
            x=float(index + 1),
            y=float(index + 10),
            source_image_ref=ceph_source.evidence_id,
            origin=LandmarkOrigin.MANUAL,
            evidence_refs=[ceph_source.evidence_id],
            evidence_status=EvidenceStatus.OBSERVED,
        )
        for index, landmark_id in enumerate(landmark_ids)
    ]
    landmark_refs = [landmark.evidence_id for landmark in landmarks]

    constructions = [
        ConstructionEvidence(
            construction_id=CONSTRUCTION_REFS[field],
            definition_id=method_id,
            definition_version="1",
            landmark_refs=landmark_refs,
            geometry={"kind": "certified_test_construction", "field": field},
            evidence_refs=landmark_refs,
        )
        for field, method_id in METHODS.items()
    ]

    measurements = _adapt()
    graph = EvidenceGraphSnapshot(
        sources=[ceph_source, calibration_source],
        landmarks=landmarks,
        constructions=constructions,
        measurements=measurements,
    )

    validate_case_evidence_graph(
        graph,
        patient_id=PATIENT_ID,
        case_id=CASE_ID,
    )
