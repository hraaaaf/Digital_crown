from datetime import datetime

import pytest

from backend import models
from backend.models_clinic_p2 import PatientPractitionerAssignment
from backend.tests.conftest import make_user


def _patient(db, owner, dossier="P2-101"):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="EL AMRANI",
        prenom="Sara",
        date_naissance=datetime(1992, 5, 18),
        sexe="F",
        employer_id=owner.id,
        assurance="AUCUNE",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _login(client, user, password="TestPass123!"):
    response = client.post("/api/auth/login", data={"username": user.email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_patient_practitioner_assignment_is_additive_and_tenant_safe(client, db, dentiste):
    associate = make_user(db, role="DENTISTE")
    associate.employer_id = dentiste.id
    secretary = make_user(db, role="SECRETAIRE")
    secretary.employer_id = dentiste.id
    inactive = make_user(db, role="DENTISTE", active=False)
    inactive.employer_id = dentiste.id
    pending = make_user(db, role="DENTISTE")
    pending.employer_id = dentiste.id
    pending.approval_status = models.ApprovalStatus.PENDING.value
    foreign = make_user(db, role="DENTISTE")
    db.commit()

    patient = _patient(db, dentiste)
    headers = _login(client, dentiste)

    options = client.get("/api/patients/_clinic/practitioners", headers=headers)
    assert options.status_code == 200, options.text
    option_ids = {row["id"] for row in options.json()}
    assert dentiste.id in option_ids
    assert associate.id in option_ids
    assert secretary.id not in option_ids
    assert inactive.id not in option_ids
    assert pending.id not in option_ids
    assert foreign.id not in option_ids

    assigned = client.put(
        f"/api/patients/{patient.id}/practitioner",
        headers=headers,
        json={"practitioner_id": associate.id},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["practitioner"]["id"] == associate.id

    stored_patient = db.query(models.Patient).filter(models.Patient.id == patient.id).one()
    assert stored_patient.nom == "EL AMRANI"
    assignment = db.query(PatientPractitionerAssignment).filter_by(patient_id=patient.id).one()
    assert assignment.practitioner_id == associate.id
    assert assignment.employer_id == dentiste.id

    rejected = client.put(
        f"/api/patients/{patient.id}/practitioner",
        headers=headers,
        json={"practitioner_id": foreign.id},
    )
    assert rejected.status_code == 403

    cleared = client.put(
        f"/api/patients/{patient.id}/practitioner",
        headers=headers,
        json={"practitioner_id": None},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["practitioner"] is None
    db.refresh(assignment)
    assert assignment.practitioner_id is None


def test_financial_snapshot_attributes_only_traceable_payments(client, db, dentiste):
    associate = make_user(db, role="DENTISTE")
    associate.employer_id = dentiste.id
    db.commit()
    patient = _patient(db, dentiste, dossier="P2-102")

    owner_act = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOINS,
        libelle="Détartrage",
        montant=1000.0,
        statut_paiement=models.PaiementStatut.PARTIEL,
    )
    associate_act = models.Acte(
        patient_id=patient.id,
        praticien_id=associate.id,
        type_acte=models.ActeType.PROTHESE,
        libelle="Couronne",
        montant=2000.0,
        statut_paiement=models.PaiementStatut.PARTIEL,
    )
    db.add_all([owner_act, associate_act])
    db.flush()
    db.add_all([
        models.Payment(
            patient_id=patient.id,
            amount=500.0,
            payment_method=models.PaymentMethod.CARTE,
            acte_id=owner_act.id,
        ),
        models.Payment(
            patient_id=patient.id,
            amount=1200.0,
            payment_method=models.PaymentMethod.ESPECES,
            acte_id=associate_act.id,
        ),
        models.Payment(
            patient_id=patient.id,
            amount=300.0,
            payment_method=models.PaymentMethod.ESPECES,
            acte_id=None,
        ),
    ])
    db.commit()

    headers = _login(client, dentiste)
    response = client.get(f"/api/patients/{patient.id}/financial-snapshot", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["total_billed"] == 3000.0
    assert payload["total_collected"] == 2000.0
    assert payload["unattributed_collected"] == 300.0

    by_id = {row["practitioner_id"]: row for row in payload["by_practitioner"]}
    assert by_id[dentiste.id]["total_billed"] == 1000.0
    assert by_id[dentiste.id]["linked_collected"] == 500.0
    assert by_id[dentiste.id]["linked_remaining_due"] == 500.0
    assert by_id[associate.id]["total_billed"] == 2000.0
    assert by_id[associate.id]["linked_collected"] == 1200.0
    assert by_id[associate.id]["linked_remaining_due"] == 800.0
