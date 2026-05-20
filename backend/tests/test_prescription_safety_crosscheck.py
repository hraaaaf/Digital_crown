import pytest
from datetime import datetime, timedelta, date
from backend import models
from backend.services.prescription_service import prescription_service


def test_antibiotic_crosscheck_no_surgical_act(db, dentiste):
    """
    Si on prescrit un antibiotique (ex: Amoxicilline) mais qu'aucun
    acte chirurgical ou endodontique n'est prévu ou réalisé aujourd'hui,
    une alerte de type 'coherence' (antibiotique-injustifie) doit être générée.
    """
    # Création du patient
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

    # RDV simple d'aujourd'hui sans mot-clé chirurgical
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

    # Appel de check_safety
    warnings = prescription_service.check_safety(db, patient.id, ["Amoxicilline 1g"])
    
    # On doit retrouver l'alerte d'incohérence
    coherence_warnings = [w for w in warnings if w.get("type") == "coherence"]
    assert len(coherence_warnings) == 1
    assert coherence_warnings[0]["drug"] == "antibiotique-injustifie"
    assert "Incohérence clinique" in coherence_warnings[0]["message"]


def test_antibiotic_crosscheck_with_surgical_act(db, dentiste):
    """
    Si un acte chirurgical (ex: Extraction) est prévu aujourd'hui,
    l'alerte d'antibiothérapie injustifiée ne doit PAS apparaître.
    """
    # Création du patient
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

    # RDV d'aujourd'hui pour une extraction
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

    # Appel de check_safety
    warnings = prescription_service.check_safety(db, patient.id, ["Amoxicilline 1g"])
    
    coherence_warnings = [w for w in warnings if w.get("type") == "coherence"]
    assert len(coherence_warnings) == 0


def test_prophylaxis_omission_no_recent_prophy(db, dentiste):
    """
    Si aucun détartrage/prophylaxie n'a été fait dans les 12 derniers mois,
    une suggestion de type 'omission' (omission-prophylaxie) doit être générée.
    """
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

    # RDV ancien (plus de 12 mois)
    old_date = datetime.now() - timedelta(days=400)
    appt = models.Appointment(
        patient_id=patient.id,
        datetime_start=old_date,
        duration_minutes=30,
        motif="Détartrage",
        status=models.AppointmentStatus.TERMINE,
        employer_id=dentiste.id,
    )
    db.add(appt)
    db.commit()

    warnings = prescription_service.check_safety(db, patient.id, ["Doliprane 1g"])
    
    omission_warnings = [w for w in warnings if w.get("type") == "omission"]
    assert len(omission_warnings) == 1
    assert omission_warnings[0]["drug"] == "omission-prophylaxie"
    assert "Aucun détartrage" in omission_warnings[0]["message"]


def test_prophylaxis_omission_with_recent_prophy(db, dentiste):
    """
    Si un détartrage a été fait il y a 6 mois, l'omission ne doit pas être générée.
    """
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

    # Acte de détartrage récent (6 mois)
    recent_date = datetime.now() - timedelta(days=180)
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Détartrage et polissage",
        montant=400.0,
        date_debut=recent_date,
    )
    db.add(acte)
    db.commit()

    warnings = prescription_service.check_safety(db, patient.id, ["Doliprane 1g"])
    
    omission_warnings = [w for w in warnings if w.get("type") == "omission"]
    assert len(omission_warnings) == 0
