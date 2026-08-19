from datetime import datetime

from backend import models
from backend.models_clinical_p3 import PatientOdontogram  # noqa: F401 — registers metadata
from backend.security import get_password_hash


PASSWORD = "TestPass123!"
SURFACES = {"M": "CARIES", "D": "HEALTHY", "O": "HEALTHY", "V": "HEALTHY", "P": "HEALTHY"}
SURFACES_V2 = {"M": "FILLING_COMPOSITE", "D": "HEALTHY", "O": "HEALTHY", "V": "HEALTHY", "P": "HEALTHY"}


def _make_user(db, email, *, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(PASSWORD),
        role="DENTISTE",
        nom_complet="Dr P3 Test",
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
        permissions=permissions or {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_patient(db, owner, dossier="P3-ODONTO-1"):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="ODONTO",
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _payload(state, revision=0, dentition="ADULT"):
    return {
        "dentition_type": dentition,
        "state": state,
        "expected_revision": revision,
    }


def test_odontogram_get_none_then_create_and_read(client, db, dentiste, auth_headers):
    patient = _make_patient(db, dentiste)

    empty = client.get(f"/api/patients/{patient.id}/odontogram", headers=auth_headers)
    assert empty.status_code == 200, empty.text
    assert empty.json() is None

    created = client.put(
        f"/api/patients/{patient.id}/odontogram",
        headers=auth_headers,
        json=_payload({"11": SURFACES}),
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["patient_id"] == patient.id
    assert body["revision"] == 1
    assert body["dentition_type"] == "ADULT"
    assert body["state"]["11"]["M"] == "CARIES"
    assert body["updated_by"] == dentiste.id

    read = client.get(f"/api/patients/{patient.id}/odontogram", headers=auth_headers)
    assert read.status_code == 200, read.text
    assert read.json()["revision"] == 1
    assert read.json()["state"]["11"]["M"] == "CARIES"


def test_odontogram_update_increments_revision_and_stale_write_fails(client, db, dentiste, auth_headers):
    patient = _make_patient(db, dentiste, "P3-ODONTO-2")
    url = f"/api/patients/{patient.id}/odontogram"

    first = client.put(url, headers=auth_headers, json=_payload({"11": SURFACES}, 0))
    assert first.status_code == 200, first.text
    assert first.json()["revision"] == 1

    second = client.put(url, headers=auth_headers, json=_payload({"11": SURFACES_V2}, 1))
    assert second.status_code == 200, second.text
    assert second.json()["revision"] == 2
    assert second.json()["state"]["11"]["M"] == "FILLING_COMPOSITE"

    stale = client.put(url, headers=auth_headers, json=_payload({"11": SURFACES}, 1))
    assert stale.status_code == 409, stale.text

    after = client.get(url, headers=auth_headers)
    assert after.status_code == 200
    assert after.json()["revision"] == 2
    assert after.json()["state"]["11"]["M"] == "FILLING_COMPOSITE"


def test_odontogram_rejects_incompatible_fdi_and_empty_state(client, db, dentiste, auth_headers):
    patient = _make_patient(db, dentiste, "P3-ODONTO-3")
    url = f"/api/patients/{patient.id}/odontogram"

    invalid_fdi = client.put(
        url,
        headers=auth_headers,
        json=_payload({"51": SURFACES}, 0, "ADULT"),
    )
    assert invalid_fdi.status_code == 422, invalid_fdi.text

    empty = client.put(url, headers=auth_headers, json=_payload({}, 0))
    assert empty.status_code == 422, empty.text


def test_odontogram_is_tenant_scoped(client, db, dentiste):
    patient = _make_patient(db, dentiste, "P3-ODONTO-4")
    other_owner = _make_user(db, "other-p3-owner@test.ma")
    headers = _headers(client, other_owner)

    get_response = client.get(f"/api/patients/{patient.id}/odontogram", headers=headers)
    assert get_response.status_code == 403, get_response.text

    put_response = client.put(
        f"/api/patients/{patient.id}/odontogram",
        headers=headers,
        json=_payload({"11": SURFACES}),
    )
    assert put_response.status_code == 403, put_response.text


def test_odontogram_requires_clinical_permission(client, db, dentiste):
    patient = _make_patient(db, dentiste, "P3-ODONTO-5")
    collaborator = _make_user(
        db,
        "p3-no-clinical@test.ma",
        employer_id=dentiste.id,
        permissions={"patients": True, "clinical": False},
    )
    headers = _headers(client, collaborator)

    get_response = client.get(f"/api/patients/{patient.id}/odontogram", headers=headers)
    assert get_response.status_code == 403, get_response.text

    put_response = client.put(
        f"/api/patients/{patient.id}/odontogram",
        headers=headers,
        json=_payload({"11": SURFACES}),
    )
    assert put_response.status_code == 403, put_response.text
