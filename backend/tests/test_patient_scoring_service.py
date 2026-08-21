"""Patient indicators: factual contracts, no automatic behavioral score."""
from datetime import datetime

from backend import models
from backend.services.patient_scoring_service import PatientScoringService


def _patient(db, dentiste, name="INDICATOR"):
    patient = models.Patient(
        nom=name,
        prenom="Test",
        date_naissance=datetime(1985, 5, 5),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _appointment(db, patient_id, status, employer_id):
    item = models.Appointment(
        patient_id=patient_id,
        employer_id=employer_id,
        datetime_start=datetime.now(),
        duration_minutes=30,
        status=status,
        motif="Test",
    )
    db.add(item)
    db.commit()


def _act(db, patient_id, practitioner_id, amount):
    item = models.Acte(
        patient_id=patient_id,
        praticien_id=practitioner_id,
        libelle="Consultation",
        type_acte=models.ActeType.SOIN,
        montant=amount,
        date_debut=datetime.now(),
    )
    db.add(item)
    db.commit()


def _payment(db, patient_id, amount):
    item = models.Payment(
        patient_id=patient_id,
        amount=amount,
        payment_method=models.PaymentMethod.ESPECES,
        payment_date=datetime.now(),
    )
    db.add(item)
    db.commit()


def test_new_patient_has_no_automatic_score_or_grade(db, dentiste):
    patient = _patient(db, dentiste, "NEWFACT")
    result = PatientScoringService().calculate_score(db, patient.id)
    assert result["score"] is None
    assert result["grade"] is None
    assert result["details"]["rdv_honores"] == 0
    assert result["details"]["rdv_annules"] == 0
    assert result["details"]["has_billing_data"] is False
    assert result["details"]["remaining_due"] is None
    assert result["details"]["assiduite_score"] is None
    assert result["details"]["solvabilite_score"] is None


def test_appointments_are_counts_not_behavioral_penalties(db, dentiste):
    patient = _patient(db, dentiste, "RDVFACT")
    _appointment(db, patient.id, models.AppointmentStatus.TERMINE, dentiste.id)
    _appointment(db, patient.id, models.AppointmentStatus.ANNULE, dentiste.id)
    result = PatientScoringService().calculate_score(db, patient.id)
    assert result["score"] is None
    assert result["details"]["rdv_honores"] == 1
    assert result["details"]["rdv_annules"] == 1
    assert result["details"]["rdv_total_observe"] == 2


def test_finance_is_factual_and_fail_closed_without_billing(db, dentiste):
    patient = _patient(db, dentiste, "PAYONLY")
    _payment(db, patient.id, 200.0)
    result = PatientScoringService().calculate_score(db, patient.id)
    assert result["details"]["has_billing_data"] is False
    assert result["details"]["total_encaisse"] == 200.0
    assert result["details"]["remaining_due"] is None


def test_finance_reports_billed_collected_and_remaining(db, dentiste):
    patient = _patient(db, dentiste, "BILLFACT")
    _act(db, patient.id, dentiste.id, 1000.0)
    _payment(db, patient.id, 400.0)
    result = PatientScoringService().calculate_score(db, patient.id)
    details = result["details"]
    assert details["has_billing_data"] is True
    assert details["total_facture"] == 1000.0
    assert details["total_encaisse"] == 400.0
    assert details["remaining_due"] == 600.0


def test_bulk_matches_factual_individual_contract(db, dentiste):
    patient = _patient(db, dentiste, "BULKFACT")
    _appointment(db, patient.id, models.AppointmentStatus.TERMINE, dentiste.id)
    _act(db, patient.id, dentiste.id, 500.0)
    _payment(db, patient.id, 500.0)
    service = PatientScoringService()
    individual = service.calculate_score(db, patient.id)
    bulk = service.calculate_scores_bulk(db, dentiste.id)[patient.id]
    assert bulk["score"] is None
    assert bulk["grade"] is None
    assert bulk["details"] == individual["details"]


def test_empty_cabinet_bulk_is_empty(db):
    service = PatientScoringService()
    assert service.calculate_scores_bulk(db, -999999) == {}
