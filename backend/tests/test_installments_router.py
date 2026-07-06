"""Tests routers/installments.py — instalment plans CRUD."""
from datetime import datetime, timedelta


def _make_patient(db, dentiste, nom="INSTPAT"):
    from backend import models
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


def _plan_payload(patient_id, n_installments=2):
    due = (datetime.now() + timedelta(days=30)).isoformat()
    return {
        "patient_id": patient_id,
        "title": "Plan Orthodontie",
        "total_amount": 60000.0,
        "installments": [
            {"label": f"Semestre {i+1}", "amount": 30000.0, "due_date": due}
            for i in range(n_installments)
        ],
    }


class TestGetInstallmentPlans:
    def test_requires_auth(self, client):
        r = client.get("/api/installments/patient/1")
        assert r.status_code == 401

    def test_empty_list_for_new_patient(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "EMPTY")
        r = client.get(f"/api/installments/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_foreign_patient_returns_403(self, client, auth_headers):
        r = client.get("/api/installments/patient/999999", headers=auth_headers)
        assert r.status_code in (403, 404)


class TestCreateInstallmentPlan:
    def test_requires_auth(self, client):
        r = client.post("/api/installments/", json={})
        assert r.status_code == 401

    def test_create_plan_with_installments(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "CREATEPLAN")
        r = client.post(
            "/api/installments/",
            json=_plan_payload(pat.id),
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "Plan Orthodontie"
        assert body["total_amount"] == 60000.0
        assert len(body["installments"]) == 2

    def test_list_returns_created_plan(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "LISTPLAN")
        client.post("/api/installments/", json=_plan_payload(pat.id), headers=auth_headers)

        r = client.get(f"/api/installments/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestUpdateInstallment:
    def test_update_status_to_paye(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "UPDATINST")
        create_r = client.post(
            "/api/installments/",
            json=_plan_payload(pat.id, n_installments=1),
            headers=auth_headers,
        )
        inst_id = create_r.json()["installments"][0]["id"]

        r = client.put(
            f"/api/installments/{inst_id}",
            json={"status": "PAYE"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "PAYE"

    def test_update_label(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "LABELUPD")
        create_r = client.post(
            "/api/installments/",
            json=_plan_payload(pat.id, n_installments=1),
            headers=auth_headers,
        )
        inst_id = create_r.json()["installments"][0]["id"]

        r = client.put(
            f"/api/installments/{inst_id}",
            json={"label": "Acompte initial"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["label"] == "Acompte initial"

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        r = client.put(
            "/api/installments/999999",
            json={"status": "PAYE"},
            headers=auth_headers,
        )
        assert r.status_code == 404


class TestDeleteInstallmentPlan:
    def test_delete_plan(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "DELPLAN")
        create_r = client.post(
            "/api/installments/",
            json=_plan_payload(pat.id),
            headers=auth_headers,
        )
        plan_id = create_r.json()["id"]

        r = client.delete(f"/api/installments/plan/{plan_id}", headers=auth_headers)
        assert r.status_code == 204

        # Confirm deletion
        list_r = client.get(f"/api/installments/patient/{pat.id}", headers=auth_headers)
        assert list_r.json() == []

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete("/api/installments/plan/999999", headers=auth_headers)
        assert r.status_code == 404
