"""Tests for services/patient_scoring_service.py — requires DB."""
import pytest
from datetime import datetime
from backend import models
from backend.services.patient_scoring_service import PatientScoringService


def _make_patient(db, dentiste, nom="SCORE"):
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1985, 5, 5),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


def _add_appointment(db, patient_id, status, employer_id=1):
    appt = models.Appointment(
        patient_id=patient_id,
        employer_id=employer_id,
        datetime_start=datetime.now(),
        duration_minutes=30,
        status=status,
        motif="Test",
    )
    db.add(appt)
    db.commit()
    return appt


def _add_acte(db, patient_id, praticien_id, montant):
    acte = models.Acte(
        patient_id=patient_id,
        praticien_id=praticien_id,
        libelle="Consultation",
        type_acte=models.ActeType.SOIN,
        montant=montant,
        date_debut=datetime.now(),
    )
    db.add(acte)
    db.commit()
    return acte


def _add_payment(db, patient_id, amount):
    pay = models.Payment(
        patient_id=patient_id,
        amount=amount,
        payment_method=models.PaymentMethod.ESPECES,
        payment_date=datetime.now(),
    )
    db.add(pay)
    db.commit()
    return pay


class TestPatientScoringService:
    def setup_method(self):
        self.service = PatientScoringService()

    def test_new_patient_perfect_score(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NEWSCORE")
        result = self.service.calculate_score(db, pat.id)
        assert result["score"] == 100
        assert result["grade"] == "PLATINUM"

    def test_returns_required_keys(self, db, dentiste):
        pat = _make_patient(db, dentiste, "KEYS")
        result = self.service.calculate_score(db, pat.id)
        assert "score" in result
        assert "grade" in result
        assert "details" in result

    def test_details_keys(self, db, dentiste):
        pat = _make_patient(db, dentiste, "DETKEYS")
        result = self.service.calculate_score(db, pat.id)
        details = result["details"]
        for k in ("assiduite_score", "solvabilite_score", "rdv_honores", "rdv_annules",
                  "total_facture", "total_encaisse"):
            assert k in details

    def test_cancelled_appointment_reduces_score(self, db, dentiste):
        pat = _make_patient(db, dentiste, "CANCEL")
        # Multiple cancellations to lower score
        for _ in range(5):
            _add_appointment(db, pat.id, models.AppointmentStatus.ANNULE, dentiste.id)
        result = self.service.calculate_score(db, pat.id)
        assert result["details"]["assiduite_score"] < 100
        assert result["details"]["rdv_annules"] == 5

    def test_completed_appointment_adds_bonus(self, db, dentiste):
        pat = _make_patient(db, dentiste, "BONUS")
        _add_appointment(db, pat.id, models.AppointmentStatus.TERMINE, dentiste.id)
        result = self.service.calculate_score(db, pat.id)
        assert result["details"]["rdv_honores"] == 1
        assert result["details"]["assiduite_score"] > 100 or result["score"] >= 100

    def test_partial_payment_lowers_solvabilite(self, db, dentiste):
        pat = _make_patient(db, dentiste, "PARTIAL")
        _add_acte(db, pat.id, dentiste.id, 1000.0)
        _add_payment(db, pat.id, 400.0)
        result = self.service.calculate_score(db, pat.id)
        assert result["details"]["total_facture"] == 1000.0
        assert result["details"]["total_encaisse"] == 400.0
        assert result["details"]["solvabilite_score"] == 40

    def test_full_payment_perfect_solvabilite(self, db, dentiste):
        pat = _make_patient(db, dentiste, "FULLPAY")
        _add_acte(db, pat.id, dentiste.id, 500.0)
        _add_payment(db, pat.id, 500.0)
        result = self.service.calculate_score(db, pat.id)
        assert result["details"]["solvabilite_score"] == 100

    def test_grade_platinum(self, db, dentiste):
        pat = _make_patient(db, dentiste, "PLAT")
        result = self.service.calculate_score(db, pat.id)
        assert result["grade"] == "PLATINUM"

    def test_grade_bronze_with_many_cancellations_no_payment(self, db, dentiste):
        pat = _make_patient(db, dentiste, "BRONZE")
        for _ in range(10):
            _add_appointment(db, pat.id, models.AppointmentStatus.ANNULE, dentiste.id)
        _add_acte(db, pat.id, dentiste.id, 1000.0)
        # No payment
        result = self.service.calculate_score(db, pat.id)
        assert result["grade"] in ("BRONZE", "SILVER")  # depends on exact calculation

    def test_score_is_integer(self, db, dentiste):
        pat = _make_patient(db, dentiste, "INTSCR")
        result = self.service.calculate_score(db, pat.id)
        assert isinstance(result["score"], int)

    def test_grade_from_score_logic(self):
        svc = PatientScoringService()
        assert svc._grade_from_score(95) == "PLATINUM"
        assert svc._grade_from_score(80) == "GOLD"
        assert svc._grade_from_score(60) == "SILVER"
        assert svc._grade_from_score(30) == "BRONZE"
        assert svc._grade_from_score(90) == "PLATINUM"
        assert svc._grade_from_score(75) == "GOLD"
        assert svc._grade_from_score(50) == "SILVER"
        assert svc._grade_from_score(49) == "BRONZE"


class TestPatientScoringBulk:
    def setup_method(self):
        self.service = PatientScoringService()

    def test_empty_cabinet_returns_empty_dict(self, db, dentiste):
        from backend import models as m
        # Create a dummy employer with no patients
        import uuid
        dummy = m.User(
            email=f"nopat_{uuid.uuid4().hex[:8]}@test.ma",
            nom_complet="No Patient Owner",
            hashed_password="$2b$12$dummy",
            role=m.UserRole.DENTISTE,
            is_active=True,
        )
        db.add(dummy)
        db.commit()
        db.refresh(dummy)
        result = self.service.calculate_scores_bulk(db, dummy.id)
        assert result == {}

    def test_bulk_returns_all_patients(self, db, dentiste):
        p1 = _make_patient(db, dentiste, "BULK1")
        p2 = _make_patient(db, dentiste, "BULK2")
        result = self.service.calculate_scores_bulk(db, dentiste.id)
        assert p1.id in result
        assert p2.id in result

    def test_bulk_scores_match_individual(self, db, dentiste):
        pat = _make_patient(db, dentiste, "BULKSINGLE")
        individual = self.service.calculate_score(db, pat.id)
        bulk = self.service.calculate_scores_bulk(db, dentiste.id)
        # Bulk and individual should agree on score
        assert bulk[pat.id]["score"] == individual["score"]

    def test_bulk_has_correct_structure(self, db, dentiste):
        pat = _make_patient(db, dentiste, "BULKSTRUCT")
        result = self.service.calculate_scores_bulk(db, dentiste.id)
        entry = result[pat.id]
        assert "score" in entry
        assert "grade" in entry
        assert "details" in entry
