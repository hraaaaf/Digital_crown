"""Extended tests for routers/patients.py — covers routes missing from test_patients.py."""
import io
import pytest
from datetime import datetime
from backend import models


PATIENT_PAYLOAD = {
    "nom": "Zerrouki",
    "prenom": "Karim",
    "date_naissance": "1988-07-22",
    "sexe": "M",
}


def _create_patient(client, auth_headers, nom="EXTPAT", prenom="Test", dob="1980-01-01", sexe="M"):
    r = client.post(
        "/api/patients/",
        json={"nom": nom, "prenom": prenom, "date_naissance": dob, "sexe": sexe},
        headers=auth_headers,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()


# ── helpers ───────────────────────────────────────────────────────────────────

class TestDossierNumberHelpers:
    def test_next_dossier_number_returns_number(self, client, auth_headers):
        r = client.get("/api/patients/next-dossier-number", headers=auth_headers)
        assert r.status_code == 200
        assert "next_number" in r.json()

    def test_next_dossier_number_requires_auth(self, client):
        r = client.get("/api/patients/next-dossier-number")
        assert r.status_code == 401

    def test_check_dossier_availability_not_exists(self, client, auth_headers):
        r = client.get("/api/patients/check-dossier/DOSSIER9999", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["exists"] is False
        assert body["patient_id"] is None

    def test_check_dossier_availability_exists(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="DOSSCHECK", prenom="Pat", dob="1975-03-15")
        numero = pat.get("numero_dossier")
        if numero:
            r = client.get(f"/api/patients/check-dossier/{numero}", headers=auth_headers)
            assert r.status_code == 200
            assert r.json()["exists"] is True


class TestDuplicateCheck:
    def test_no_duplicate(self, client, auth_headers):
        r = client.post(
            "/api/patients/check-duplicate",
            json={"nom": "Unique999", "prenom": "NoDup", "date_naissance": "1999-12-31"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["has_duplicate"] is False

    def test_detects_duplicate(self, client, auth_headers):
        _create_patient(client, auth_headers, nom="Duptest", prenom="Alpha", dob="1990-06-06")
        r = client.post(
            "/api/patients/check-duplicate",
            json={"nom": "Duptest", "prenom": "Alpha", "date_naissance": "1990-06-06"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["has_duplicate"] is True

    def test_duplicate_check_with_exclude_id(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Excludetest", prenom="Beta", dob="1991-08-08")
        r = client.post(
            "/api/patients/check-duplicate",
            json={
                "nom": "Excludetest",
                "prenom": "Beta",
                "date_naissance": "1991-08-08",
                "exclude_id": pat["id"],
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["has_duplicate"] is False

    def test_duplicate_check_requires_auth(self, client):
        r = client.post(
            "/api/patients/check-duplicate",
            json={"nom": "X", "prenom": "Y", "date_naissance": "2000-01-01"},
        )
        assert r.status_code == 401


# ── list / search ──────────────────────────────────────────────────────────────

class TestListPatients:
    def test_search_by_nom(self, client, auth_headers):
        _create_patient(client, auth_headers, nom="Searchtest", prenom="Zeta", dob="1970-04-12")
        r = client.get("/api/patients/?search=Searchtest", headers=auth_headers)
        assert r.status_code == 200
        results = r.json()
        assert any(p["nom"] == "SEARCHTEST" for p in results)

    def test_x_total_count_header(self, client, auth_headers):
        r = client.get("/api/patients/", headers=auth_headers)
        assert r.status_code == 200
        assert "x-total-count" in r.headers or "X-Total-Count" in r.headers

    def test_pagination_skip_limit(self, client, auth_headers):
        r = client.get("/api/patients/?skip=0&limit=1", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) <= 1


# ── create ─────────────────────────────────────────────────────────────────────

class TestCreatePatient:
    def test_create_normalizes_name(self, client, auth_headers):
        r = client.post(
            "/api/patients/",
            json={"nom": "benali", "prenom": "sara", "date_naissance": "1985-03-10", "sexe": "F"},
            headers=auth_headers,
        )
        assert r.status_code in (200, 201)
        body = r.json()
        assert body["nom"] == "BENALI"
        assert body["prenom"] == "Sara"

    def test_create_duplicate_returns_409_without_force(self, client, auth_headers):
        payload = {"nom": "Dupforce", "prenom": "Test", "date_naissance": "1982-11-11", "sexe": "M"}
        client.post("/api/patients/", json=payload, headers=auth_headers)
        r2 = client.post("/api/patients/", json=payload, headers=auth_headers)
        assert r2.status_code == 409

    def test_create_duplicate_allowed_with_force(self, client, auth_headers):
        payload = {"nom": "Dupforce2", "prenom": "Test", "date_naissance": "1983-12-12", "sexe": "M"}
        client.post("/api/patients/", json=payload, headers=auth_headers)
        r2 = client.post("/api/patients/?force_create=true", json=payload, headers=auth_headers)
        assert r2.status_code in (200, 201)

    def test_create_generates_dossier_number(self, client, auth_headers):
        r = client.post(
            "/api/patients/",
            json={"nom": "Dossiertest", "prenom": "Auto", "date_naissance": "1977-05-05", "sexe": "M"},
            headers=auth_headers,
        )
        assert r.status_code in (200, 201)
        assert r.json().get("numero_dossier") is not None


# ── get / update / delete ──────────────────────────────────────────────────────

class TestGetUpdateDelete:
    def test_update_patient_fields(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Updatetest", prenom="Field", dob="1969-01-01")
        r = client.put(
            f"/api/patients/{pat['id']}",
            json={"telephone": "0661112233"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["telephone"] == "0661112233"

    def test_update_nonexistent_patient_returns_404(self, client, auth_headers):
        r = client.put(
            "/api/patients/999999",
            json={"telephone": "0600000000"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_delete_patient_success(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Deletetest", prenom="Gone", dob="1994-09-09")
        r = client.delete(f"/api/patients/{pat['id']}", headers=auth_headers)
        assert r.status_code == 204

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete("/api/patients/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_delete_requires_auth(self, client):
        r = client.delete("/api/patients/1")
        assert r.status_code == 401


# ── sub-resources ──────────────────────────────────────────────────────────────

class TestPatientSubResources:
    def test_get_score(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Scoretest", prenom="Score", dob="1985-05-05")
        r = client.get(f"/api/patients/{pat['id']}/score", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "score" in body
        assert "grade" in body

    def test_patch_grade(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Gradetest", prenom="Manual", dob="1976-02-28")
        r = client.patch(
            f"/api/patients/{pat['id']}/grade",
            json={"grade": "GOLD", "comment": "Excellent patient"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_patch_ortho(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Orthotest", prenom="Ortho", dob="2000-06-15")
        r = client.patch(
            f"/api/patients/{pat['id']}/ortho",
            json={"is_ortho_active": True},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["is_ortho_active"] is True

    def test_get_documents(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Doctest", prenom="Docs", dob="1995-11-20")
        r = client.get(f"/api/patients/{pat['id']}/documents", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_appointment_intel(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Inteltest", prenom="Intel", dob="1979-08-08")
        r = client.get(f"/api/patients/{pat['id']}/appointment-intel", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "suggestion" in body
        assert "solde_attente" in body

    def test_get_analyses_empty(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Analystest", prenom="Ana", dob="1987-04-17")
        r = client.get(f"/api/patients/{pat['id']}/analyses", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_get_ai_summary(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Aisumtest", prenom="Aisum", dob="1991-12-25")
        r = client.get(f"/api/patients/{pat['id']}/ai-summary", headers=auth_headers)
        assert r.status_code == 200

    def test_get_master_plan_empty(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Plantest", prenom="Plan", dob="1983-07-07")
        r = client.get(f"/api/patients/{pat['id']}/master-plan", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() is None

    def test_update_master_plan(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Planupdate", prenom="Plan", dob="1984-08-08")
        steps = [
            {"title": "Détartrage", "assistant": "Hygiéniste", "status": "pending", "date_str": "2026-07"},
            {"title": "Composite", "assistant": "Dentiste", "status": "pending", "date_str": "2026-08"},
        ]
        r = client.put(
            f"/api/patients/{pat['id']}/master-plan",
            json=steps,
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "steps" in body
        assert len(body["steps"]) == 2


# ── bulk scores ────────────────────────────────────────────────────────────────

class TestBulkScores:
    def test_get_scores_returns_dict(self, client, auth_headers):
        r = client.get("/api/patients/scores", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_scores_requires_auth(self, client):
        r = client.get("/api/patients/scores")
        assert r.status_code == 401


# ── fantomes ───────────────────────────────────────────────────────────────────

class TestFantomes:
    def test_fantomes_returns_list(self, client, auth_headers):
        r = client.get("/api/patients/fantomes", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_fantomes_requires_auth(self, client):
        r = client.get("/api/patients/fantomes")
        assert r.status_code == 401


# ── CSV import ─────────────────────────────────────────────────────────────────

class TestCSVImport:
    def test_import_csv_valid(self, client, auth_headers):
        csv_content = (
            "nom,prenom,date_naissance,sexe\n"
            "Csvimport,Premier,1990-01-01,M\n"
            "Csvimport,Second,1991-02-02,F\n"
        )
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("patients.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "created" in body
        assert body["created"] >= 1

    def test_import_csv_duplicate_skipped(self, client, auth_headers):
        csv_content = (
            "nom,prenom,date_naissance,sexe\n"
            "Csvdup,One,1990-03-03,M\n"
        )
        client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            headers=auth_headers,
        )
        r2 = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            headers=auth_headers,
        )
        assert r2.status_code == 200
        assert r2.json()["skipped_duplicates"] >= 1

    def test_import_csv_missing_required_fields(self, client, auth_headers):
        csv_content = "nom,prenom\nNodob,Test\n"
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["created"] == 0
        assert len(body["errors"]) >= 1

    def test_import_csv_invalid_date(self, client, auth_headers):
        csv_content = "nom,prenom,date_naissance\nBaddate,Test,notadate\n"
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert len(body["errors"]) >= 1

    def test_import_csv_requires_auth(self, client):
        csv_content = "nom,prenom,date_naissance\nTest,Test,1990-01-01\n"
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 401

    def test_import_csv_semicolon_delimiter(self, client, auth_headers):
        csv_content = "nom;prenom;date_naissance;sexe\nSemicolon;Pat;1992-04-04;M\n"
        r = client.post(
            "/api/patients/import-csv",
            files={"file": ("p.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["created"] >= 1


# ── cephalo validation ─────────────────────────────────────────────────────────

class TestCephaloValidation:
    def test_cephalo_validation_no_analysis_returns_404(self, client, auth_headers):
        pat = _create_patient(client, auth_headers, nom="Cephnoana", prenom="Test", dob="1960-06-06")
        r = client.get(f"/api/patients/{pat['id']}/cephalo-validation", headers=auth_headers)
        assert r.status_code == 404


# ── multi-tenant isolation ─────────────────────────────────────────────────────

class TestMultiTenantPatients:
    def test_unauthenticated_patient_request_returns_401(self, client):
        r = client.get("/api/patients/12345")
        assert r.status_code == 401


# ── UNIFY-ACT-PERSISTENCE-1 : financial-snapshot / journey reflètent enfin un ──
# ── vrai reste dû pour un patient sans historique Acte legacy ──────────────────

class TestFinancialSnapshotAndJourneyReflectNewBilling:
    def test_financial_snapshot_reflects_new_document_billing(self, client, auth_headers, db):
        pat = _create_patient(client, auth_headers, nom="Snapshotpat", prenom="Test", dob="1990-01-01")
        req_data = {
            "type": "note",
            "patient_id": pat["id"],
            "is_accounted": True,
            "payment_status": "PARTIEL",
            "data": {
                "payments": [{"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 1000.0, "mode_reglement": "ESPECES"}],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp_gen = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp_gen.status_code == 200, resp_gen.text

        r = client.get(f"/api/patients/{pat['id']}/financial-snapshot", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        # Avant cette mission, total_billed aurait été 0 (aucune ligne Acte jamais créée
        # par ce flux) — désormais reflète le vrai montant facturé.
        assert body["total_billed"] == 1000.0
        assert body["total_collected"] == 500.0  # Payment lump-sum existant : total/2.0
        assert body["remaining_due"] == 500.0

    def test_journey_summary_has_billing_data_true_after_note(self, client, auth_headers, db):
        pat = _create_patient(client, auth_headers, nom="Journeypat", prenom="Test", dob="1990-01-01")
        req_data = {
            "type": "note",
            "patient_id": pat["id"],
            "is_accounted": True,
            "payment_status": "PAYE",
            "data": {
                "payments": [{"date": "2026-05-18", "acte": "Détartrage", "dent": "-", "montant": 400.0, "mode_reglement": "ESPECES"}],
                "doc_date": "2026-05-18",
                "teeth_data": [],
            },
        }
        resp_gen = client.post("/api/documents/generate", json=req_data, headers=auth_headers)
        assert resp_gen.status_code == 200, resp_gen.text

        r = client.get(f"/api/patients/{pat['id']}/journey", headers=auth_headers)
        assert r.status_code == 200
        summary = r.json()["summary"]
        assert summary["has_billing_data"] is True
        assert summary["remaining_due"] == 0.0
