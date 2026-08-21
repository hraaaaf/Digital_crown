from datetime import datetime
from decimal import Decimal
from pathlib import Path

from backend import models
from backend.security import get_password_hash
from backend.services.catalog_connected_truth import flatten_catalog_acts


PASSWORD = "CatalogTruth123!"


def _make_owner(db, email: str):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(PASSWORD),
        role="DENTISTE",
        nom_complet="Catalogue Truth Test",
        is_active=True,
        is_licensed=True,
        permissions={"settings": True, "clinical": True},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_patient(db, owner, dossier: str):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="CATALOGUE",
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


def test_flatten_catalog_acts_preserves_public_contract_and_filters_inactive():
    catalog = [
        {
            "name": "Prévention",
            "acts": [
                {"id": 1, "name": "Détartrage", "code": "DET-001", "base_price": Decimal("500.00"), "is_active": True},
                {"id": 2, "name": "Acte masqué", "code": "OLD", "base_price": 100, "is_active": False},
            ],
        }
    ]
    assert flatten_catalog_acts(catalog, "DET-001") == [
        {
            "id": "cat_1",
            "catalog_act_id": 1,
            "name": "Détartrage",
            "code": "DET-001",
            "base_price": 500.0,
            "price": 500.0,
            "category": "Prévention",
            "is_habit": False,
        }
    ]
    assert flatten_catalog_acts(catalog, "OLD") == []


def test_clinical_search_and_quick_add_use_same_tenant_r6_catalog():
    source = Path("backend/routers/prescriptions.py").read_text(encoding="utf-8")
    assert 'q: str = ""' in source
    assert "current_user.get_employer_id()" in source
    assert "catalog_store.list_catalog(db, tenant_id)" in source
    assert "flatten_catalog_acts(catalog, query=q" in source
    assert 'route, "path", None) == "/catalog/quick-add"' in source
    assert "catalog_store.create_act" in source
    assert "models.CatalogAct" not in source


def test_master_plan_validates_new_snapshot_tenant_but_reuses_history():
    source = Path("backend/routers/patient_master_plan_p3.py").read_text(encoding="utf-8")
    model = Path("backend/models_catalog_plan.py").read_text(encoding="utf-8")
    assert "TreatmentPlanCatalogSnapshot" in source
    assert "catalog_store.get_owned(db, catalog_store.acts, act_id, tenant_id)" in source
    assert "Acte catalogue indisponible pour ce cabinet" in source
    assert "_same_snapshot(explicit, preserved)" in source
    assert "snapshot = queue.popleft()" in source
    assert "revision_snapshot" in source
    assert "treatment_plan_catalog_snapshots" in model
    assert "Numeric(12, 2)" in model


def test_master_plan_http_put_and_get_return_persisted_catalog_snapshot(client, db):
    owner = _make_owner(db, "catalog-http-roundtrip@test.ma")
    patient = _make_patient(db, owner, "CAT-HTTP-1")
    headers = _headers(client, owner)

    specialty_response = client.post(
        "/api/catalog/specialties",
        headers=headers,
        json={"name": "Certification Catalogue HTTP", "color": "#64748B"},
    )
    assert specialty_response.status_code == 201, specialty_response.text
    specialty = specialty_response.json()

    act_response = client.post(
        f"/api/catalog/specialties/{specialty['id']}/acts",
        headers=headers,
        json={
            "name": "Détartrage HTTP certifié",
            "code": "CERT-HTTP-001",
            "base_price": 500,
            "color": "#0F766E",
            "is_active": True,
        },
    )
    assert act_response.status_code == 201, act_response.text
    act = act_response.json()

    master_url = f"/api/patients/{patient.id}/master-plan"
    snapshot = {
        "act_id": act["id"],
        "code": "CERT-HTTP-001",
        "name": "Détartrage HTTP certifié",
        "price": 500,
    }
    payload = [
        {
            "title": "Détartrage HTTP certifié",
            "assistant": "Catalogue cabinet · Certification Catalogue HTTP · CERT-HTTP-001 · 500 DH · Tarif capturé",
            "status": "pending",
            "date_str": "À planifier",
            "order_index": 0,
            "catalog_snapshot": snapshot,
        }
    ]

    saved = client.put(master_url, headers=headers, json=payload)
    assert saved.status_code == 200, saved.text
    saved_step = saved.json()["steps"][0]
    assert saved_step["catalog_snapshot"] == snapshot

    reread = client.get(master_url, headers=headers)
    assert reread.status_code == 200, reread.text
    reread_step = reread.json()["steps"][0]
    assert reread_step["catalog_snapshot"] == snapshot
