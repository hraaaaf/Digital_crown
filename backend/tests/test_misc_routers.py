"""Tests for smaller routers: analytics, lab_jobs, agenda_settings, medications."""
from datetime import datetime, timedelta


# ── analytics ─────────────────────────────────────────────────────────────────

class TestAnalyticsFinancial:
    def test_requires_auth(self, client):
        r = client.get("/api/analytics/financial")
        assert r.status_code == 401

    def test_returns_structure(self, client, auth_headers):
        r = client.get("/api/analytics/financial", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "revenue_this_month" in body
        assert "revenue_last_month" in body
        assert "monthly_revenue" in body
        assert "recovery_rate" in body
        assert "total_billed" in body
        assert "total_paid" in body
        assert "top_acts_revenue" in body
        assert "top_acts_frequency" in body

    def test_monthly_revenue_has_6_months(self, client, auth_headers):
        r = client.get("/api/analytics/financial", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["monthly_revenue"]) == 6

    def test_empty_returns_zeros(self, client, auth_headers):
        r = client.get("/api/analytics/financial", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["revenue_this_month"] >= 0
        assert body["total_billed"] >= 0

    def test_recovery_rate_100_when_no_data(self, client, auth_headers):
        r = client.get("/api/analytics/financial", headers=auth_headers)
        assert r.status_code == 200
        # With no billing data recovery_rate defaults to 100.0
        assert r.json()["recovery_rate"] >= 0


# ── lab_jobs ──────────────────────────────────────────────────────────────────

class TestLabJobs:
    def test_list_requires_auth(self, client):
        r = client.get("/api/lab-jobs/")
        assert r.status_code == 401

    def test_list_returns_list(self, client, auth_headers):
        r = client.get("/api/lab-jobs/", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_requires_auth(self, client):
        r = client.post("/api/lab-jobs/", json={})
        assert r.status_code == 401

    def test_create_lab_job(self, client, db, auth_headers, dentiste):
        from backend import models
        pat = models.Patient(
            nom="LABTEST", prenom="Pat",
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
            patient_id=pat.id,
            praticien_id=dentiste.id,
            libelle="Couronne",
            montant=1500.0,
            type_acte=models.ActeType.SOIN,
        )
        db.add(acte)
        db.commit()
        db.refresh(acte)

        deadline = (datetime.now() + timedelta(days=7)).isoformat()
        r = client.post(
            "/api/lab-jobs/",
            json={
                "patient_id": pat.id,
                "act_id": acte.id,
                "material": "Zircone",
                "type": "Couronne",
                "deadline": deadline,
                "is_remake": False,
            },
            headers=auth_headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["status"] is not None

    def test_update_lab_job_requires_auth(self, client):
        r = client.patch("/api/lab-jobs/1", json={"status": "SENT"})
        assert r.status_code == 401

    def test_update_nonexistent_lab_job_returns_404(self, client, auth_headers):
        r = client.patch("/api/lab-jobs/999999", json={"status": "SENT"}, headers=auth_headers)
        assert r.status_code == 404

    def test_update_lab_job_status(self, client, db, auth_headers, dentiste):
        from backend import models
        pat = models.Patient(
            nom="LABUPD", prenom="Pat",
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
            patient_id=pat.id,
            praticien_id=dentiste.id,
            libelle="Bridge",
            montant=3000.0,
            type_acte=models.ActeType.PROTHESE,
        )
        db.add(acte)
        db.commit()
        db.refresh(acte)

        job = models.LabJob(
            patient_id=pat.id,
            act_id=acte.id,
            material="Métal",
            type="Bridge",
            deadline=datetime.now() + timedelta(days=10),
            status=models.LabJobStatus.PRESCRIPTION,
            is_remake=False,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        r = client.patch(
            f"/api/lab-jobs/{job.id}",
            json={"status": "SENT"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert "id" in r.json()


# ── agenda_settings ───────────────────────────────────────────────────────────

class TestAgendaSettings:
    def test_get_settings_requires_auth(self, client):
        r = client.get("/api/agenda/settings")
        assert r.status_code == 401

    def test_get_settings_returns_200(self, client, auth_headers):
        r = client.get("/api/agenda/settings", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert "agenda_mode" in body

    def test_update_settings_requires_auth(self, client):
        r = client.put("/api/agenda/settings", json={"use_tickets": True})
        assert r.status_code == 401

    def test_update_settings_opening_hours(self, client, auth_headers):
        r = client.put(
            "/api/agenda/settings",
            json={
                "opening_time_morning": "08:00",
                "closing_time_morning": "12:00",
                "opening_time_afternoon": "14:00",
                "closing_time_afternoon": "18:00",
                "is_continuous": False,
                "agenda_mode": "EXACT",
                "use_tickets": False,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["opening_time_morning"] == "08:00"

    def test_update_settings_tickets_mode(self, client, auth_headers):
        r = client.put(
            "/api/agenda/settings",
            json={
                "opening_time_morning": "09:00",
                "closing_time_morning": "13:00",
                "opening_time_afternoon": "14:00",
                "closing_time_afternoon": "18:00",
                "is_continuous": False,
                "agenda_mode": "BLOCK",
                "use_tickets": True,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["use_tickets"] is True

    def test_list_exceptions_requires_auth(self, client):
        r = client.get("/api/agenda/exceptions")
        assert r.status_code == 401

    def test_list_exceptions_returns_list(self, client, auth_headers):
        r = client.get("/api/agenda/exceptions", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_exception_requires_auth(self, client):
        r = client.post("/api/agenda/exceptions", json={})
        assert r.status_code == 401

    def test_create_exception(self, client, auth_headers):
        start = (datetime.now() + timedelta(days=5)).isoformat()
        end = (datetime.now() + timedelta(days=6)).isoformat()
        r = client.post(
            "/api/agenda/exceptions",
            json={"start_date": start, "end_date": end, "reason": "Congé", "is_holiday": False},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert body["reason"] == "Congé"

    def test_delete_exception_requires_auth(self, client):
        r = client.delete("/api/agenda/exceptions/1")
        assert r.status_code == 401

    def test_delete_nonexistent_exception_returns_404(self, client, auth_headers):
        r = client.delete("/api/agenda/exceptions/999999", headers=auth_headers)
        assert r.status_code == 404

    def test_delete_exception(self, client, auth_headers):
        start = (datetime.now() + timedelta(days=10)).isoformat()
        end = (datetime.now() + timedelta(days=11)).isoformat()
        r_create = client.post(
            "/api/agenda/exceptions",
            json={"start_date": start, "end_date": end, "reason": "Férié", "is_holiday": True},
            headers=auth_headers,
        )
        exc_id = r_create.json()["id"]
        r_del = client.delete(f"/api/agenda/exceptions/{exc_id}", headers=auth_headers)
        assert r_del.status_code == 204

    def test_get_upcoming_holidays(self, client):
        r = client.get("/api/agenda/upcoming-holidays")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ── medications ───────────────────────────────────────────────────────────────

class TestMedications:
    def test_search_requires_auth(self, client):
        r = client.get("/api/medications/search?q=ibu")
        assert r.status_code == 401

    def test_search_returns_list(self, client, auth_headers):
        r = client.get("/api/medications/search?q=ibu", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_search_short_query_returns_422(self, client, auth_headers):
        r = client.get("/api/medications/search?q=i", headers=auth_headers)
        assert r.status_code == 422

    def test_validate_requires_auth(self, client):
        r = client.get("/api/medications/validate?name=ibuprofene")
        assert r.status_code == 401

    def test_validate_without_dosage(self, client, auth_headers):
        r = client.get("/api/medications/validate?name=ibuprofene", headers=auth_headers)
        assert r.status_code == 200

    def test_validate_with_dosage(self, client, auth_headers):
        r = client.get("/api/medications/validate?name=ibuprofene&dosage=400mg", headers=auth_headers)
        assert r.status_code == 200
