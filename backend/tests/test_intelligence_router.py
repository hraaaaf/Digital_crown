"""Tests routers/intelligence.py — briefing, alerts, forecasts, patient intel."""
import pytest
from datetime import datetime, timedelta
from backend import models


def _make_patient(db, dentiste, nom="INTPAT", prenom="Test"):
    pat = models.Patient(
        nom=nom, prenom=prenom,
        date_naissance=datetime(1985, 3, 10),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


# ── auth guard ────────────────────────────────────────────────────────────────

class TestIntelligenceAuthGuard:
    def test_briefing_j1_requires_auth(self, client):
        r = client.get("/api/intelligence/briefing-j1")
        assert r.status_code == 401

    def test_briefing_today_requires_auth(self, client):
        r = client.get("/api/intelligence/briefing-today")
        assert r.status_code == 401

    def test_forecast_requires_auth(self, client):
        r = client.get("/api/intelligence/forecast-semaine")
        assert r.status_code == 401

    def test_alerts_today_requires_auth(self, client):
        r = client.get("/api/intelligence/alerts/today")
        assert r.status_code == 401

    def test_taux_conversion_requires_auth(self, client):
        r = client.get("/api/intelligence/taux-conversion")
        assert r.status_code == 401

    def test_latent_cash_requires_auth(self, client):
        r = client.get("/api/intelligence/latent-cash")
        assert r.status_code == 401

    def test_projection_requires_auth(self, client):
        r = client.get("/api/intelligence/projection-mensuelle")
        assert r.status_code == 401

    def test_distribution_assurances_requires_auth(self, client):
        r = client.get("/api/intelligence/distribution-assurances")
        assert r.status_code == 401


# ── briefing endpoints ─────────────────────────────────────────────────────────

class TestBriefings:
    def test_briefing_j1_returns_structure(self, client, auth_headers):
        r = client.get("/api/intelligence/briefing-j1", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "date" in body
        assert "total_patients" in body
        assert "patients" in body

    def test_briefing_today_returns_structure(self, client, auth_headers):
        r = client.get("/api/intelligence/briefing-today", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "date" in body
        assert "total_patients" in body
        assert "patients" in body

    def test_briefing_today_empty(self, client, auth_headers):
        r = client.get("/api/intelligence/briefing-today", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json()["patients"], list)


# ── forecast ───────────────────────────────────────────────────────────────────

class TestForecast:
    def test_forecast_semaine_structure(self, client, auth_headers):
        r = client.get("/api/intelligence/forecast-semaine", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "rdv_count" in body
        assert "forecast_revenue" in body
        assert "avg_per_rdv" in body

    def test_projection_mensuelle_structure(self, client, auth_headers):
        r = client.get("/api/intelligence/projection-mensuelle", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "historical" in body
        assert "projections" in body
        assert "avg_monthly" in body
        assert len(body["projections"]) == 6

    def test_taux_conversion_empty(self, client, auth_headers):
        r = client.get("/api/intelligence/taux-conversion", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "devis_count" in body
        assert "taux" in body

    def test_latent_cash_empty(self, client, auth_headers):
        r = client.get("/api/intelligence/latent-cash", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "total_opportunites" in body
        assert "opportunites" in body

    def test_distribution_assurances_returns_list(self, client, auth_headers):
        r = client.get("/api/intelligence/distribution-assurances", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ── alerts ─────────────────────────────────────────────────────────────────────

class TestAlerts:
    def test_alerts_today_returns_structure(self, client, auth_headers):
        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "alerts" in body
        assert isinstance(body["alerts"], list)

    def test_mark_nonexistent_alert_read_returns_404(self, client, auth_headers):
        r = client.patch("/api/intelligence/alerts/999999/read", headers=auth_headers)
        assert r.status_code == 404

    def test_mark_alert_read_success(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "ALERTPAT")
        alert = models.ProactiveAlert(
            employer_id=dentiste.id,
            patient_id=pat.id,
            alert_type="TEST",
            title="Test Alert",
            message="Test message",
            is_read=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        r = client.patch(f"/api/intelligence/alerts/{alert.id}/read", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ── patient-level intelligence ─────────────────────────────────────────────────

class TestPatientIntelligence:
    def test_get_patient_intelligence_requires_auth(self, client):
        r = client.get("/api/intelligence/patient/1")
        assert r.status_code == 401

    def test_get_patient_intelligence_licensed(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "INTELLPAT")
        r = client.get(f"/api/intelligence/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200

    def test_nba_no_triggers(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "NBAPAT")
        r = client.get(f"/api/intelligence/patient/{pat.id}/nba", headers=auth_headers)
        assert r.status_code == 200
        assert "nba" in r.json()

    def test_upcoming_prescription_no_appointment(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "UPCOMINGPAT")
        r = client.get(f"/api/intelligence/patient/{pat.id}/upcoming-prescription", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["upcoming"] is None

    def test_get_treatment_plan_patient(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "TREATPAT")
        r = client.get(f"/api/intelligence/patient/{pat.id}/treatment-plan", headers=auth_headers)
        assert r.status_code == 200

    def test_audit_document_context(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "AUDITPAT")
        r = client.post(
            f"/api/intelligence/patient/{pat.id}/audit?context_type=ordonnance",
            json={"items": []},
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_upcoming_prescription_with_appointment(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "UPCOMINGRDV")
        appt = models.Appointment(
            patient_id=pat.id,
            employer_id=dentiste.id,
            datetime_start=datetime.now() + timedelta(days=5),
            duration_minutes=30,
            motif="Controle",
            status=models.AppointmentStatus.PREVU,
        )
        db.add(appt)
        db.commit()
        r = client.get(f"/api/intelligence/patient/{pat.id}/upcoming-prescription", headers=auth_headers)
        assert r.status_code == 200


def _make_appt(db, dentiste, pat, dt):
    from backend import models
    appt = models.Appointment(
        patient_id=pat.id,
        patient_name=f"{pat.nom} {pat.prenom}",
        datetime_start=dt,
        duration_minutes=30,
        status=models.AppointmentStatus.PREVU,
        employer_id=dentiste.id,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


# ── briefing-j1 ───────────────────────────────────────────────────────────────

class TestBriefingJ1:
    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/briefing-j1")
        assert r.status_code == 401

    def test_empty_tomorrow_returns_zero_patients(self, client, auth_headers):
        r = client.get("/api/intelligence/briefing-j1", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "date" in body
        assert "total_patients" in body
        assert "total_outstanding" in body
        assert "patients" in body

    def test_with_tomorrow_appointment(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "BRIEFJ1", "Pat")
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_noon = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        _make_appt(db, dentiste, pat, tomorrow_noon)

        r = client.get("/api/intelligence/briefing-j1", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_patients"] >= 1
        patient_ids = [p["patient_id"] for p in body["patients"]]
        assert pat.id in patient_ids


# ── briefing-today ────────────────────────────────────────────────────────────

class TestBriefingToday:
    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/briefing-today")
        assert r.status_code == 401

    def test_empty_today_returns_empty_list(self, client, auth_headers):
        r = client.get("/api/intelligence/briefing-today", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "date" in body
        assert "total_patients" in body
        assert isinstance(body["patients"], list)

    def test_with_today_appointment(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "TODAYBRF", "Pat")
        today_noon = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0)
        _make_appt(db, dentiste, pat, today_noon)

        r = client.get("/api/intelligence/briefing-today", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_patients"] >= 1


# ── forecast-semaine ──────────────────────────────────────────────────────────

class TestForecastSemaine:
    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/forecast-semaine")
        assert r.status_code == 401

    def test_returns_forecast_structure(self, client, auth_headers):
        r = client.get("/api/intelligence/forecast-semaine", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "week_start" in body
        assert "week_end" in body
        assert "rdv_count" in body
        assert "forecast_revenue" in body
        assert "avg_per_rdv" in body

    def test_forecast_revenue_non_negative(self, client, auth_headers):
        r = client.get("/api/intelligence/forecast-semaine", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["forecast_revenue"] >= 0


# ── patient intelligence ──────────────────────────────────────────────────────

class TestPatientIntelligence2:
    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/patient/1")
        assert r.status_code == 401

    def test_patient_not_found_returns_403_or_404(self, client, auth_headers):
        r = client.get("/api/intelligence/patient/999999", headers=auth_headers)
        assert r.status_code in (403, 404)

    def test_valid_patient_returns_200(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "INTEL2", "Pat")
        r = client.get(f"/api/intelligence/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200

    def test_treatment_plan_requires_auth(self, client):
        r = client.get("/api/intelligence/patient/1/treatment-plan")
        assert r.status_code == 401

    def test_treatment_plan_valid_patient(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PLANPAT2", "Plan")
        r = client.get(f"/api/intelligence/patient/{pat.id}/treatment-plan", headers=auth_headers)
        assert r.status_code == 200


# ── alerts today ─────────────────────────────────────────────────────────────

class TestAlertsToday:
    def _make_alert(self, db, dentiste, patient_id, read=False):
        from backend import models
        alert = models.ProactiveAlert(
            employer_id=dentiste.id,
            patient_id=patient_id,
            alert_type="RAPPEL_RDV",
            title="Rappel RDV",
            message="Patient sans RDV depuis 6 mois",
            action="book_appointment",
            priority=1,
            is_read=read,
            created_at=datetime.now(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/alerts/today")
        assert r.status_code == 401

    def test_empty_returns_zero(self, client, auth_headers):
        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "total" in body
        assert "alerts" in body
        assert isinstance(body["alerts"], list)

    def test_unread_alert_appears(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "ALERTPAT")
        self._make_alert(db, dentiste, pat.id, read=False)

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        alert_ids = [a["patient_id"] for a in body["alerts"]]
        assert pat.id in alert_ids

    def test_alert_with_null_patient_does_not_crash(self, client, db, auth_headers, dentiste):
        # Alertes cabinet (ex. stock) : daily_scheduler.py crée patient_id=None —
        # la route ne doit jamais planter dessus (bug audit fonctionnel 2026-07-12).
        alert = models.ProactiveAlert(
            employer_id=dentiste.id,
            patient_id=None,
            alert_type="STOCK_COMPOSITE",
            title="⚠️ Stock — composites",
            message="4 composites prévus cette semaine.",
            action="/settings",
            priority=1,
            is_read=False,
            created_at=datetime.now(),
        )
        db.add(alert)
        db.commit()

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        matching = [a for a in body["alerts"] if a["id"] == alert.id]
        assert len(matching) == 1
        assert matching[0]["patient_id"] is None
        assert matching[0]["nom"] is None
        assert matching[0]["prenom"] is None
        assert matching[0]["title"] == "⚠️ Stock — composites"

    def test_old_unread_alert_still_visible(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "OLDUNREAD")
        alert = self._make_alert(db, dentiste, pat.id, read=False)
        alert.created_at = datetime.now() - timedelta(days=2)
        alert.expires_at = datetime.now() + timedelta(days=5)
        db.commit()

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        alert_ids = [a["id"] for a in r.json()["alerts"]]
        assert alert.id in alert_ids

    def test_expired_alert_not_included(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "EXPIRED")
        alert = self._make_alert(db, dentiste, pat.id, read=False)
        alert.expires_at = datetime.now() - timedelta(hours=1)
        db.commit()

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        alert_ids = [a["id"] for a in r.json()["alerts"]]
        assert alert.id not in alert_ids

    def test_read_alert_not_included(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "ALERTREAD")
        self._make_alert(db, dentiste, pat.id, read=True)

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        # The read alert should NOT appear
        pids = [a["patient_id"] for a in r.json()["alerts"]]
        assert pat.id not in pids

    def test_alert_fields_present(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "ALERTFLD")
        self._make_alert(db, dentiste, pat.id)

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        alerts = r.json()["alerts"]
        found = next((a for a in alerts if a["patient_id"] == pat.id), None)
        assert found is not None
        for field in ("id", "patient_id", "nom", "prenom", "type", "title", "message", "priority"):
            assert field in found

    def test_alert_for_soft_deleted_patient_excluded(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "SOFTDELPAT")
        self._make_alert(db, dentiste, pat.id, read=False)
        pat.deleted_at = datetime.now()
        db.commit()

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        pids = [a["patient_id"] for a in r.json()["alerts"]]
        assert pat.id not in pids

    def test_snoozed_alert_excluded_until_expiry(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "SNOOZEDPAT")
        alert = self._make_alert(db, dentiste, pat.id, read=False)
        alert.snoozed_until = datetime.now() + timedelta(hours=1)
        db.commit()

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        alert_ids = [a["id"] for a in r.json()["alerts"]]
        assert alert.id not in alert_ids

    def test_past_snooze_alert_included(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "PASTSNOOZEPAT")
        alert = self._make_alert(db, dentiste, pat.id, read=False)
        alert.snoozed_until = datetime.now() - timedelta(hours=1)
        db.commit()

        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        assert r.status_code == 200
        alert_ids = [a["id"] for a in r.json()["alerts"]]
        assert alert.id in alert_ids


# ── mark alert read ──────────────────────────────────────────────────────────

class TestMarkAlertRead:
    def _make_alert(self, db, dentiste, patient_id):
        from backend import models
        alert = models.ProactiveAlert(
            employer_id=dentiste.id,
            patient_id=patient_id,
            alert_type="RAPPEL",
            title="Test",
            message="Message",
            is_read=False,
            created_at=datetime.now(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def test_requires_auth(self, client):
        r = client.patch("/api/intelligence/alerts/1/read")
        assert r.status_code == 401

    def test_mark_nonexistent_returns_404(self, client, auth_headers):
        r = client.patch("/api/intelligence/alerts/999999/read", headers=auth_headers)
        assert r.status_code == 404

    def test_mark_alert_read_returns_ok(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "MARKREAD")
        alert = self._make_alert(db, dentiste, pat.id)

        r = client.patch(f"/api/intelligence/alerts/{alert.id}/read", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_alert_no_longer_in_today_after_read(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "AFTERREAD")
        alert = self._make_alert(db, dentiste, pat.id)

        client.patch(f"/api/intelligence/alerts/{alert.id}/read", headers=auth_headers)
        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        pids = [a["patient_id"] for a in r.json()["alerts"]]
        assert pat.id not in pids


# ── snooze alert ──────────────────────────────────────────────────────────────

class TestSnoozeAlert:
    def _make_alert(self, db, dentiste, patient_id, expires_at=None):
        from backend import models
        alert = models.ProactiveAlert(
            employer_id=dentiste.id,
            patient_id=patient_id,
            alert_type="RAPPEL",
            title="Test",
            message="Message",
            is_read=False,
            created_at=datetime.now(),
            expires_at=expires_at,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def test_requires_auth(self, client):
        r = client.patch("/api/intelligence/alerts/1/snooze")
        assert r.status_code == 401

    def test_snooze_nonexistent_returns_404(self, client, auth_headers):
        r = client.patch("/api/intelligence/alerts/999999/snooze", headers=auth_headers)
        assert r.status_code == 404

    def test_snooze_alert_returns_ok_and_sets_snoozed_until(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "SNOOZEOK")
        alert = self._make_alert(db, dentiste, pat.id)

        r = client.patch(f"/api/intelligence/alerts/{alert.id}/snooze", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "snoozed_until" in body
        db.refresh(alert)
        assert alert.snoozed_until is not None
        assert alert.snoozed_until > datetime.now() + timedelta(hours=23)

    def test_snoozed_alert_not_in_today_after_snooze(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "SNOOZEAFTER")
        alert = self._make_alert(db, dentiste, pat.id)

        client.patch(f"/api/intelligence/alerts/{alert.id}/snooze", headers=auth_headers)
        r = client.get("/api/intelligence/alerts/today", headers=auth_headers)
        alert_ids = [a["id"] for a in r.json()["alerts"]]
        assert alert.id not in alert_ids

    def test_snooze_extends_expiry_if_needed(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "SNOOZEEXPIRY")
        near_expiry = datetime.now() + timedelta(hours=2)
        alert = self._make_alert(db, dentiste, pat.id, expires_at=near_expiry)

        r = client.patch(f"/api/intelligence/alerts/{alert.id}/snooze", headers=auth_headers)
        assert r.status_code == 200
        db.refresh(alert)
        assert alert.expires_at > alert.snoozed_until


# ── patient NBA ───────────────────────────────────────────────────────────────

class TestPatientNBA:
    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/patient/1/nba")
        assert r.status_code == 401

    def test_foreign_patient_returns_403_or_404(self, client, auth_headers):
        r = client.get("/api/intelligence/patient/999999/nba", headers=auth_headers)
        assert r.status_code in (403, 404)

    def test_nba_returns_nba_key(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "NBAPAT")
        r = client.get(f"/api/intelligence/patient/{pat.id}/nba", headers=auth_headers)
        assert r.status_code == 200
        assert "nba" in r.json()

    def test_nba_value_is_none_or_dict(self, client, db, auth_headers, dentiste):
        pat = _make_patient(db, dentiste, "NBAPAT2")
        r = client.get(f"/api/intelligence/patient/{pat.id}/nba", headers=auth_headers)
        assert r.status_code == 200
        nba = r.json()["nba"]
        assert nba is None or isinstance(nba, dict)


# ── taux-conversion ──────────────────────────────────────────────────────────

class TestTauxConversion:
    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/taux-conversion")
        assert r.status_code == 401

    def test_no_devis_returns_zero(self, client, auth_headers):
        r = client.get("/api/intelligence/taux-conversion", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["devis_count"] == 0
        assert body["taux"] == 0.0
        assert body["avg_days"] is None

    def test_with_devis_returns_structure(self, client, db, auth_headers, dentiste):
        from backend import models
        import uuid
        pat = _make_patient(db, dentiste, "DEVISCONV")
        doc = models.DocumentArchive(
            patient_id=pat.id,
            document_type=models.DocumentType.DEVIS,
            filename="devis.pdf",
            original_filename="devis.pdf",
            document_group_id=str(uuid.uuid4()),
            file_hash="abc123",
            file_size=100,
            file_path="/tmp/devis.pdf",
            created_at=datetime.now() - timedelta(days=5),
        )
        db.add(doc)
        db.commit()

        r = client.get("/api/intelligence/taux-conversion", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["devis_count"] >= 1
        assert "converted_count" in body
        assert "taux" in body


# ── latent cash ───────────────────────────────────────────────────────────────

class TestLatentCash:
    def test_requires_auth(self, client):
        r = client.get("/api/intelligence/latent-cash")
        assert r.status_code == 401

    def test_no_dormant_devis_returns_empty(self, client, auth_headers):
        r = client.get("/api/intelligence/latent-cash", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "total_opportunites" in body
        assert "valeur_totale_latente" in body
        assert isinstance(body["opportunites"], list)
