"""Tests for services/clinical_intelligence.py fail-closed patient summary."""
import json
from datetime import datetime, timedelta

from backend import models
from backend.services.clinical_intelligence import (
    ClinicalIntelligenceService,
    MOTIF_CATALOG,
    _resolve_motifs,
)


def _make_patient(db, dentiste, nom="CLINPAT", motif=None, antecedents=None):
    pat = models.Patient(
        nom=nom,
        prenom="Test",
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
        assert any(v["urgency"] == "urgence" for v in MOTIF_CATALOG.values())

    def test_has_planifie_motifs(self):
        assert any(v["urgency"] == "planifié" for v in MOTIF_CATALOG.values())

    def test_all_motifs_have_label_and_specialties(self):
        for val in MOTIF_CATALOG.values():
            assert val.get("label")
            assert val.get("specialties")

    def test_non_ortho_motifs_keep_acts(self):
        for val in MOTIF_CATALOG.values():
            if "ORTHODONTIE" in val.get("specialties", []):
                continue
            assert val.get("acts")

    def test_ortho_motifs_do_not_require_acts(self):
        ortho = [v for v in MOTIF_CATALOG.values() if "ORTHODONTIE" in v.get("specialties", [])]
        assert ortho
        assert any("acts" not in val for val in ortho)


class TestGetPatientSummary:
    def setup_method(self):
        self.service = ClinicalIntelligenceService()

    def test_nonexistent_patient_returns_empty(self, db, dentiste):
        assert self.service.get_patient_summary(db, 999999) == {}

    def test_new_patient_returns_structure(self, db, dentiste):
        pat = _make_patient(db, dentiste, "CLINSUM")
        result = self.service.get_patient_summary(db, pat.id)
        for key in (
            "last_visit",
            "clinical_summary",
            "alerts",
            "risk_level",
            "motif_specialties",
            "motif_treatment_hints",
        ):
            assert key in result

    def test_no_visits_last_visit_is_none(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NOVISIT")
        assert self.service.get_patient_summary(db, pat.id)["last_visit"] is None

    def test_dossier_vierge_clinical_summary(self, db, dentiste):
        pat = _make_patient(db, dentiste, "VIERGE")
        assert "Dossier vierge" in self.service.get_patient_summary(db, pat.id)["clinical_summary"]

    def test_antecedents_included_in_summary(self, db, dentiste):
        pat = _make_patient(db, dentiste, "ANTEC", antecedents="Diabète type 2")
        assert "Diabète type 2" in self.service.get_patient_summary(db, pat.id)["clinical_summary"]

    def test_diabete_generates_alert(self, db, dentiste):
        pat = _make_patient(db, dentiste, "DIABET", antecedents="diabète contrôlé")
        result = self.service.get_patient_summary(db, pat.id)
        assert any("diabète" in alert.lower() for alert in result["alerts"])

    def test_high_risk_when_medical_alert(self, db, dentiste):
        pat = _make_patient(db, dentiste, "HIGHRISK", antecedents="diabète sévère")
        assert self.service.get_patient_summary(db, pat.id)["risk_level"] == "high"

    def test_non_ortho_motif_keeps_catalog_hint(self, db, dentiste):
        pat = _make_patient(db, dentiste, "MOTIF", motif=json.dumps(["carie"]))
        result = self.service.get_patient_summary(db, pat.id)
        assert "Carie dentaire" in result["clinical_summary"]
        assert result["motif_treatment_hints"]

    def test_ortho_motif_is_routing_only(self, db, dentiste):
        pat = _make_patient(db, dentiste, "ORTHOROUTE", motif=json.dumps(["malocclusion"]))
        result = self.service.get_patient_summary(db, pat.id)
        assert "ORTHODONTIE" in result["motif_specialties"]
        assert result["motif_treatment_hints"] == []

    def test_mixed_ortho_motif_does_not_generate_act_hint(self, db, dentiste):
        pat = _make_patient(db, dentiste, "DIASTEME", motif=json.dumps(["diasteme"]))
        result = self.service.get_patient_summary(db, pat.id)
        assert "ORTHODONTIE" in result["motif_specialties"]
        assert result["motif_treatment_hints"] == []

    def test_urgent_motif_creates_alert(self, db, dentiste):
        pat = _make_patient(db, dentiste, "URGENT", motif=json.dumps(["abces"]))
        result = self.service.get_patient_summary(db, pat.id)
        assert any("urgence" in alert.lower() for alert in result["alerts"])

    def test_acts_last_90d_count(self, db, dentiste):
        pat = _make_patient(db, dentiste, "ACTS90")
        db.add(
            models.Acte(
                patient_id=pat.id,
                praticien_id=dentiste.id,
                libelle="Composite",
                type_acte=models.ActeType.SOIN,
                montant=400.0,
                date_debut=datetime.now() - timedelta(days=10),
            )
        )
        db.commit()
        assert self.service.get_patient_summary(db, pat.id)["acts_last_90d"] == 1

    def test_next_visit_is_none_when_no_upcoming_appointments(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NEXTV")
        assert self.service.get_patient_summary(db, pat.id)["next_visit"] is None

    def test_cephalo_trend_insufficient_data(self, db, dentiste):
        pat = _make_patient(db, dentiste, "CEPHT")
        assert self.service.get_patient_summary(db, pat.id)["cephalo_trend"] == "données insuffisantes"

    def test_risk_level_is_valid_value(self, db, dentiste):
        pat = _make_patient(db, dentiste, "RISKVAL")
        assert self.service.get_patient_summary(db, pat.id)["risk_level"] in ("low", "moderate", "high")


class TestGetFullDiagnostic:
    def setup_method(self):
        self.service = ClinicalIntelligenceService()

    def test_nonexistent_patient_is_fail_closed(self, db):
        result = self.service.get_full_diagnostic(db, 999999)
        assert result["source"] == "raw_clinical_data"
        assert result["confidence"] is None
        assert result["requires_validation"] is True
        assert "introuvable" in result["report"].lower()

    def test_no_cephalo_data_is_fail_closed(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NOCEPH")
        result = self.service.get_full_diagnostic(db, pat.id)
        assert result["source"] == "raw_clinical_data"
        assert result["confidence"] is None
        assert result["requires_validation"] is True
        assert "aucun diagnostic" in result["report"].lower()

    def test_with_cephalo_data_reports_raw_values_only(self, db, dentiste):
        pat = _make_patient(db, dentiste, "WITHCEPH")
        angles_data = {
            "analyse_osseuse": {
                "SNA": {
                    "valeur": 82.0,
                    "status": "Legacy status must be ignored",
                    "norm_mean": 82.0,
                    "norm_min": 79.0,
                    "norm_max": 85.0,
                    "z_score": 0.0,
                    "interpretation": "Legacy interpretation must be ignored",
                }
            }
        }
        db.add(
            models.CephaloAnalysis(
                patient_id=pat.id,
                image_original_path="api/static/uploads/radios/test.jpg",
                angles_data=angles_data,
                mm_per_pixel=0.2,
                is_calibrated=True,
            )
        )
        db.commit()

        result = self.service.get_full_diagnostic(db, pat.id)
        report = result["report"]
        assert result["source"] == "raw_clinical_data"
        assert result["confidence"] is None
        assert result["requires_validation"] is True
        assert "SNA = 82.0" in report
        assert "Legacy status" not in report
        assert "Legacy interpretation" not in report
        assert "aucune norme locale" in report.lower()
        assert "stratégie thérapeutique" in report.lower()


class TestCalculateAge:
    def test_age_calculation(self):
        service = ClinicalIntelligenceService()
        born = datetime(1990, 1, 1)
        age = service._calculate_age(born)
        assert age >= 35

    def test_age_child(self):
        service = ClinicalIntelligenceService()
        born = datetime(2015, 6, 1)
        age = service._calculate_age(born)
        assert age < 15
