"""Independently verify authentic GUI edits from new SQLite sessions.

Requires disposable T2 and a successful synthetic browser proof. Never uses a
patient record, external clinical media, ONNX inference, or medical judgement.
"""
import json
import os
from pathlib import Path

assert os.environ.get("ENVIRONMENT") == "test"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.environ.get("DATABASE_URL") == "sqlite:///./t2-runtime-cert.db"
assert os.environ.get("CLOUD_AI_ENABLED") == "false"
assert Path("t2-runtime-cert.db").is_file(), "No isolated SQLite database"
report = json.loads(Path("artifacts/ceph-odf-gui-sqlite-e2e/report.json").read_text())
seed = json.loads(os.environ["CEPH_ODF_CASE_JSON"])
assert report["head"] == os.environ["PRODUCT_HEAD"]
assert report["final_status"] == "REAL_GUI_FASTAPI_SQLITE_DRAG_UNDO_REDO_RELOAD_PASS_SYNTHETIC_NONCLINICAL"
assert not report["errors"]
assert report["patient_synthetic"] is True and report["clinical_release"] is False
assert report["mm_scale_validated"] is False and report["scientific_norms_validated"] is False
assert report["real_image_used"] is False and report["model_inference_used"] is False
assert len(report["original_landmarks"]) == len(report["saved_landmarks"]) == 38
assert report["after_undo"] == report["original_landmarks"]
assert report["after_redo"] == report["saved_landmarks"]
assert report["put_responses"] and all(200 <= x["status"] < 300 for x in report["put_responses"])

from backend import database, models

with database.SessionLocal() as db:
    patient = db.get(models.Patient, seed["patient_id"])
    assert patient and patient.numero_dossier == "T2-CEPH-ODF-E2E-01"
    assert patient.employer_id is not None and patient.nom == "FICTION-ODF"
    study = db.get(models.CephaloAnalysis, seed["analysis_id"])
    assert study and study.patient_id == patient.id
    assert study.is_calibrated is False and study.mm_per_pixel is None
    assert study.calibration_data is None
    assert study.image_original_path == "api/static/uploads/radios/t2-cephalo-seeded.png"
    assert len(study.landmarks_data) == 38
    assert study.landmarks_data == report["saved_landmarks"]
    old = {point["id"]: point for point in report["original_landmarks"]}
    new = {point["id"]: point for point in study.landmarks_data}
    assert old.keys() == new.keys() and len(old) == 38
    changed = [key for key in old if abs(old[key]["x"]-new[key]["x"]) > 0.05
                                  or abs(old[key]["y"]-new[key]["y"]) > 0.05]
    assert changed == [report["changed_id"]], "Exactly one intended synthetic landmark may change"
    assert study.angles_data.get("calibration_status") != "verified", "No fabricated verified physical scale"
    assert study.angles_data.get("_cephalo_r14_final_decision_v1") is None, "No clinical finalisation"
    print("CEPH_ODF_REAL_GUI_FASTAPI_FRESH_SQLITE_RELOAD_PASS_SYNTHETIC_NONCLINICAL")
