"""Tests routers/accounting.py — payments, honoraires, treasury and legacy-route guards."""
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


def _seed_legacy_doc_archive(db, patient_id, employer_id, amount=500.0):
    """Simule un DocumentArchive historique pré-UNIFY-ACT-PERSISTENCE-1 : jamais de
    ligne Acte liée (created directement en DB, sans passer par /documents/generate)."""
    import uuid as _uuid
    from backend import models
    doc = models.DocumentArchive(
        patient_id=patient_id,
        uploaded_by_id=employer_id,
        document_type=models.DocumentType.NOTE_HONORAIRES,
        filename=f"note_{_uuid.uuid4().hex[:8]}.pdf",
        original_filename="note.pdf",
        document_group_id=str(_uuid.uuid4()),
        version_number=1,
        is_latest_version=True,
        file_hash=_uuid.uuid4().hex,
        file_size=1024,
        file_path="/tmp/note.pdf",
        title="Consultation",
        is_accounted=True,
        payment_status=models.PaiementStatut.EN_ATTENTE,
        is_collected=False,
        clinical_data={"payments": [{"acte": "Consultation", "montant": amount}]},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── route / auth guards ───────────────────────────────────────────────────────

class TestAccountingGuard:
    def test_legacy_plan_routes_are_removed(self, client):
        # P0-E: installment CRUD has one canonical surface under /api/installments.
        # The former /api/accounting/plans aliases must remain absent, not merely hidden.
        assert client.post("/api/accounting/plans", json={}).status_code == 404
        assert client.get("/api/accounting/plans/patient/1").status_code == 404
        assert client.put("/api/accounting/installments/1", json={}).status_code == 404
        assert client.delete("/api/accounting/plans/1").status_code == 404

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
        create_r = client.post(
            "/api/accounting/payments",
            json={"patient_id": pat.id, "amount": 500.0, "payment_method": "ESPECES"},
            headers=auth_headers,
        )
        assert create_r.status_code == 200
        r = client.get(f"/api/accounting/payments/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_payment_validated_by_set(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PAYVALIDBY")
        r = client.post(
            "/api/accounting/payments",
            json={"patient_id": pat.id, "amount": 300.0, "payment_method": "ESPECES"},
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

    def test_new_document_not_double_counted(self, client, db, auth_headers, dentiste):
        # UNIFY-ACT-PERSISTENCE-1 : un document généré via /documents/generate a
        # désormais des Acte liés — /accounting/honoraires ne doit pas sommer aussi
        # son clinical_data JSON en plus, sinon le montant est compté deux fois.
        pat = _make_patient(db, dentiste, "DEDUPPAT")
        req_data = {
            "type": "note",
            "patient_id": pat.id,
            "is_accounted": True,
            "payment_status": "PAYE",
            "data": {
                "payments": [{"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 1000.0, "mode_reglement": "ESPECES"}],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp_gen = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp_gen.status_code == 200, resp_gen.text

        r = client.get(f"/api/accounting/honoraires?patient_id={pat.id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_amount"] == 1000.0  # pas 2000.0
        assert len(body["items"]) == 1
        assert body["items"][0]["id"].startswith("acte_")

    def test_legacy_document_without_acte_still_extracted_from_json(self, client, db, auth_headers, dentiste):
        # Non-régression : les documents historiques (jamais liés à un Acte, pas de
        # backfill) doivent continuer à être comptés via l'extraction JSON existante.
        pat = _make_patient(db, dentiste, "LEGACYDOCPAT")
        _seed_legacy_doc_archive(db, pat.id, dentiste.id, amount=500.0)

        r = client.get(f"/api/accounting/honoraires?patient_id={pat.id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_amount"] == 500.0
        assert len(body["items"]) == 1
        assert body["items"][0]["id"].startswith("doc_")

    def test_insured_notes_only_still_shows_new_document_via_json(self, client, db, auth_headers, dentiste):
        # Mode filtré : acte_query est mise à `filter(False)` (exclut tous les Acte
        # simples) — la garde de dédoublonnage doit rester désactivée dans ce mode,
        # sinon un nouveau document avec Acte liés disparaîtrait complètement de la vue.
        from backend import models
        pat = _make_patient(db, dentiste, "INSUREDPAT")
        pat.assurance = "CNOPS"
        db.commit()

        req_data = {
            "type": "note",
            "patient_id": pat.id,
            "is_accounted": True,
            "payment_status": "PAYE",
            "data": {
                "payments": [{"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 800.0, "mode_reglement": "ESPECES"}],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp_gen = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp_gen.status_code == 200, resp_gen.text

        r = client.get(f"/api/accounting/honoraires?filter_type=insured_notes_only&patient_id={pat.id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_amount"] == 800.0
        assert len(body["items"]) == 1
        assert body["items"][0]["id"].startswith("doc_")


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

    def test_treasury_hub_new_document_not_double_counted(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "TREASDEDUPPAT")
        req_data = {
            "type": "note",
            "patient_id": pat.id,
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
            "data": {
                "payments": [{"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 600.0, "mode_reglement": "ESPECES"}],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp_gen = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp_gen.status_code == 200, resp_gen.text

        r = client.get("/api/accounting/treasury-hub", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        matching_items = [
            it for it in body.get("items", [])
            if it.get("patient_id") == pat.id
        ]
        assert len(matching_items) == 1
        assert matching_items[0]["id"].startswith("acte_")


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
        r = client.post(
            "/api/accounting/encaisser/doc_999999",
            json={"payment_method": "ESPECES"},
            headers=auth_headers,
        )
        assert r.status_code == 404
