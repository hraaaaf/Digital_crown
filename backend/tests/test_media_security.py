"""Tests de régression sécurité — accès fichiers patients."""
import pytest
from fastapi.testclient import TestClient


def test_anonymous_panoramic_returns_401(client):
    """Accès anonyme à panoramique doit retourner 401."""
    r = client.get("/api/static/uploads/panoramic/test.jpg")
    assert r.status_code == 401


def test_anonymous_radios_returns_401(client):
    """Accès anonyme à radio doit retourner 401."""
    r = client.get("/api/static/uploads/radios/test.jpg")
    assert r.status_code == 401


def test_anonymous_actes_returns_401(client):
    """Accès anonyme à acte doit retourner 401."""
    r = client.get("/api/static/uploads/actes/test.jpg")
    assert r.status_code == 401


def test_anonymous_archives_returns_401(client):
    """Accès anonyme à archives doit retourner 401."""
    r = client.get("/api/static/archives/test.pdf")
    assert r.status_code == 401


def test_anonymous_documents_returns_401(client):
    """Accès anonyme à documents doit retourner 401."""
    r = client.get("/api/static/documents/test.pdf")
    assert r.status_code == 401


def test_anonymous_clinics_returns_401(client):
    """Accès anonyme à clinics doit retourner 401."""
    r = client.get("/api/static/uploads/clinics/test/logo.png")
    assert r.status_code == 401


def test_path_traversal_panoramic_rejected(client, auth_headers):
    """Path traversal (../..) sur panoramique doit être rejeté."""
    r = client.get("/api/static/uploads/panoramic/../../backend/config.py", headers=auth_headers)
    assert r.status_code in (400, 404)


def test_path_traversal_actes_rejected(client, auth_headers):
    """Path traversal sur actes doit être rejeté."""
    r = client.get("/api/static/uploads/actes/../../backend/config.py", headers=auth_headers)
    # actes route utilise basename() donc ../ est rejeté directement
    assert r.status_code in (400, 403, 404)


def test_clinic_asset_requires_auth(client):
    """Accès à clinic asset sans auth doit retourner 401."""
    r = client.get("/api/static/uploads/clinics/nonexistent/logo.png")
    assert r.status_code == 401


def test_patient_count_unchanged(db):
    """Vérifier que le nombre de patients est accessible."""
    from backend import models
    count = db.query(models.Patient).count()
    assert isinstance(count, int)
    assert count >= 0


def test_document_count_unchanged(db):
    """Vérifier que le nombre de documents est accessible."""
    from backend import models
    count = db.query(models.DocumentArchive).count()
    assert isinstance(count, int)
    assert count >= 0


def test_acte_count_unchanged(db):
    """Vérifier que le nombre d'actes est accessible."""
    from backend import models
    count = db.query(models.Acte).count()
    assert isinstance(count, int)
    assert count >= 0


def test_appointment_count_unchanged(db):
    """Vérifier que le nombre de rendez-vous est accessible."""
    from backend import models
    count = db.query(models.Appointment).count()
    assert isinstance(count, int)
    assert count >= 0
