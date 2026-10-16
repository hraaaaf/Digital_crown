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
