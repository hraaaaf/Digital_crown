"""Tests services/habits_engine.py — HabitsEngine (MPL)."""
from datetime import datetime, timedelta
import pytest

from backend.services.habits_engine import HabitsEngine


@pytest.fixture()
def engine():
    return HabitsEngine()


# ── get_recommended_duration (pure function) ─────────────────────────────────

class TestGetRecommendedDuration:
    def test_endodontie_molaire(self, engine):
        assert engine.get_recommended_duration("Traitement Canal Molaire") == 60

    def test_endodontie_pluri(self, engine):
        assert engine.get_recommended_duration("Endo Pluri-radicul") == 60

    def test_endodontie_simple(self, engine):
        assert engine.get_recommended_duration("Traitement Canal") == 45

    def test_implant(self, engine):
        assert engine.get_recommended_duration("Pose Implant") == 90

    def test_chirurgie(self, engine):
        assert engine.get_recommended_duration("Chirurgie osseuse") == 60

    def test_extraction_sagesse(self, engine):
        assert engine.get_recommended_duration("Extraction Dent de Sagesse") == 45

    def test_extraction_simple(self, engine):
        assert engine.get_recommended_duration("Extraction simple") == 30

    def test_couronne(self, engine):
        assert engine.get_recommended_duration("Couronne céramo-métallique") == 45

    def test_composite(self, engine):
        assert engine.get_recommended_duration("Composite direct") == 30

    def test_detartrage(self, engine):
        assert engine.get_recommended_duration("Détartrage prophylaxie") == 30

    def test_consultation(self, engine):
        assert engine.get_recommended_duration("Consultation initiale") == 15

    def test_examen(self, engine):
        assert engine.get_recommended_duration("Examen bilan") == 15

    def test_unknown_defaults_to_30(self, engine):
        assert engine.get_recommended_duration("Acte inconnu") == 30

    def test_empty_defaults_to_30(self, engine):
        assert engine.get_recommended_duration("") == 30


# ── get_smart_bundles ─────────────────────────────────────────────────────────

class TestGetSmartBundles:
    def test_empty_db_returns_empty(self, engine, db, dentiste):
        result = engine.get_smart_bundles(db, dentiste.id, "Détartrage")
        assert result == []

    def test_returns_correlated_acts(self, engine, db, dentiste):
        from backend import models

        db.add(models.DoctorActCorrelation(
            doctor_id=dentiste.id, act_a="Détartrage", act_b="Composite", occurrence_count=5
        ))
        db.add(models.DoctorActCorrelation(
            doctor_id=dentiste.id, act_a="Détartrage", act_b="Couronne", occurrence_count=2
        ))
        db.commit()

        result = engine.get_smart_bundles(db, dentiste.id, "Détartrage")
        assert "Composite" in result
        assert "Couronne" in result
        # ordered by occurrence_count desc
        assert result[0] == "Composite"

    def test_max_3_results(self, engine, db, dentiste):
        from backend import models

        for i in range(5):
            db.add(models.DoctorActCorrelation(
                doctor_id=dentiste.id, act_a="Consultation",
                act_b=f"Acte{i}", occurrence_count=10 - i
            ))
        db.commit()

        result = engine.get_smart_bundles(db, dentiste.id, "Consultation")
        assert len(result) <= 3


# ── record_act_sequence ───────────────────────────────────────────────────────

class TestRecordActSequence:
    def test_no_error_when_single_acte(self, engine, db, dentiste):
        from backend import models

        pat = models.Patient(
            nom="SEQTEST", prenom="One",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        db.add(models.Acte(
            patient_id=pat.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN,
            libelle="Détartrage",
            montant=1000.0,
            statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now(),
        ))
        db.commit()

        # Only 1 act → should return early without creating correlation
        engine.record_act_sequence(db, dentiste.id, pat.id)
        count = db.query(models.DoctorActCorrelation).count()
        assert count == 0

    def test_creates_correlation_from_two_actes(self, engine, db, dentiste):
        from backend import models

        pat = models.Patient(
            nom="SEQTEST2", prenom="Two",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        db.add(models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN, libelle="Détartrage",
            montant=1000.0, statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now() - timedelta(days=1),
        ))
        db.add(models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN, libelle="Composite",
            montant=2000.0, statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now(),
        ))
        db.commit()

        engine.record_act_sequence(db, dentiste.id, pat.id)

        corr = db.query(models.DoctorActCorrelation).filter(
            models.DoctorActCorrelation.doctor_id == dentiste.id,
            models.DoctorActCorrelation.act_a == "Détartrage",
            models.DoctorActCorrelation.act_b == "Composite",
        ).first()
        assert corr is not None
        assert corr.occurrence_count == 1

    def test_increments_existing_correlation(self, engine, db, dentiste):
        from backend import models

        pat = models.Patient(
            nom="SEQTEST3", prenom="Inc",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        existing = models.DoctorActCorrelation(
            doctor_id=dentiste.id, act_a="Détartrage", act_b="Couronne", occurrence_count=3
        )
        db.add(existing)
        db.commit()

        db.add(models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN, libelle="Détartrage",
            montant=1000.0, statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now() - timedelta(days=1),
        ))
        db.add(models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.PROTHESE, libelle="Couronne",
            montant=5000.0, statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now(),
        ))
        db.commit()

        engine.record_act_sequence(db, dentiste.id, pat.id)

        db.refresh(existing)
        assert existing.occurrence_count == 4


# ── get_relevance_score ───────────────────────────────────────────────────────

class TestGetRelevanceScore:
    def test_unknown_drug_returns_low_score(self, engine, db, dentiste):
        score = engine.get_relevance_score(db, dentiste.id, "Détartrage", "Amoxicilline")
        assert score == 0.1

    def test_known_drug_returns_positive_score(self, engine, db, dentiste):
        from backend import models

        habit = models.DoctorMedicationHabit(
            doctor_id=dentiste.id, medication_name="Amoxicilline",
            usage_count=5
        )
        db.add(habit)
        db.commit()

        score = engine.get_relevance_score(db, dentiste.id, "Extraction", "Amoxicilline")
        assert score > 0.1
        assert score <= 0.95


# ── check_proactive_triggers ──────────────────────────────────────────────────

class TestCheckProactiveTriggers:
    def test_unknown_patient_returns_empty(self, engine, db):
        result = engine.check_proactive_triggers(db, patient_id=999999)
        assert result == []

    def test_missing_antecedents_triggers_quality(self, engine, db, dentiste):
        from backend import models

        pat = models.Patient(
            nom="TRIGTEST", prenom="Quality",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
            antecedents_medicaux=None,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        triggers = engine.check_proactive_triggers(db, pat.id)
        types = [t["type"] for t in triggers]
        assert "QUALITY" in types

    def test_overdue_detartrage_triggers_prevention(self, engine, db, dentiste):
        from backend import models

        pat = models.Patient(
            nom="DETARTTEST", prenom="Prev",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
            antecedents_medicaux="RAS",
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        # Détartrage il y a >365 jours
        db.add(models.Acte(
            patient_id=pat.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN,
            libelle="Détartrage prophylaxie",
            montant=1500.0,
            statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now() - timedelta(days=400),
        ))
        db.commit()

        triggers = engine.check_proactive_triggers(db, pat.id)
        types = [t["type"] for t in triggers]
        assert "CRITICAL_PREVENTION" in types
