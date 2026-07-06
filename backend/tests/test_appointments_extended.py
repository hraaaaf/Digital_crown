"""Tests routers/appointments.py — bulk, suggest, reminders/send, patient list."""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


BASE = "/api/appointments"


def _mk_appt_payload(days_offset=5, patient_name="Test Pat", duration=30):
    dt = (datetime.now() + timedelta(days=days_offset)).replace(second=0, microsecond=0)
    return {
        "datetime_start": dt.isoformat(),
        "duration_minutes": duration,
        "patient_name": patient_name,
        "status": "PRÉVU",
    }


def _create_patient(db, dentiste):
    from backend import models
    pat = models.Patient(
        nom="APPTEXTPAT", prenom="Test",
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


class TestBulkCreate:
    def test_bulk_requires_auth(self, client):
        r = client.post(f"{BASE}/bulk", json={"appointments": []})
        assert r.status_code == 401

    def test_bulk_empty_list_returns_200(self, client, auth_headers):
        r = client.post(f"{BASE}/bulk", json={"appointments": []}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_bulk_creates_multiple(self, client, auth_headers):
        dt1 = (datetime.now() + timedelta(days=30)).replace(second=0, microsecond=0)
        dt2 = (datetime.now() + timedelta(days=31)).replace(second=0, microsecond=0)
        payload = {
            "appointments": [
                {
                    "datetime_start": dt1.isoformat(),
                    "duration_minutes": 30,
                    "patient_name": "Bulk Pat A",
                    "status": "PRÉVU",
                    "scheduling_type": "EXACT_TIME",
                },
                {
                    "datetime_start": dt2.isoformat(),
                    "duration_minutes": 45,
                    "patient_name": "Bulk Pat B",
                    "status": "PRÉVU",
                    "scheduling_type": "EXACT_TIME",
                },
            ]
        }
        r = client.post(f"{BASE}/bulk", json=payload, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 2
        names = {a["patient_name"] for a in body}
        assert "Bulk Pat A" in names
        assert "Bulk Pat B" in names

    def test_bulk_single_item(self, client, auth_headers):
        dt = (datetime.now() + timedelta(days=40)).replace(second=0, microsecond=0)
        payload = {
            "appointments": [
                {
                    "datetime_start": dt.isoformat(),
                    "duration_minutes": 20,
                    "patient_name": "Solo Bulk",
                    "status": "PRÉVU",
                    "scheduling_type": "EXACT_TIME",
                }
            ]
        }
        r = client.post(f"{BASE}/bulk", json=payload, headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["duration_minutes"] == 20

    def test_bulk_with_linked_patient(self, client, db, auth_headers, dentiste):
        pat = _create_patient(db, dentiste)
        dt = (datetime.now() + timedelta(days=50)).replace(second=0, microsecond=0)
        payload = {
            "appointments": [
                {
                    "datetime_start": dt.isoformat(),
                    "duration_minutes": 30,
                    "patient_name": f"{pat.nom} {pat.prenom}",
                    "patient_id": pat.id,
                    "status": "PRÉVU",
                    "scheduling_type": "EXACT_TIME",
                }
            ]
        }
        r = client.post(f"{BASE}/bulk", json=payload, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["patient_id"] == pat.id

    def test_bulk_assigns_employer_id(self, client, auth_headers, dentiste):
        dt = (datetime.now() + timedelta(days=60)).replace(second=0, microsecond=0)
        payload = {
            "appointments": [
                {
                    "datetime_start": dt.isoformat(),
                    "duration_minutes": 30,
                    "patient_name": "EmpCheck",
                    "status": "PRÉVU",
                    "scheduling_type": "EXACT_TIME",
                }
            ]
        }
        r = client.post(f"{BASE}/bulk", json=payload, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()[0]["employer_id"] == dentiste.id


class TestRemindersEndpoint:
    def test_trigger_reminders_requires_auth(self, client):
        r = client.post(f"{BASE}/reminders/send")
        assert r.status_code == 401

    def test_trigger_reminders_returns_count(self, client, auth_headers):
        with patch(
            "backend.services.notification_service.notification_service.cron_send_reminders",
            return_value=3,
        ):
            r = client.post(f"{BASE}/reminders/send", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "success"
        assert body["reminders_sent"] == 3

    def test_trigger_reminders_zero_sent(self, client, auth_headers):
        with patch(
            "backend.services.notification_service.notification_service.cron_send_reminders",
            return_value=0,
        ):
            r = client.post(f"{BASE}/reminders/send", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["reminders_sent"] == 0


class TestSuggestAppointment:
    def test_suggest_requires_auth(self, client, db, dentiste):
        pat = _create_patient(db, dentiste)
        r = client.get(f"{BASE}/suggest/{pat.id}")
        assert r.status_code == 401

    def test_suggest_invalid_patient_returns_403_or_404(self, client, auth_headers):
        r = client.get(f"{BASE}/suggest/999999", headers=auth_headers)
        assert r.status_code in (403, 404)

    def test_suggest_no_plan_returns_generic(self, client, db, auth_headers, dentiste):
        pat = _create_patient(db, dentiste)
        with patch(
            "backend.services.elite_manager.elite_manager.get_treatment_plan",
            return_value={},
        ):
            r = client.get(f"{BASE}/suggest/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["patient_id"] == pat.id
        assert "duration_minutes" in body
        assert body["duration_minutes"] == 15

    def test_suggest_with_plan_returns_first_act(self, client, db, auth_headers, dentiste):
        pat = _create_patient(db, dentiste)
        plan = {
            "phases": {
                "INITIALE": [{"suggested_act": "Détartrage complet"}],
            }
        }
        with patch(
            "backend.services.elite_manager.elite_manager.get_treatment_plan",
            return_value=plan,
        ):
            r = client.get(f"{BASE}/suggest/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["patient_id"] == pat.id
        assert body["motif"] == "Détartrage complet"
        assert body["duration_minutes"] == 20

    def test_suggest_implant_gets_45min(self, client, db, auth_headers, dentiste):
        pat = _create_patient(db, dentiste)
        plan = {
            "phases": {
                "REHABILITATION": [{"suggested_act": "Pose implant unitaire"}],
            }
        }
        with patch(
            "backend.services.elite_manager.elite_manager.get_treatment_plan",
            return_value=plan,
        ):
            r = client.get(f"{BASE}/suggest/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["duration_minutes"] == 45

    def test_suggest_urgent_phase_first(self, client, db, auth_headers, dentiste):
        """URGENCE phase is first in the order — should be returned before INITIALE."""
        pat = _create_patient(db, dentiste)
        plan = {
            "phases": {
                "INITIALE": [{"suggested_act": "Bilan"}],
                "URGENCE": [{"suggested_act": "Extraction urgence"}],
            }
        }
        with patch(
            "backend.services.elite_manager.elite_manager.get_treatment_plan",
            return_value=plan,
        ):
            r = client.get(f"{BASE}/suggest/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["motif"] == "Extraction urgence"


class TestPatientAppointments:
    def test_list_requires_auth(self, client, db, dentiste):
        pat = _create_patient(db, dentiste)
        r = client.get(f"{BASE}/patient/{pat.id}")
        assert r.status_code == 401

    def test_list_invalid_patient_forbidden(self, client, auth_headers):
        r = client.get(f"{BASE}/patient/999999", headers=auth_headers)
        assert r.status_code in (403, 404)

    def test_list_returns_appointments(self, client, db, auth_headers, dentiste):
        from backend import models
        pat = _create_patient(db, dentiste)
        dt = datetime.now() + timedelta(days=5)
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

        r = client.get(f"{BASE}/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        assert all(a["patient_id"] == pat.id for a in body)

    def test_list_empty_for_patient_with_no_appts(self, client, db, auth_headers, dentiste):
        pat = _create_patient(db, dentiste)
        r = client.get(f"{BASE}/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_ordered_desc(self, client, db, auth_headers, dentiste):
        from backend import models
        pat = _create_patient(db, dentiste)
        for offset in [5, 10, 15]:
            db.add(models.Appointment(
                patient_id=pat.id,
                patient_name="OrdTest",
                datetime_start=datetime.now() + timedelta(days=offset),
                duration_minutes=30,
                status=models.AppointmentStatus.PREVU,
                employer_id=dentiste.id,
            ))
        db.commit()

        r = client.get(f"{BASE}/patient/{pat.id}", headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert len(body) >= 3
        # Ordered descending: first item should be furthest in the future
        dts = [a["datetime_start"] for a in body]
        assert dts == sorted(dts, reverse=True)


class TestCheckConflictsEdgeCases:
    def test_invalid_datetime_format_returns_422(self, client, auth_headers):
        r = client.get(
            f"{BASE}/check-conflicts",
            params={"datetime_start": "not-a-date", "duration_minutes": 30},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_non_overlapping_adjacent_slots_no_conflict(self, client, auth_headers):
        """A slot that starts exactly when another ends should NOT conflict."""
        from backend import models
        from backend.tests.test_appointments_m5b import _create_appt
        dt_base = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=100)
        _create_appt(client, auth_headers, dt_base, duration=30)
        dt_next = dt_base + timedelta(minutes=30)
        r = client.get(
            f"{BASE}/check-conflicts",
            params={"datetime_start": dt_next.isoformat(), "duration_minutes": 30},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["has_conflict"] is False
