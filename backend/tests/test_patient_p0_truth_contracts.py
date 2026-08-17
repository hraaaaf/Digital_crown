from datetime import datetime

import pytest
from pydantic import ValidationError

from backend import models
from backend.routers.patients import check_duplicate_patient
from backend.schemas.patient import PatientCreate, PatientUpdate
from backend.schemas.payments import PaymentCreate
from backend.tests.conftest import make_user


def _patient_payload(**overrides):
    payload = {
        "nom": "EL ALAMI",
        "prenom": "Youssef",
        "date_naissance": "1990-05-12",
        "sexe": "M",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("invalid", [None, "", " ", "inconnu", "X"])
def test_patient_create_rejects_implicit_or_unknown_sex(invalid):
    with pytest.raises(ValidationError):
        PatientCreate(**_patient_payload(sexe=invalid))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("M", "M"),
        ("homme", "M"),
        ("masculin", "M"),
        ("garçon", "M"),
        ("F", "F"),
        ("femme", "F"),
        ("féminin", "F"),
        ("fille", "F"),
    ],
)
def test_patient_create_normalizes_only_explicit_sex(raw, expected):
    patient = PatientCreate(**_patient_payload(sexe=raw))
    assert patient.sexe == expected


def test_patient_update_can_omit_sex_but_rejects_empty_value():
    assert PatientUpdate(nom="DUPONT").sexe is None
    with pytest.raises(ValidationError):
        PatientUpdate(sexe="")


def test_duplicate_check_never_crosses_tenant_boundary(db):
    owner_a = make_user(db, email="tenant-a@cabinet.ma")
    owner_b = make_user(db, email="tenant-b@cabinet.ma")
    born = datetime(1990, 5, 12)

    patient_a = models.Patient(
        nom="EL ALAMI",
        prenom="Youssef",
        date_naissance=born,
        sexe="M",
        employer_id=owner_a.id,
        numero_dossier="1",
    )
    patient_b = models.Patient(
        nom="EL ALAMI",
        prenom="Youssef",
        date_naissance=born,
        sexe="M",
        employer_id=owner_b.id,
        numero_dossier="1",
    )
    db.add_all([patient_a, patient_b])
    db.commit()
    db.refresh(patient_a)
    db.refresh(patient_b)

    assert check_duplicate_patient(db, "EL ALAMI", "Youssef", born, owner_a.id).id == patient_a.id
    assert check_duplicate_patient(db, "EL ALAMI", "Youssef", born, owner_b.id).id == patient_b.id
    assert check_duplicate_patient(
        db,
        "EL ALAMI",
        "Youssef",
        born,
        owner_a.id,
        exclude_id=patient_a.id,
    ) is None


def test_csv_import_rejects_missing_or_invalid_sex(client, auth_headers):
    csv_body = (
        "nom,prenom,date_naissance,sexe\n"
        "DUPONT,Claire,1992-01-03,\n"
        "MARTIN,Alex,1988-02-04,X\n"
    )
    response = client.post(
        "/api/patients/import-csv",
        headers=auth_headers,
        files={"file": ("patients.csv", csv_body.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 0
    assert len(body["errors"]) == 2
    assert "sexe" in body["errors"][0]["reason"].lower()
    assert "sexe invalide" in body["errors"][1]["reason"].lower()


def test_payment_requires_explicit_method():
    with pytest.raises(ValidationError):
        PaymentCreate(patient_id=1, amount=100)
    with pytest.raises(ValidationError):
        PaymentCreate(patient_id=1, amount=100, payment_method=None)


def test_payment_method_alias_is_normalized_when_explicit():
    payment = PaymentCreate(patient_id=1, amount=100, payment_method="espèces")
    assert payment.payment_method == "ESPECES"
