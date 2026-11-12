"""Disposable synthetic Cephalo study for authenticated GUI→SQLite regression only.

This module refuses non-T2 state, never creates a clinical case, and does not
use patient radiographs, model inference, calibration measurements or diagnosis.
"""
import copy
import json
import os
from datetime import datetime
from pathlib import Path

assert os.environ.get("ENVIRONMENT") == "test", "T2 test flag required"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1", "Isolated T2 required"
assert os.environ.get("DATABASE_URL") == "sqlite:///./t2-runtime-cert.db", "Disposable DB path required"
assert Path("t2-runtime-cert.db").is_file(), "Disposable DB must exist"
assert os.environ.get("CLOUD_AI_ENABLED") == "false", "External AI prohibited"

from backend import database, models

with database.SessionLocal() as db:
    user = db.query(models.User).filter_by(email="t2-browser@cabinet.ma").one()
    source_patient = db.query(models.Patient).filter_by(numero_dossier="T2-0001", employer_id=user.id).one()
    source = db.query(models.CephaloAnalysis).filter_by(patient_id=source_patient.id).one()
    # Coordinates are already deterministic synthetic *test fixture* data;
    # they are not a model result, anatomical ground truth or calibration proof.
    landmarks = copy.deepcopy(source.landmarks_data)
    assert isinstance(landmarks, list) and len(landmarks) == 38
    assert len({item["id"] for item in landmarks}) == 38
    assert all(type(item["x"]) in (int, float) and type(item["y"]) in (int, float) for item in landmarks)
    assert source.image_original_path == "api/static/uploads/radios/t2-cephalo-seeded.png"
    assert Path("backend/static/uploads/radios/t2-cephalo-seeded.png").is_file()

    case_number = "T2-CEPH-ODF-E2E-01"
    assert not db.query(models.Patient).filter_by(numero_dossier=case_number).first(), "Reuse forbidden"
    patient = models.Patient(
        numero_dossier=case_number,
        nom="FICTION-ODF", prenom="E2E",
        date_naissance=datetime(1990, 1, 1), sexe="M", employer_id=user.id,
        telephone="0600000000", email="ceph-odf-synthetic@example.com",
        assurance="AUCUNE",
        antecedents_medicaux="ALERTE SYNTHETIQUE D'ESSAI — AUCUNE DONNEE CLINIQUE REELLE",
    )
    # The real patient serializer uses EmailStr; a reserved .invalid suffix
    # fails validation even for a synthetic patient and obscures the E2E result.
    from email_validator import validate_email
    validate_email(patient.email, check_deliverability=False)
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=True))
    study = models.CephaloAnalysis(
        patient_id=patient.id,
        image_original_path=source.image_original_path,
        landmarks_data=landmarks,
        angles_data={
            "vision_metadata": {"mode_inference": "SYNTHETIC_COORDINATES_NO_MODEL"},
            "calibration_status": "unverified",
        },
        calibration_data=None, mm_per_pixel=None, is_calibrated=False,
    )
    db.add(study)
    db.commit()
    db.refresh(study)
    assert study.mm_per_pixel is None and study.is_calibrated is False
    print("CEPH_ODF_GUI_SQLITE_SEED=" + json.dumps({
        "patient_id": patient.id, "analysis_id": study.id,
        "clinical_release": False, "original_landmarks": landmarks,
        "fixture_name": case_number,
    }, separators=(",", ":")), flush=True)
