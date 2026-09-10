"""Integration contract for CephaloService's fail-closed scientific boundary.

Age and sex are still read from the real patient for API compatibility, but the
runtime cephalometric engine must not turn them into local norms, cohorts,
diagnosis, growth projections, or treatment recommendations.
"""
from datetime import datetime

from backend import models
from backend.services.cephalo_service import CephaloService
from backend.services import cephalo_service as cephalo_service_module
from backend.services import calibration_service as calibration_service_module


def _make_patient(db, dentiste, date_naissance, sexe, nom="CEPHCTX"):
    patient = models.Patient(
        nom=nom,
        prenom="Test",
        date_naissance=date_naissance,
        sexe=sexe,
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


_FAKE_LANDMARKS = [
    {"id": "S", "x": 50.0, "y": 60.0},
    {"id": "N", "x": 70.0, "y": 40.0},
    {"id": "A", "x": 90.0, "y": 90.0},
    {"id": "B", "x": 85.0, "y": 130.0},
    {"id": "Prn", "x": 100.0, "y": 40.0},
    {"id": "Pog_soft", "x": 100.0, "y": 200.0},
]


def _patch_vision_and_calibration(monkeypatch, ratio=0.5):
    monkeypatch.setattr(
        cephalo_service_module.vision_engine,
        "predict_landmarks",
        lambda file_path: {
            "landmarks": _FAKE_LANDMARKS,
            "mode_inference": "test_stub",
            "warning": None,
            "processing_time_ms": 1,
        },
    )
    monkeypatch.setattr(
        calibration_service_module.calibration_service,
        "detect_mm_per_pixel",
        lambda file_path: ratio,
    )


def _assert_fail_closed(results):
    assert results["analysis_metadata"]["cohort"] == "Non classé"
    assert results["ai_narrative"] == {}
    assert results["t1_projection"] == {}
    assert results["t2_projection"] == {}

    for group in results["metrics"].values():
        for measurement in group.values():
            assert measurement["norm_mean"] is None
            assert measurement["norm_min"] is None
            assert measurement["norm_max"] is None
            assert measurement["z_score"] is None
            assert measurement["status"] in {"N/A", "Missing"}


def test_process_new_radio_is_non_normative_for_real_patient_context(db, dentiste, monkeypatch):
    _patch_vision_and_calibration(monkeypatch)
    patient = _make_patient(db, dentiste, datetime(1985, 7, 20), "F", nom="ADULT")

    result = CephaloService(db).process_new_radio(
        patient.id,
        "fake_path.jpg",
        "fake_db_path",
    )

    _assert_fail_closed(result["results"])


def test_age_and_sex_do_not_create_different_normative_authority(db, dentiste, monkeypatch):
    _patch_vision_and_calibration(monkeypatch)
    adult = _make_patient(db, dentiste, datetime(1985, 7, 20), "M", nom="ADULT_CTX")
    young = _make_patient(db, dentiste, datetime(2017, 7, 20), "F", nom="YOUNG_CTX")
    service = CephaloService(db)

    adult_results = service.process_new_radio(adult.id, "adult.jpg", "adult_db")["results"]
    young_results = service.process_new_radio(young.id, "young.jpg", "young_db")["results"]

    _assert_fail_closed(adult_results)
    _assert_fail_closed(young_results)
    assert adult_results["analysis_metadata"] == young_results["analysis_metadata"]
    assert adult_results["metrics"] == young_results["metrics"]


def test_refine_analysis_remains_fail_closed(db, dentiste, monkeypatch):
    _patch_vision_and_calibration(monkeypatch)
    patient = _make_patient(db, dentiste, datetime(2017, 7, 20), "F", nom="REFINE")
    service = CephaloService(db)
    created = service.process_new_radio(patient.id, "fake_path.jpg", "fake_db_path")

    refined = service.refine_analysis(
        created["analysis_id"],
        [{"id": lm["id"], "x": lm["x"], "y": lm["y"]} for lm in _FAKE_LANDMARKS],
        clinician_id=str(dentiste.id),
    )

    _assert_fail_closed(refined["results"])
    assert "Aucune stratégie thérapeutique n'est générée automatiquement" in refined["ai_diagnostic"]["strategie_therapeutique"]


def test_unrecognized_sex_code_does_not_invent_context(db, dentiste, monkeypatch):
    _patch_vision_and_calibration(monkeypatch)
    patient = _make_patient(db, dentiste, datetime(1985, 7, 20), "AUTRE", nom="UNKNOWN")

    result = CephaloService(db).process_new_radio(
        patient.id,
        "fake_path.jpg",
        "fake_db_path",
    )

    _assert_fail_closed(result["results"])
