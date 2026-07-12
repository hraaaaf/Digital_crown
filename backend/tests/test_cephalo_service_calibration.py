"""
Tests d'intégration pour l'injection de `calibration_status` dans le pipeline céphalo
(bug audit fonctionnel 2026-07-12 : ratio mm/px par défaut 0.1 utilisé silencieusement
quand l'auto-calibration échoue, sans jamais avertir le praticien). Fixtures `db`/
`dentiste` de conftest.py.
Exécuter avec : pytest backend/tests/test_cephalo_service_calibration.py -v
"""
from datetime import datetime

from backend import models
from backend.services.cephalo_service import CephaloService
from backend.services import cephalo_service as cephalo_service_module
from backend.services import calibration_service as calibration_service_module


def _make_patient(db, dentiste, nom="CEPHCAL"):
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1985, 7, 20),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


# Landmarks minimaux mais suffisants pour que SNA/SNB/ANB se calculent (angles
# présents non-None), avec l'id "id" attendu par vision_result["landmarks"].
_FAKE_LANDMARKS = [
    {"id": "S", "x": 50.0, "y": 60.0},
    {"id": "N", "x": 70.0, "y": 40.0},
    {"id": "A", "x": 90.0, "y": 90.0},
    {"id": "B", "x": 85.0, "y": 130.0},
    {"id": "Prn", "x": 100.0, "y": 40.0},
    {"id": "Pog_soft", "x": 100.0, "y": 200.0},
]


def _fake_vision_result():
    return {
        "landmarks": _FAKE_LANDMARKS,
        "mode_inference": "test_stub",
        "warning": None,
        "processing_time_ms": 1,
    }


class TestCalibrationStatusOnNewRadio:
    def test_unverified_when_auto_calibration_fails(self, db, dentiste, monkeypatch):
        pat = _make_patient(db, dentiste)
        monkeypatch.setattr(
            cephalo_service_module.vision_engine, "predict_landmarks",
            lambda file_path: _fake_vision_result(),
        )
        monkeypatch.setattr(
            calibration_service_module.calibration_service, "detect_mm_per_pixel",
            lambda file_path: None,
        )

        service = CephaloService(db)
        result = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        assert result["results"]["calibration_status"] == "unverified"
        assert result["is_calibrated"] is False
        assert result["results"]["metrics"]["analyse_osseuse"]["SNA"]["valeur"] is not None

    def test_verified_when_auto_calibration_succeeds(self, db, dentiste, monkeypatch):
        pat = _make_patient(db, dentiste)
        monkeypatch.setattr(
            cephalo_service_module.vision_engine, "predict_landmarks",
            lambda file_path: _fake_vision_result(),
        )
        monkeypatch.setattr(
            calibration_service_module.calibration_service, "detect_mm_per_pixel",
            lambda file_path: 0.11,
        )

        service = CephaloService(db)
        result = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        assert result["results"]["calibration_status"] == "verified"
        assert result["is_calibrated"] is True


class TestCalibrationStatusPersistedOnRefine:
    def test_refine_preserves_verified_status(self, db, dentiste, monkeypatch):
        pat = _make_patient(db, dentiste)
        monkeypatch.setattr(
            cephalo_service_module.vision_engine, "predict_landmarks",
            lambda file_path: _fake_vision_result(),
        )
        monkeypatch.setattr(
            calibration_service_module.calibration_service, "detect_mm_per_pixel",
            lambda file_path: 0.11,
        )
        service = CephaloService(db)
        created = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")
        analysis_id = created["analysis_id"]

        # Auto-save (refine_analysis) sans repasser par la calibration — le statut doit
        # être réinjecté depuis is_calibrated persisté, pas retomber à "unverified".
        landmarks = [
            {"id": lm["id"], "x": lm["x"], "y": lm["y"]} for lm in _FAKE_LANDMARKS
        ]
        refined = service.refine_analysis(analysis_id, landmarks, mm_per_pixel=0.11)

        assert refined["results"]["calibration_status"] == "verified"
