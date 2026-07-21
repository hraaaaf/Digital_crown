"""Tests for services/clinical_intelligence.py — DB-based patient summary."""
import pytest
import json
from datetime import datetime, timedelta
from backend import models
from backend.services.clinical_intelligence import ClinicalIntelligenceService, _resolve_motifs, MOTIF_CATALOG


def _make_patient(db, dentiste, nom="CLINPAT", motif=None, antecedents=None):
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1985, 3, 10),
        sexe="M",
        employer_id=dentiste.id,
        motif_consultation=motif,
        antecedents_medicaux=antecedents,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


class TestResolveMotifs:
    def test_empty_returns_empty(self):
        assert _resolve_motifs(None) == []
        assert _resolve_motifs("") == []

    def test_valid_json_array_resolves(self):
        motifs = _resolve_motifs(json.dumps(["carie", "tartre_important"]))
        assert len(motifs) == 2
        assert any(m["label"] == "Carie dentaire" for m in motifs)

    def test_unknown_ids_skipped(self):
        motifs = _resolve_motifs(json.dumps(["carie", "nonexistent_motif"]))
        assert len(motifs) == 1

    def test_invalid_json_returns_empty(self):
        assert _resolve_motifs("not json") == []

    def test_non_list_json_returns_empty(self):
        assert _resolve_motifs('{"key": "value"}') == []


class TestMotifCatalog:
    def test_has_urgence_motifs(self):
        urgent = [k for k, v in MOTIF_CATALOG.items() if v["urgency"] == "urgence"]
        assert len(urgent) > 0

    def test_has_planifie_motifs(self):
        planifie = [k for k, v in MOTIF_CATALOG.items() if v["urgency"] == "planifié"]
        assert len(planifie) > 0

    def test_all_motifs_have_label(self):
        for key, val in MOTIF_CATALOG.items():
            assert "label" in val

    def test_all_motifs_have_acts(self):
        for key, val in MOTIF_CATALOG.items():
            assert "acts" in val
            assert len(val["acts"]) > 0


class TestGetPatientSummary:
    def setup_method(self):
        self.service = ClinicalIntelligenceService()

    def test_nonexistent_patient_returns_empty(self, db, dentiste):
        result = self.service.get_patient_summary(db, 999999)
        assert result == {}

    def test_new_patient_returns_structure(self, db, dentiste):
        pat = _make_patient(db, dentiste, "CLINSUM")
        result = self.service.get_patient_summary(db, pat.id)
        for key in ("last_visit", "clinical_summary", "alerts", "risk_level"):
            assert key in result

    def test_no_visits_last_visit_is_none(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NOVISIT")
        result = self.service.get_patient_summary(db, pat.id)
        assert result["last_visit"] is None

    def test_dossier_vierge_clinical_summary(self, db, dentiste):
        pat = _make_patient(db, dentiste, "VIERGE")
        result = self.service.get_patient_summary(db, pat.id)
        assert "Dossier vierge" in result["clinical_summary"]

    def test_antecedents_included_in_summary(self, db, dentiste):
        pat = _make_patient(db, dentiste, "ANTEC", antecedents="Diabète type 2")
        result = self.service.get_patient_summary(db, pat.id)
        assert "Diabète type 2" in result["clinical_summary"]

    def test_diabete_generates_alert(self, db, dentiste):
        pat = _make_patient(db, dentiste, "DIABET", antecedents="diabète contrôlé")
        result = self.service.get_patient_summary(db, pat.id)
        assert any("Alerte Médicale" in a or "diabète" in a.lower() for a in result["alerts"])

    def test_high_risk_when_medical_alert(self, db, dentiste):
        pat = _make_patient(db, dentiste, "HIGHRISK", antecedents="diabète sévère")
        result = self.service.get_patient_summary(db, pat.id)
        assert result["risk_level"] in ("moderate", "high")

    def test_motif_consultation_resolved(self, db, dentiste):
        pat = _make_patient(db, dentiste, "MOTIF", motif=json.dumps(["carie"]))
        result = self.service.get_patient_summary(db, pat.id)
        assert "Carie" in result["clinical_summary"] or len(result.get("motif_treatment_hints", [])) > 0

    def test_urgent_motif_creates_alert(self, db, dentiste):
        pat = _make_patient(db, dentiste, "URGENT", motif=json.dumps(["abces"]))
        result = self.service.get_patient_summary(db, pat.id)
        assert any("Urgence" in a or "urgence" in a.lower() for a in result["alerts"])

    def test_acts_last_90d_count(self, db, dentiste):
        pat = _make_patient(db, dentiste, "ACTS90")
        # Add a recent acte
        acte = models.Acte(
            patient_id=pat.id,
            praticien_id=dentiste.id,
            libelle="Composite",
            type_acte=models.ActeType.SOIN,
            montant=400.0,
            date_debut=datetime.now() - timedelta(days=10),
        )
        db.add(acte)
        db.commit()
        result = self.service.get_patient_summary(db, pat.id)
        assert result["acts_last_90d"] == 1

    def test_next_visit_is_none_when_no_upcoming_appointments(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NEXTV")
        result = self.service.get_patient_summary(db, pat.id)
        assert result["next_visit"] is None

    def test_cephalo_trend_insufficient_data(self, db, dentiste):
        pat = _make_patient(db, dentiste, "CEPHT")
        result = self.service.get_patient_summary(db, pat.id)
        assert result["cephalo_trend"] == "données insuffisantes"

    def test_risk_level_is_valid_value(self, db, dentiste):
        pat = _make_patient(db, dentiste, "RISKVAL")
        result = self.service.get_patient_summary(db, pat.id)
        assert result["risk_level"] in ("low", "moderate", "high")


class TestGetFullDiagnostic:
    def setup_method(self):
        self.service = ClinicalIntelligenceService()

    def test_nonexistent_patient_returns_error(self, db):
        result = self.service.get_full_diagnostic(db, 999999)
        assert "rapport" in result.get("report", "").lower() or "introuvable" in str(result).lower() or "report" in result

    def test_no_cephalo_data_returns_heuristic(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NOCEPH")
        result = self.service.get_full_diagnostic(db, pat.id)
        assert "report" in result
        assert result.get("source") == "heuristic"

    def test_with_cephalo_data_generates_report(self, db, dentiste):
        pat = _make_patient(db, dentiste, "WITHCEPH")
        angles_data = {
            "analyse_osseuse": {
                "Decalage_A_B": {"valeur": 2.3, "status": "Normal", "norm_mean": 2.3, "norm_min": 0.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Angle_de_Tweed": {"valeur": 26.0, "status": "Normal", "norm_mean": 26.0, "norm_min": 20.0, "norm_max": 32.0, "z_score": 0.0, "interpretation": "Normal"},
                "Situation_A": {"valeur": 2.3, "status": "Normal", "norm_mean": 2.3, "norm_min": -1.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Situation_B": {"valeur": 0.0, "status": "Normal", "norm_mean": 0.0, "norm_min": -5.0, "norm_max": 5.0, "z_score": 0.0, "interpretation": "Normal"},
                "Profondeur_Faciale": {"valeur": 87.0, "status": "Normal", "norm_mean": 87.0, "norm_min": 82.0, "norm_max": 92.0, "z_score": 0.0, "interpretation": "Normal"},
                "SNA": {"valeur": 82.0, "status": "Normal", "norm_mean": 82.0, "norm_min": 79.0, "norm_max": 85.0, "z_score": 0.0, "interpretation": "Normal"},
                "SNB": {"valeur": 80.0, "status": "Normal", "norm_mean": 80.0, "norm_min": 77.0, "norm_max": 83.0, "z_score": 0.0, "interpretation": "Normal"},
                "ANB": {"valeur": 2.0, "status": "Normal", "norm_mean": 2.0, "norm_min": 0.0, "norm_max": 4.0, "z_score": 0.0, "interpretation": "Normal"},
            },
            "analyse_dentaire": {
                "IMPA": {"valeur": 90.0, "status": "Normal", "norm_mean": 90.0, "norm_min": 83.0, "norm_max": 97.0, "z_score": 0.0, "interpretation": "Normal"},
                "I_Francfort": {"valeur": 107.0, "status": "Normal", "norm_mean": 107.0, "norm_min": 100.0, "norm_max": 114.0, "z_score": 0.0, "interpretation": "Normal"},
                "Surplomb": {"valeur": 2.5, "status": "Normal", "norm_mean": 2.5, "norm_min": 1.0, "norm_max": 4.0, "z_score": 0.0, "interpretation": "Normal"},
                "Recouvrement": {"valeur": 2.5, "status": "Normal", "norm_mean": 2.5, "norm_min": 1.0, "norm_max": 4.0, "z_score": 0.0, "interpretation": "Normal"},
                "Inter_Incisif": {"valeur": 130.0, "status": "Normal", "norm_mean": 130.0, "norm_min": 125.0, "norm_max": 135.0, "z_score": 0.0, "interpretation": "Normal"},
            },
            "analyse_esthetique": {
                "Ligne_E_Ls": {"valeur": -2.0, "status": "Normal", "norm_mean": -2.0, "norm_min": -5.0, "norm_max": 1.0, "z_score": 0.0, "interpretation": "Normal"},
                "Ligne_E_Li": {"valeur": 0.0, "status": "Normal", "norm_mean": 0.0, "norm_min": -3.0, "norm_max": 3.0, "z_score": 0.0, "interpretation": "Normal"},
                "Angle_Nasolabial": {"valeur": 102.0, "status": "Normal", "norm_mean": 102.0, "norm_min": 95.0, "norm_max": 110.0, "z_score": 0.0, "interpretation": "Normal"},
            },
        }
        cephalo = models.CephaloAnalysis(
            patient_id=pat.id,
            image_original_path="api/static/uploads/radios/test.jpg",
            angles_data=angles_data,
            mm_per_pixel=0.2,
            is_calibrated=True,
        )
        db.add(cephalo)
        db.commit()

        result = self.service.get_full_diagnostic(db, pat.id)
        assert "report" in result
        assert len(result["report"]) > 100

    def test_patient_age_and_sex_reach_ai_advisor(self, db, dentiste, monkeypatch):
        # CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C:
        # get_full_diagnostic already computes numeric age (self._calculate_age)
        # but never threaded it (or sex) into ai_advisor.generate_diagnostic —
        # same plumbing-gap class as CEPHALOMETRY-NORMATIVE-CONTEXT-PLUMBING-4A2's
        # cephalo_service.py fix. This proves the real patient's age/sex now reach it.
        import backend.services.clinical_intelligence as ci_module
        captured = {}
        original = ci_module.ai_advisor.generate_diagnostic

        def _spy(result, use_slm=False, age=None, sex=None):
            captured["age"] = age
            captured["sex"] = sex
            return original(result, use_slm=use_slm, age=age, sex=sex)

        monkeypatch.setattr(ci_module.ai_advisor, "generate_diagnostic", _spy)

        pat = _make_patient(db, dentiste, "AGESEX")
        cephalo = models.CephaloAnalysis(
            patient_id=pat.id,
            image_original_path="api/static/uploads/radios/test.jpg",
            angles_data={"analyse_osseuse": {}, "analyse_dentaire": {}, "analyse_esthetique": {}},
            mm_per_pixel=0.2,
            is_calibrated=True,
        )
        db.add(cephalo)
        db.commit()

        self.service.get_full_diagnostic(db, pat.id)
        assert captured["age"] == self.service._calculate_age(pat.date_naissance)
        assert captured["sex"] == pat.sexe == "M"


class TestCalculateAge:
    def test_age_calculation(self):
        service = ClinicalIntelligenceService()
        born = datetime(1990, 1, 1)
        age = service._calculate_age(born)
        assert age >= 35  # 2026 - 1990

    def test_age_child(self):
        service = ClinicalIntelligenceService()
        born = datetime(2015, 6, 1)
        age = service._calculate_age(born)
        assert age < 15
