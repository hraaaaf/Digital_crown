"""
Tests d'intégration pour CEPHALOMETRY-NORMATIVE-CONTEXT-PLUMBING-4A2 :
CephaloService charge désormais le Patient réel et thread age/sexe jusqu'à
CephaloEngine.calculate_metrics / BilanOrthoEngine.generate_bilan.

Bug corrigé (préexistant, indépendant du chantier normatif) : `age` n'était
jamais transmis dans le vrai chemin d'appel — `is_child` valait toujours
False et `cohort` toujours "Adulte", quel que soit l'âge réel du patient.

Fixtures `db`/`dentiste` de conftest.py, mêmes conventions que
test_cephalo_service_calibration.py.
Exécuter avec : pytest backend/tests/test_cephalo_service_normative_context.py -v
"""
from datetime import datetime

import pytest

from backend import models
from backend.services.cephalo_service import CephaloService
from backend.services import cephalo_service as cephalo_service_module
from backend.services import calibration_service as calibration_service_module
from backend.services import cephalo_engine as cephalo_engine_module
from backend.services import bilan_ortho_engine as bilan_ortho_engine_module


def _make_patient(db, dentiste, date_naissance, sexe, nom="CEPHCTX"):
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=date_naissance,
        sexe=sexe,
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


def _fake_vision_result():
    return {
        "landmarks": _FAKE_LANDMARKS,
        "mode_inference": "test_stub",
        "warning": None,
        "processing_time_ms": 1,
    }


def _patch_vision_and_calibration(monkeypatch, ratio=0.5):
    monkeypatch.setattr(
        cephalo_service_module.vision_engine, "predict_landmarks",
        lambda file_path: _fake_vision_result(),
    )
    monkeypatch.setattr(
        calibration_service_module.calibration_service, "detect_mm_per_pixel",
        lambda file_path: ratio,
    )


class TestAgeReachesTheEngine:
    """The pre-existing bug: age was never passed at all. This proves it now is."""

    def test_adult_patient_gets_adulte_cohort(self, db, dentiste, monkeypatch):
        _patch_vision_and_calibration(monkeypatch)
        pat = _make_patient(db, dentiste, datetime(1985, 7, 20), "M", nom="ADULT")
        service = CephaloService(db)
        result = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")
        assert result["results"]["analysis_metadata"]["cohort"] == "Adulte"

    def test_child_patient_gets_enfant_cohort(self, db, dentiste, monkeypatch):
        # Previously impossible: age was never passed, so cohort was ALWAYS "Adulte"
        # regardless of the patient's true age. A birth date making the patient 9
        # years old today must now correctly yield "Enfant".
        _patch_vision_and_calibration(monkeypatch)
        nine_years_ago = datetime.now().replace(year=datetime.now().year - 9)
        pat = _make_patient(db, dentiste, nine_years_ago, "F", nom="CHILD")
        service = CephaloService(db)
        result = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")
        assert "Enfant" in result["results"]["analysis_metadata"]["cohort"]

    def test_child_patient_gets_child_band_situation_a_norm(self, db, dentiste, monkeypatch):
        # Situation_A's norm depends on is_child (norm_sit_a differs child vs adult) —
        # confirms the age fix reaches all the way to CVM-dependent norm selection,
        # not just the cohort label.
        _patch_vision_and_calibration(monkeypatch)
        nine_years_ago = datetime.now().replace(year=datetime.now().year - 9)
        pat = _make_patient(db, dentiste, nine_years_ago, "F", nom="CHILD2")
        service = CephaloService(db)
        result = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")
        situation_a = result["results"]["metrics"]["analyse_osseuse"]["Situation_A"]
        # child norm_mean is 2.8 (adult would be 2.3) — see cephalo_engine.py norm_sit_a
        assert situation_a["norm_mean"] == 2.8

    def test_refine_analysis_also_receives_age(self, db, dentiste, monkeypatch):
        _patch_vision_and_calibration(monkeypatch)
        nine_years_ago = datetime.now().replace(year=datetime.now().year - 9)
        pat = _make_patient(db, dentiste, nine_years_ago, "F", nom="CHILD_REFINE")
        service = CephaloService(db)
        created = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        refined = service.refine_analysis(
            created["analysis_id"],
            [{"id": lm["id"], "x": lm["x"], "y": lm["y"]} for lm in _FAKE_LANDMARKS],
        )
        assert "Enfant" in refined["results"]["analysis_metadata"]["cohort"]


class TestSexReachesTheNormativeContext:
    def test_sex_captured_by_evaluate_measurement_via_process_new_radio(self, db, dentiste, monkeypatch):
        _patch_vision_and_calibration(monkeypatch)
        pat = _make_patient(db, dentiste, datetime(1985, 7, 20), "F", nom="SEXCTX")

        captured = {}
        original = cephalo_engine_module.evaluate_measurement

        def _spy(measurement_id, raw_value, definition_version, context):
            captured[measurement_id] = context
            return original(measurement_id, raw_value, definition_version, context)

        monkeypatch.setattr(cephalo_engine_module, "evaluate_measurement", _spy)

        service = CephaloService(db)
        service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        assert "ANB" in captured
        from backend.schemas.cephalo_normative import Sex
        assert captured["ANB"].sex == Sex.FEMALE
        assert captured["ANB"].population_id is None  # never invented

    def test_sex_captured_by_bilan_ortho_engine_via_refine_analysis(self, db, dentiste, monkeypatch):
        _patch_vision_and_calibration(monkeypatch)
        pat = _make_patient(db, dentiste, datetime(1990, 3, 15), "M", nom="SEXCTX_REFINE")
        service = CephaloService(db)
        created = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        captured = {}
        original = bilan_ortho_engine_module.evaluate_measurement

        def _spy(measurement_id, raw_value, definition_version, context):
            captured[measurement_id] = context
            return original(measurement_id, raw_value, definition_version, context)

        monkeypatch.setattr(bilan_ortho_engine_module, "evaluate_measurement", _spy)

        service.refine_analysis(
            created["analysis_id"],
            [{"id": lm["id"], "x": lm["x"], "y": lm["y"]} for lm in _FAKE_LANDMARKS],
        )

        assert "ANB" in captured
        from backend.schemas.cephalo_normative import Sex
        assert captured["ANB"].sex == Sex.MALE

    def test_unrecognized_sex_code_maps_to_none_not_guessed(self, db, dentiste, monkeypatch):
        _patch_vision_and_calibration(monkeypatch)
        pat = _make_patient(db, dentiste, datetime(1985, 7, 20), "AUTRE", nom="SEXUNKNOWN")

        captured = {}
        original = cephalo_engine_module.evaluate_measurement

        def _spy(measurement_id, raw_value, definition_version, context):
            captured[measurement_id] = context
            return original(measurement_id, raw_value, definition_version, context)

        monkeypatch.setattr(cephalo_engine_module, "evaluate_measurement", _spy)

        service = CephaloService(db)
        service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")

        assert captured["ANB"].sex is None


class TestStillNonAuthoritativeWithRealAgeAndSex:
    """Population remains permanently unavailable this phase — proves that even
    with realistic age/sex now supplied, SNA/SNB/ANB stay non-authoritative
    against the real registry (population_id=None still blocks every match).
    """

    def test_adult_patient_still_gets_no_skeletal_class(self, db, dentiste, monkeypatch):
        _patch_vision_and_calibration(monkeypatch)
        pat = _make_patient(db, dentiste, datetime(1985, 7, 20), "M", nom="STILLNONAUTH")
        service = CephaloService(db)
        result = service.process_new_radio(pat.id, "fake_path.jpg", "fake_db_path")
        narrative = result["results"]["ai_narrative"]["diagnostic_squelettique"]
        assert "Tendance squelettique de Classe" not in narrative
        assert "référence normative non validée" in narrative or "ANB" not in narrative
