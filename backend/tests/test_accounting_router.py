"""Tests routers/accounting.py — installment plans, payments, honoraires, treasury."""
import pytest
from datetime import datetime


def _make_patient(db, dentiste, nom="ACCTPAT"):
    from backend import models
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1980, 3, 15),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


def _plan_payload(patient_id):
    return {
        "patient_id": patient_id,
        "title": "Plan Orthodontie 2024",
        "total_amount": 15000.0,
        "installments": [
            {
                "label": "Acompte",
                "amount": 5000.0,
                "due_date": "2024-01-15T00:00:00",
                "status": "EN_ATTENTE",
            },
            {
                "label": "2ème versement",
                "amount": 5000.0,
                "due_date": "2024-04-15T00:00:00",
                "status": "EN_ATTENTE",
            },
            {
                "label": "Solde",
                "amount": 5000.0,
                "due_date": "2024-07-15T00:00:00",
                "status": "EN_ATTENTE",
            },
        ]
    }


# ── auth guards ────────────────────────────────────────────────────────────────

class TestAccountingGuard:
    def test_plans_requires_auth(self, client):
        r = client.post("/api/accounting/plans", json={})
        assert r.status_code == 401

    def test_payments_requires_auth(self, client):
        r = client.post("/api/accounting/payments", json={})
        assert r.status_code == 401

    def test_honoraires_requires_auth(self, client):
        r = client.get("/api/accounting/honoraires")
        assert r.status_code == 401

    def test_treasury_requires_auth(self, client):
        r = client.get("/api/accounting/treasury-hub")
        assert r.status_code == 401

    def test_frequent_acts_requires_auth(self, client):
        r = client.get("/api/accounting/frequent-acts")
        assert r.status_code == 401

    def test_overdue_requires_auth(self, client):
        r = client.get("/api/accounting/overdue")
        assert r.status_code == 401


# ── installment plans ─────────────────────────────────────────────────────────

class TestInstallmentPlans:
    def test_create_plan(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PLANPAT")
        r = client.post(
            "/api/accounting/plans",
            json=_plan_payload(pat.id),
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "Plan Orthodontie 2024"
        assert body["total_amount"] == 15000.0
        assert len(body["installments"]) == 3

    def test_get_patient_plans(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "GETPLAN")
        client.post("/api/accounting/plans", json=_plan_payload(pat.id), headers=auth_headers)

        r = client.get(f"/api/accounting/plans/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        plans = r.json()
        assert isinstance(plans, list)
        assert len(plans) >= 1

    def test_get_plans_empty(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "NOPLAN")
        r = client.get(f"/api/accounting/plans/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_delete_plan(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "DELPLAN")
        create_r = client.post("/api/accounting/plans", json=_plan_payload(pat.id), headers=auth_headers)
        plan_id = create_r.json()["id"]

        r = client.delete(f"/api/accounting/plans/{plan_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_delete_nonexistent_plan_returns_404(self, client, auth_headers):
        r = client.delete("/api/accounting/plans/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_update_installment(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "UPDINST")
        create_r = client.post("/api/accounting/plans", json=_plan_payload(pat.id), headers=auth_headers)
        inst_id = create_r.json()["installments"][0]["id"]

        r = client.put(
            f"/api/accounting/installments/{inst_id}",
            json={"status": "PAYE", "paid_date": "2024-01-20"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "PAYE"

    def test_update_nonexistent_installment_returns_404(self, client, auth_headers):
        r = client.put(
            "/api/accounting/installments/999999",
            json={"status": "PAYE"},
            headers=auth_headers,
        )
        assert r.status_code == 404


# ── payments ──────────────────────────────────────────────────────────────────

class TestPayments:
    def test_record_payment(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PAYPAT")
        r = client.post(
            "/api/accounting/payments",
            json={
                "patient_id": pat.id,
                "amount": 1500.0,
                "payment_method": "ESPECES",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["amount"] == 1500.0
        assert body["patient_id"] == pat.id

    def test_record_payment_with_notes(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PAYNOTES")
        r = client.post(
            "/api/accounting/payments",
            json={
                "patient_id": pat.id,
                "amount": 800.0,
                "payment_method": "VIREMENT",
                "notes": "Paiement partiel",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["notes"] == "Paiement partiel"

    def test_get_patient_payments(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "GETPAY")
        client.post(
            "/api/accounting/payments",
            json={"patient_id": pat.id, "amount": 500.0},
            headers=auth_headers,
        )
        r = client.get(f"/api/accounting/payments/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_payment_validated_by_set(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PAYVALIDBY")
        r = client.post(
            "/api/accounting/payments",
            json={"patient_id": pat.id, "amount": 300.0},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["validated_by"] is not None


# ── honoraires ────────────────────────────────────────────────────────────────

class TestHonoraires:
    def test_list_honoraires_empty(self, client, auth_headers):
        r = client.get("/api/accounting/honoraires", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total_amount" in body

    def test_list_honoraires_with_year_filter(self, client, auth_headers):
        r = client.get("/api/accounting/honoraires?year=2024", headers=auth_headers)
        assert r.status_code == 200

    def test_list_honoraires_with_month_filter(self, client, auth_headers):
        r = client.get("/api/accounting/honoraires?month=6", headers=auth_headers)
        assert r.status_code == 200

    def test_list_honoraires_insured_only_filter(self, client, auth_headers):
        r = client.get("/api/accounting/honoraires?filter_type=insured_notes_only", headers=auth_headers)
        assert r.status_code == 200

    def test_list_honoraires_by_patient(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "HONPAT")
        r = client.get(f"/api/accounting/honoraires?patient_id={pat.id}", headers=auth_headers)
        assert r.status_code == 200


# ── treasury hub ──────────────────────────────────────────────────────────────

class TestTreasuryHub:
    def test_treasury_hub_returns_structure(self, client, auth_headers):
        r = client.get("/api/accounting/treasury-hub", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)

    def test_treasury_hub_with_date_filter(self, client, auth_headers):
        r = client.get("/api/accounting/treasury-hub?period=month", headers=auth_headers)
        assert r.status_code == 200


# ── frequent acts ─────────────────────────────────────────────────────────────

class TestFrequentActs:
    def test_frequent_acts_returns_list(self, client, auth_headers):
        r = client.get("/api/accounting/frequent-acts", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_record_act(self, client, auth_headers):
        r = client.post(
            "/api/accounting/record-act",
            json={"name": "Composite 2 faces", "price": 600.0, "category": "CONSERVATRICE"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"


# ── overdue ───────────────────────────────────────────────────────────────────

class TestOverdue:
    def test_overdue_returns_dict(self, client, auth_headers):
        r = client.get("/api/accounting/overdue", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body


# ── encaisser ─────────────────────────────────────────────────────────────────

class TestEncaisser:
    def test_encaisser_nonexistent_item_returns_404(self, client, auth_headers):
        r = client.post("/api/accounting/encaisser/doc_999999", headers=auth_headers)
        assert r.status_code == 404
