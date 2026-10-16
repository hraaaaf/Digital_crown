"""CB-00 ID, dossier, and name searches; synthetic patients only."""
from datetime import datetime
from unittest.mock import patch
from backend import models
from backend.config import settings

URL = "/api/bot/workflows/preview"

def test_dossier_and_name(client, db, dentiste, auth_headers):
    p = models.Patient(nom="Benali", prenom="Amina", date_naissance=datetime(1990, 1, 1),
                       sexe="F", employer_id=dentiste.id, numero_dossier="BEN-0001")
    db.add(p)
    db.commit()
    db.refresh(p)
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        for selector in ("BEN-0001", "dossier:BEN-0001", "Amina Benali", "Mme Benali"):
            r = client.post(URL, headers=auth_headers,
                            json={"messages": ["/patient", selector]})
            assert r.status_code == 200, r.text
            assert r.json()["patient"]["id"] == p.id
            assert r.json()["patient"]["numero_dossier"] == "BEN-0001"
            assert r.json()["proposal"] is None


def test_homonymes_need_explicit_dossier(client, db, dentiste, auth_headers):
    people = []
    for name, dossier in (("Amina", "BN-101"), ("Salma", "BN-102")):
        row = models.Patient(nom="Benali", prenom=name,
                             numero_dossier=dossier,
                             date_naissance=datetime(1990, 1, 1),
                             sexe="F", employer_id=dentiste.id)
        db.add(row)
        people.append(row)
    db.commit()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        r = client.post(URL, headers=auth_headers,
                        json={"messages": ["/patient", "Mme Benali"]})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "disambiguation"
        assert r.json()["proposal"] is None
        assert len(r.json()["candidates"]) == 2
        chosen = client.post(URL, headers=auth_headers,
                             json={"messages": ["/patient", "dossier:BN-102"]})
        assert chosen.status_code == 200
        assert chosen.json()["patient"]["id"] == people[1].id


def test_numeric_dossier_collision_not_auto_selected(client, db, dentiste, auth_headers):
    first = models.Patient(nom="First", prenom="Patient",
                           date_naissance=datetime(1990, 1, 1),
                           sexe="F", employer_id=dentiste.id)
    second = models.Patient(nom="Second", prenom="Patient",
                            date_naissance=datetime(1990, 1, 1),
                            sexe="F", employer_id=dentiste.id)
    db.add_all([first, second])
    db.commit()
    second.numero_dossier = str(first.id)
    db.commit()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        r = client.post(URL, headers=auth_headers,
                        json={"messages": ["/patient", str(first.id)]})
        assert r.status_code == 200
        assert r.json()["status"] == "disambiguation"
        assert {v["id"] for v in r.json()["candidates"]} == {first.id, second.id}
        for selector, expected in ((f"id:{first.id}", first.id),
                                   (f"dossier:{first.id}", second.id)):
            r = client.post(URL, headers=auth_headers,
                            json={"messages": ["/patient", selector]})
            assert r.status_code == 200
            assert r.json()["patient"]["id"] == expected


def test_foreign_name_and_dossier_look_like_unknown(client, db, auth_headers):
    from backend.tests.conftest import make_user
    other = make_user(db)
    foreign = models.Patient(nom="Externe", prenom="Fictif",
                             numero_dossier="F-2026-919",
                             date_naissance=datetime(1990, 1, 1),
                             sexe="F", employer_id=other.id)
    db.add(foreign)
    db.commit()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        responses = []
        for selector in ("F-2026-919", "dossier:F-2026-919",
                         "Fictif Externe", "DOSS-ABSENT-002"):
            result = client.post(URL, headers=auth_headers,
                                 json={"messages": ["/patient", selector]})
            assert result.status_code == 404
            responses.append(result.json())
        assert all(r == {"detail": "Patient introuvable."} for r in responses)


def test_soft_deleted_and_denied_search(client, db, dentiste, auth_headers):
    p = models.Patient(nom="Supprime", prenom="Fictif",
                       numero_dossier="SUP-2026-01",
                       date_naissance=datetime(1990, 1, 1),
                       sexe="F", employer_id=dentiste.id,
                       deleted_at=datetime.utcnow())
    db.add(p)
    db.commit()
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        for selector in ("SUP-2026-01", "Fictif Supprime"):
            result = client.post(URL, headers=auth_headers,
                                 json={"messages": ["/patient", selector]})
            assert result.status_code == 404
        with patch("backend.routers.bot_workflows.has_permission",
                   return_value=False):
            denied = client.post(URL, headers=auth_headers,
                                 json={"messages": ["/patient", "Benali"]})
            assert denied.status_code == 403
            assert "candidates" not in denied.text


def test_dossier_rdv_remains_unexecutable(client, db, dentiste, auth_headers):
    from datetime import date, timedelta
    p = models.Patient(nom="Rdv", prenom="Fictif", numero_dossier="RDV-008",
                       date_naissance=datetime(1990, 1, 1),
                       sexe="F", employer_id=dentiste.id)
    db.add(p)
    db.commit()
    baseline = (db.query(models.Appointment).count(),
                db.query(models.BotPendingAction).count())
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True):
        result = client.post(URL, headers=auth_headers, json={"messages": [
            "/rdv", "dossier:RDV-008",
            (date.today() + timedelta(days=1)).isoformat(),
            "10:00", "30", "consultation", "CONFIRMER"]})
    assert result.status_code == 200, result.text
    assert result.json()["proposal"]["params"]["patient_id"] == p.id
    assert result.json()["status"] == "proposal_only"
    assert "pending_action_id" not in result.text
    assert (db.query(models.Appointment).count(),
            db.query(models.BotPendingAction).count()) == baseline
