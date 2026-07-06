"""Tests for smaller routers: analytics, medications, agenda_settings, lab_jobs."""
from datetime import datetime, timedelta


# ── analytics ─────────────────────────────────────────────────────────────────

class TestAnalyticsFinancial:
    def test_requires_auth(self, client):
        r = client.get("/api/analytics/financial")
        assert r.status_code == 401

    def test_empty_db_returns_zeros(self, client, auth_headers):
        r = client.get("/api/analytics/financial", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "revenue_this_month" in body
        assert "revenue_last_month" in body
        assert "monthly_revenue" in body
        assert "recovery_rate" in body
        assert "top_acts_revenue" in body
        assert "top_acts_frequency" in body
        assert len(body["monthly_revenue"]) == 6
        assert body["revenue_this_month"] == 0.0
        assert body["recovery_rate"] == 100.0  # no bills = 100% recovery

    def test_recovery_rate_with_payments(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="ANALYTICS", prenom="Test",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        db.add(models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.SOIN, libelle="Consultation",
            montant=3000.0, statut_paiement=models.PaiementStatut.PAYE,
            date_debut=datetime.now(),
        ))
        db.add(models.Payment(
            patient_id=pat.id,
            amount=3000.0,
            payment_method="ESPECES",
            payment_date=datetime.now(),
        ))
        db.commit()

        r = client.get("/api/analytics/financial", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["revenue_this_month"] >= 3000.0
        assert body["total_billed"] >= 3000.0
        assert body["recovery_rate"] == 100.0


# ── medications ───────────────────────────────────────────────────────────────

class TestMedicationsSearch:
    def test_requires_auth(self, client):
        r = client.get("/api/medications/search", params={"q": "amoxicilline"})
        assert r.status_code == 401

    def test_search_returns_list(self, client, auth_headers):
        r = client.get("/api/medications/search", params={"q": "amox"}, headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_search_min_length(self, client, auth_headers):
        # min_length=2 → single char should fail validation
        r = client.get("/api/medications/search", params={"q": "a"}, headers=auth_headers)
        assert r.status_code == 422


class TestMedicationsValidate:
    def test_requires_auth(self, client):
        r = client.get("/api/medications/validate", params={"name": "Amoxicilline"})
        assert r.status_code == 401

    def test_validate_returns_result(self, client, auth_headers):
        r = client.get(
            "/api/medications/validate",
            params={"name": "Amoxicilline", "dosage": "500 mg"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_validate_no_dosage(self, client, auth_headers):
        r = client.get(
            "/api/medications/validate",
            params={"name": "Ibuprofene"},
            headers=auth_headers,
        )
        assert r.status_code == 200


# ── agenda settings ───────────────────────────────────────────────────────────

class TestAgendaSettings:
    def test_get_settings_requires_auth(self, client):
        r = client.get("/api/agenda/settings")
        assert r.status_code == 401

    def test_get_settings_creates_default(self, client, auth_headers):
        r = client.get("/api/agenda/settings", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "id" in body

    def test_update_settings(self, client, auth_headers):
        # First ensure settings exist
        client.get("/api/agenda/settings", headers=auth_headers)
        # Then update
        r = client.put(
            "/api/agenda/settings",
            json={"slot_duration": 30, "working_days": [1, 2, 3, 4, 5]},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_list_exceptions_requires_auth(self, client):
        r = client.get("/api/agenda/exceptions")
        assert r.status_code == 401

    def test_list_exceptions_empty(self, client, auth_headers):
        r = client.get("/api/agenda/exceptions", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_and_delete_exception(self, client, auth_headers):
        start = (datetime.now() + timedelta(days=5)).isoformat()
        end = (datetime.now() + timedelta(days=5, hours=8)).isoformat()
        payload = {
            "start_date": start,
            "end_date": end,
            "reason": "Congrès dentaire",
            "is_holiday": False,
        }
        r = client.post("/api/agenda/exceptions", json=payload, headers=auth_headers)
        assert r.status_code == 200
        exc_id = r.json()["id"]

        r_del = client.delete(f"/api/agenda/exceptions/{exc_id}", headers=auth_headers)
        assert r_del.status_code == 204

    def test_delete_nonexistent_exception_returns_404(self, client, auth_headers):
        r = client.delete("/api/agenda/exceptions/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_upcoming_holidays_public(self, client):
        r = client.get("/api/agenda/upcoming-holidays")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ── lab jobs ──────────────────────────────────────────────────────────────────

class TestLabJobs:
    def test_list_requires_auth(self, client):
        r = client.get("/api/lab-jobs/")
        assert r.status_code == 401

    def test_list_empty(self, client, auth_headers):
        r = client.get("/api/lab-jobs/", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_lab_job(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="LABTEST", prenom="Job",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        acte = models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.PROTHESE, libelle="Couronne",
            montant=5000.0, statut_paiement=models.PaiementStatut.EN_ATTENTE,
            date_debut=datetime.now(),
        )
        db.add(acte)
        db.commit()
        db.refresh(acte)

        payload = {
            "patient_id": pat.id,
            "act_id": acte.id,
            "material": "Céramique",
            "type": "COURONNE",
            "deadline": (datetime.now() + timedelta(days=14)).isoformat(),
        }
        r = client.post("/api/lab-jobs/", json=payload, headers=auth_headers)
        assert r.status_code == 201
        assert "id" in r.json()

    def test_update_lab_job_status(self, client, db, auth_headers, dentiste):
        from backend import models

        pat = models.Patient(
            nom="LABUPD", prenom="Status",
            date_naissance=datetime(1990, 1, 1),
            sexe="M",
            employer_id=dentiste.id,
        )
        db.add(pat)
        db.flush()
        db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
        db.commit()
        db.refresh(pat)

        acte = models.Acte(
            patient_id=pat.id, praticien_id=dentiste.id,
            type_acte=models.ActeType.PROTHESE, libelle="Bridge",
            montant=10000.0, statut_paiement=models.PaiementStatut.EN_ATTENTE,
            date_debut=datetime.now(),
        )
        db.add(acte)
        db.commit()
        db.refresh(acte)

        job = models.LabJob(
            patient_id=pat.id,
            act_id=acte.id,
            material="Zircone",
            type="BRIDGE",
            deadline=datetime.now() + timedelta(days=10),
            status=models.LabJobStatus.PRESCRIPTION,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        r = client.patch(
            f"/api/lab-jobs/{job.id}",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_update_nonexistent_job_returns_404(self, client, auth_headers):
        r = client.patch(
            "/api/lab-jobs/999999",
            json={"status": "EN_COURS"},
            headers=auth_headers,
        )
        assert r.status_code == 404
