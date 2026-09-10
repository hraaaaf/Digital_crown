"""
Tests d'intégration du statut de calibration dans le pipeline céphalo.

Invariant scientifique: une détection automatique de réglette est seulement un
candidat image-space. Elle ne rend jamais l'analyse calibrée sans la transition
auditable de validation praticien.
"""
from datetime import datetime

import pytest

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


_FAKE_LANDMARKS = [
    {"id": "S", "x": 50.0, "y": 60.0},
    {"id": "N", "x": 70.0, "y": 40.0},
    {"id": "A", "x": 90.0, "y": 90.0},
    {"id": "B", "x": 85.0, "y": 130.0},
    {"id": "Prn", "x": 100.0, "y": 40.0},
    {"id": "Pog_soft", "x": 100.0, "y": 200.0},
]

_FAKE_RULER_CANDIDATE = {
    "method": "RULER_TICK_CANDIDATE_V1",
    "p1": [620.0, 55.0],
    "p2": [620.0, 80.0],
    "distance_px": 25.0,
    "tick_count": 6,
    "spacing_regularity": 1.0,
    "requires_clinician_validation": True,
}


def _fake_vision_result():
    return {
        "landmarks": _FAKE_LANDMARKS,
        "mode_inference": "test_stub",
        "warning": None,
        "processing_time_ms": 1,
    }


def _patch_vision(monkeypatch):
    monkeypatch.setattr(
        cephalo_service_module.vision_engine,
        "predict_landmarks",
        lambda file_path: _fake_vision_result(),
    )


class TestCalibrationStatusOnNewRadio:
    def test_unverified_when_no_ruler_candidate(self, db, dentiste, monkeypatch):
        pat = _make_patient(db, dentiste)
        _patch_vision(monkeypatch)
        monkeypatch.setattr(
            calibration_service_module.calibration_service,
            "detect_ruler_candidate",
            lambda file_path: None,
        )

        result = CephaloService(db).process_new_radio(
            pat.id, "fake_path.jpg", "fake_db_path"
        )

        assert result["results"]["calibration_status"] == "unverified"
        assert result["is_calibrated"] is False
        assert result["calibration_candidate"] is None
        assert result["results"]["metrics"]["analyse_osseuse"]["SNA"]["valeur"] is not None
        assert result["mm_per_pixel"] is None
        assert result["results"]["analysis_metadata"]["pixel_ratio"] is None
        assert result["results"]["metrics"]["analyse_dentaire"]["Surplomb"]["valeur"] is None

    def test_ruler_candidate_remains_unverified_until_clinician_validation(
        self, db, dentiste, monkeypatch
    ):
        pat = _make_patient(db, dentiste, nom="CEPHCAL_CANDIDATE")
        _patch_vision(monkeypatch)
        monkeypatch.setattr(
            calibration_service_module.calibration_service,
            "detect_ruler_candidate",
            lambda file_path: dict(_FAKE_RULER_CANDIDATE),
        )

        result = CephaloService(db).process_new_radio(
            pat.id, "fake_path.jpg", "fake_db_path"
        )

        assert result["results"]["calibration_status"] == "unverified"
        assert result["is_calibrated"] is False
        assert result["mm_per_pixel"] is None
        assert result["results"]["analysis_metadata"]["pixel_ratio"] is None
        assert result["calibration_candidate"] == _FAKE_RULER_CANDIDATE
        assert result["calibration_candidate"]["requires_clinician_validation"] is True


class TestCalibrationStatusPersistedOnRefine:
    def test_ruler_candidate_refine_stays_unverified_without_calibration_transition(
        self, db, dentiste, monkeypatch
    ):
        pat = _make_patient(db, dentiste, nom="CEPHCAL_REFINE")
        _patch_vision(monkeypatch)
        monkeypatch.setattr(
            calibration_service_module.calibration_service,
            "detect_ruler_candidate",
            lambda file_path: dict(_FAKE_RULER_CANDIDATE),
        )
        service = CephaloService(db)
        created = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        refined = service.refine_analysis(
            created["analysis_id"],
            [{"id": lm["id"], "x": lm["x"], "y": lm["y"]} for lm in _FAKE_LANDMARKS],
            clinician_id=str(dentiste.id),
        )

        assert refined["results"]["calibration_status"] == "unverified"
        assert refined["is_calibrated"] is False
        assert refined["mm_per_pixel"] is None
        assert refined["results"]["analysis_metadata"]["pixel_ratio"] is None

    def test_explicit_refine_ratio_is_rejected_for_typed_case(self, db, dentiste, monkeypatch):
        pat = _make_patient(db, dentiste, nom="CEPHCAL_EXPLICIT")
        _patch_vision(monkeypatch)
        monkeypatch.setattr(
            calibration_service_module.calibration_service,
            "detect_ruler_candidate",
            lambda file_path: None,
        )
        service = CephaloService(db)
        created = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        with pytest.raises(ValueError, match="endpoint de calibration"):
            service.refine_analysis(
                created["analysis_id"],
                [{"id": lm["id"], "x": lm["x"], "y": lm["y"]} for lm in _FAKE_LANDMARKS],
                mm_per_pixel=0.250,
                clinician_id=str(dentiste.id),
            )

    def test_uncalibrated_refine_does_not_become_verified(self, db, dentiste, monkeypatch):
        pat = _make_patient(db, dentiste, nom="CEPHCAL_UNVERIFIED")
        _patch_vision(monkeypatch)
        monkeypatch.setattr(
            calibration_service_module.calibration_service,
            "detect_ruler_candidate",
            lambda file_path: None,
        )
        service = CephaloService(db)
        created = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        refined = service.refine_analysis(
            created["analysis_id"],
            [{"id": lm["id"], "x": lm["x"], "y": lm["y"]} for lm in _FAKE_LANDMARKS],
            clinician_id=str(dentiste.id),
        )

        assert refined["is_calibrated"] is False
        assert refined["results"]["calibration_status"] == "unverified"
