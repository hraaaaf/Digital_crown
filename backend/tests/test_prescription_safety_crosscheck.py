from datetime import datetime, timedelta

from backend import models
from backend.services.prescription_service import prescription_service


def test_antibiotic_crosscheck_no_surgical_act(db, dentiste):
    patient = models.Patient(
        nom="Alami",
        prenom="Omar",
        date_naissance=datetime(1985, 4, 12),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    appt = models.Appointment(
        patient_id=patient.id,
        datetime_start=datetime.now(),
        duration_minutes=30,
        motif="Contrôle simple",
        status=models.AppointmentStatus.PREVU,
        employer_id=dentiste.id,
    )
    db.add(appt)
    db.commit()

    warnings = prescription_service.check_safety(db, patient.id, ["Amoxicilline 1g"])

    coherence_warnings = [w for w in warnings if w.get("type") == "coherence"]
    assert len(coherence_warnings) == 1
    assert coherence_warnings[0]["drug"] == "antibiotique-injustifie"
    assert "Incohérence clinique" in coherence_warnings[0]["message"]


def test_antibiotic_crosscheck_with_surgical_act(db, dentiste):
    patient = models.Patient(
        nom="El Fassi",
        prenom="Youssef",
        date_naissance=datetime(1992, 8, 20),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    appt = models.Appointment(
        patient_id=patient.id,
        datetime_start=datetime.now(),
        duration_minutes=45,
        motif="Extraction dent de sagesse",
        status=models.AppointmentStatus.PREVU,
        employer_id=dentiste.id,
    )
    db.add(appt)
    db.commit()

    warnings = prescription_service.check_safety(db, patient.id, ["Amoxicilline 1g"])

    coherence_warnings = [w for w in warnings if w.get("type") == "coherence"]
    assert len(coherence_warnings) == 0


def test_medication_safety_does_not_emit_prophylaxis_omission(db, dentiste):
    """Preventive recall belongs outside the medication-safety contract."""
    patient = models.Patient(
        nom="Tazi",
        prenom="Laila",
        date_naissance=datetime(1995, 11, 5),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    old_date = datetime.now() - timedelta(days=400)
    db.add(
        models.Appointment(
            patient_id=patient.id,
            datetime_start=old_date,
            duration_minutes=30,
            motif="Détartrage",
            status=models.AppointmentStatus.TERMINE,
            employer_id=dentiste.id,
        )
    )
    db.commit()

    warnings = prescription_service.check_safety(db, patient.id, ["Doliprane 1g"])

    assert not any(w.get("type") == "omission" for w in warnings)
    assert not any(w.get("drug") == "omission-prophylaxie" for w in warnings)


def test_medication_safety_ignores_recent_prophylaxis_state(db, dentiste):
    """A recent prophylaxis must not affect medication safety either way."""
    patient = models.Patient(
        nom="Mernissi",
        prenom="Salma",
        date_naissance=datetime(1988, 1, 30),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    db.add(
        models.Acte(
            patient_id=patient.id,
            praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN,
            libelle="Détartrage et polissage",
            montant=400.0,
            date_debut=datetime.now() - timedelta(days=180),
        )
    )
    db.commit()

    warnings = prescription_service.check_safety(db, patient.id, ["Doliprane 1g"])

    assert not any(w.get("type") == "omission" for w in warnings)
