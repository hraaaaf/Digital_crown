import json
from pathlib import Path

import pytest

from scripts.train_ricketts_mandible_specialist import (
    LANDMARKS,
    MODEL_ID,
    NON_CLINICAL_MARKER,
    validate_real_dataset_contract,
)


def test_landmark_contract_is_source_specific_and_minimal():
    assert MODEL_ID == "RICKETTS_MANDIBLE_SPECIALIST_V1"
    assert LANDMARKS == (
        "R1_Ricketts",
        "R2_Ricketts",
        "R3_Ricketts",
        "R4_Ricketts",
        "Pm_Ricketts",
        "DC_Ricketts",
    )


def test_smoke_artifact_is_explicitly_non_clinical():
    assert NON_CLINICAL_MARKER == "NON_CLINICAL_SMOKE_ONLY"


def test_real_mode_fails_closed_without_manifest(tmp_path: Path):
    with pytest.raises(SystemExit, match="REAL_DATASET_REQUIRED"):
        validate_real_dataset_contract(tmp_path)


def test_real_mode_rejects_unverified_dataset(tmp_path: Path):
    payload = {
        "schema": "RICKETTS_MANDIBLE_SPECIALIST_DATASET_V1",
        "landmarks": list(LANDMARKS),
        "license_verified": False,
        "clinician_annotation_verified": True,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit, match="REAL_DATASET_LICENSE_NOT_VERIFIED"):
        validate_real_dataset_contract(tmp_path)


def test_real_mode_remains_disabled_even_after_contract_passes(tmp_path: Path):
    payload = {
        "schema": "RICKETTS_MANDIBLE_SPECIALIST_DATASET_V1",
        "landmarks": list(LANDMARKS),
        "license_verified": True,
        "clinician_annotation_verified": True,
        "patient_split_provenance": "patient-level immutable split manifest",
        "deidentification_evidence": "documented de-identification review",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit, match="REAL_TRAINING_NOT_ENABLED_YET"):
        validate_real_dataset_contract(tmp_path)


def test_real_mode_requires_patient_split_provenance(tmp_path: Path):
    payload = {
        "schema": "RICKETTS_MANDIBLE_SPECIALIST_DATASET_V1",
        "landmarks": list(LANDMARKS),
        "license_verified": True,
        "clinician_annotation_verified": True,
        "deidentification_evidence": "documented",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit, match="REAL_DATASET_PATIENT_SPLIT_PROVENANCE_REQUIRED"):
        validate_real_dataset_contract(tmp_path)


def test_real_mode_requires_deidentification_evidence(tmp_path: Path):
    payload = {
        "schema": "RICKETTS_MANDIBLE_SPECIALIST_DATASET_V1",
        "landmarks": list(LANDMARKS),
        "license_verified": True,
        "clinician_annotation_verified": True,
        "patient_split_provenance": "patient-level immutable split manifest",
    }
    (tmp_path / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit, match="REAL_DATASET_DEIDENTIFICATION_EVIDENCE_REQUIRED"):
        validate_real_dataset_contract(tmp_path)
