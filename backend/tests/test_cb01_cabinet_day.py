"""CB-01 ONLY: canonical pilot cabinet day and display-only verified RDV identity."""
from datetime import datetime, timezone
from unittest.mock import patch

from backend import models
from backend.config import settings
from backend.routers.bot_workflows import cabinet_day_context


def test_same_utc_instant_yields_canonical_cabinet_day_across_timezone_changes():
    at = datetime(2026, 7, 15, 23, 30, tzinfo=timezone.utc)
    casablanca = cabinet_day_context(at_utc=at, timezone_name="Africa/Casablanca")
    new_york = cabinet_day_context(at_utc=at, timezone_name="America/New_York")
    assert casablanca == {
        "day": "2026-07-16", "timezone": "Africa/Casablanca",
        "start_date": "2026-07-16T00:00:00",
        "end_date": "2026-07-16T23:59:59.999", "consulted_at": "00:30",
    }
    assert new_york["day"] == "2026-07-15"
    assert new_york["consulted_at"] == "19:30"


def test_cabinet_day_endpoint_scoped_and_invalid_timezone_fails_closed(client, auth_headers):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), patch.object(
        settings, "CROWN_BOT_CABINET_TIMEZONE", "Africa/Casablanca"
    ):
        response = client.get("/api/bot/workflows/cabinet-day", headers=auth_headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["timezone"] == "Africa/Casablanca"
        assert data["start_date"] == data["day"] + "T00:00:00"
        assert data["end_date"] == data["day"] + "T23:59:59.999"
        assert len(data["consulted_at"]) == 5
        assert "patient" not in data
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), patch.object(
        settings, "CROWN_BOT_CABINET_TIMEZONE", "Invalid/Unknown-TZ"
    ):
        response = client.get("/api/bot/workflows/cabinet-day", headers=auth_headers)
        assert response.status_code == 503
        assert "patient" not in response.text.lower()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", False):
        response = client.get("/api/bot/workflows/cabinet-day", headers=auth_headers)
        assert response.status_code == 404


def test_rdv_homonym_patient_identity_is_revalidated_each_step(client, db, dentiste, auth_headers):
    for name, dossier in (("Amina", "C-101"), ("Salma", "C-102")):
        db.add(models.Patient(nom="Benali", prenom=name, numero_dossier=dossier,
            date_naissance=datetime(1990, 1, 1), sexe="F", employer_id=dentiste.id))
    db.commit()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        amb = client.post("/api/bot/workflows/preview", headers=auth_headers,
            json={"messages":["/rdv","Mme Benali"]})
        assert amb.status_code == 200, amb.text
        assert amb.json()["status"] == "disambiguation"
        selected = next(p for p in amb.json()["candidates"] if p["numero_dossier"]=="C-102")
        step = client.post("/api/bot/workflows/preview", headers=auth_headers,
            json={"messages":["/rdv", "id:" + str(selected["id"])]})
        assert step.status_code == 200, step.text
        assert step.json()["status"] == "clarification"
        assert step.json()["patient"]["numero_dossier"] == "C-102"
        assert step.json()["patient"]["prenom"] == "Salma"
        next_step = client.post("/api/bot/workflows/preview", headers=auth_headers,
            json={"messages":["/rdv","id:" + str(selected["id"]), "2027-01-10"]})
        assert next_step.status_code == 200, next_step.text
        assert next_step.json()["patient"]["numero_dossier"] == "C-102"
        assert next_step.json()["proposal"] is None
        # No CB-01 preview request creates any real appointment/pending action.
        assert db.query(models.Appointment).count() == 0
