import pytest
from pydantic import ValidationError

from backend.schemas.patient import PatientCreate, PatientUpdate
from backend.schemas.payments import PaymentCreate


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


def test_payment_requires_explicit_method():
    with pytest.raises(ValidationError):
        PaymentCreate(patient_id=1, amount=100)
    with pytest.raises(ValidationError):
        PaymentCreate(patient_id=1, amount=100, payment_method=None)


def test_payment_method_alias_is_normalized_when_explicit():
    payment = PaymentCreate(patient_id=1, amount=100, payment_method="espèces")
    assert payment.payment_method == "ESPECES"
