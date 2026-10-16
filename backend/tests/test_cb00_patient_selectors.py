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
