from datetime import datetime

from backend import models
from backend.models_clinical_p3 import TreatmentMasterPlanRevision
from backend.security import get_password_hash


PASSWORD = "TestPass123!"


def _make_user(db, email, *, employer_id=None, permissions=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(PASSWORD),
        role="DENTISTE",
        nom_complet="P3 Master Plan Test",
        is_active=True,
        is_licensed=True,
        employer_id=employer_id,
        permissions=permissions or {},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_patient(db, owner, dossier):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="MASTERPLAN",
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


def test_each_successful_master_plan_save_appends_a_revision(client, db):
    owner = _make_user(db, "p3-master-plan-owner@test.ma")
    patient = _make_patient(db, owner, "P3-MASTER-1")
    headers = _headers(client, owner)
    url = f"/api/patients/{patient.id}/master-plan"

    first_payload = [
        {"title": "Assainissement", "assistant": "paro", "status": "pending", "date_str": "À planifier", "order_index": 0},
    ]
    second_payload = [
        {"title": "Assainissement", "assistant": "paro", "status": "done", "date_str": "Fait", "order_index": 0},
        {"title": "Restauration 16", "assistant": "general", "status": "pending", "date_str": "À planifier", "order_index": 1},
    ]

    first = client.put(url, headers=headers, json=first_payload)
    assert first.status_code == 200, first.text
    second = client.put(url, headers=headers, json=second_payload)
    assert second.status_code == 200, second.text

    revisions = client.get(f"{url}/revisions", headers=headers)
    assert revisions.status_code == 200, revisions.text
    rows = revisions.json()
    assert [row["revision"] for row in rows] == [2, 1]
    assert rows[0]["updated_by"] == owner.id
    assert rows[1]["updated_by"] == owner.id
    assert rows[0]["steps_snapshot"] == second_payload
    assert rows[1]["steps_snapshot"] == first_payload

    db_rows = (
        db.query(TreatmentMasterPlanRevision)
        .filter(TreatmentMasterPlanRevision.patient_id == patient.id)
        .order_by(TreatmentMasterPlanRevision.revision.asc())
        .all()
    )
    assert len(db_rows) == 2
    assert db_rows[0].steps_snapshot == first_payload
    assert db_rows[1].steps_snapshot == second_payload


def test_master_plan_revision_history_is_tenant_scoped(client, db):
    owner = _make_user(db, "p3-master-plan-tenant-a@test.ma")
    patient = _make_patient(db, owner, "P3-MASTER-2")
    owner_headers = _headers(client, owner)
    url = f"/api/patients/{patient.id}/master-plan"

    saved = client.put(
        url,
        headers=owner_headers,
        json=[{"title": "Étape A", "assistant": "general", "status": "pending", "date_str": "À planifier", "order_index": 0}],
    )
    assert saved.status_code == 200, saved.text

    foreign = _make_user(db, "p3-master-plan-tenant-b@test.ma")
    foreign_headers = _headers(client, foreign)
    denied = client.get(f"{url}/revisions", headers=foreign_headers)
    assert denied.status_code == 403, denied.text
