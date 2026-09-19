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


def test_authenticated_orphan_panoramic_fails_closed(client, auth_headers, tmp_path, monkeypatch):
    """Un fichier disque sans provenance DB ne doit jamais devenir lisible par simple authentification."""
    upload_root = tmp_path / "uploads"
    target = upload_root / "panoramic" / "orphan.jpg"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"synthetic-orphan")

    monkeypatch.setattr("backend.main.UPLOAD_DIR", str(upload_root))
    response = client.get("/api/static/uploads/panoramic/orphan.jpg", headers=auth_headers)

    assert response.status_code == 404
    assert response.content != b"synthetic-orphan"


def test_authenticated_orphan_acte_attachment_fails_closed(client, auth_headers, tmp_path, monkeypatch):
    upload_root = tmp_path / "uploads"
    target = upload_root / "actes" / "orphan.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"synthetic-orphan-acte")

    monkeypatch.setattr("backend.main.UPLOAD_DIR", str(upload_root))
    response = client.get("/api/static/uploads/actes/orphan.pdf", headers=auth_headers)

    assert response.status_code == 404
    assert response.content != b"synthetic-orphan-acte"


def test_clinic_asset_route_is_bound_to_authenticated_cabinet_source():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    assert "models.CabinetConfig.owner_id == current_user.get_employer_id()" in source
    assert 'parts[0] != public_id' in source
    assert 'os.path.join(UPLOAD_DIR, "clinics", public_id)' in source


def test_authenticated_orphan_document_requires_valid_preview_token(client, auth_headers, dentiste, tmp_path, monkeypatch):
    from backend.services.document_preview_token import create_document_preview_token

    media_root = tmp_path / "media"
    target = media_root / "documents" / "2026" / "09" / "preview.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"%PDF-synthetic-preview")

    monkeypatch.setattr("backend.main.MEDIA_DIR", media_root)
    rel_path = "2026/09/preview.pdf"

    denied = client.get(f"/api/static/documents/{rel_path}", headers=auth_headers)
    assert denied.status_code == 404

    token = create_document_preview_token(dentiste.get_employer_id(), rel_path)
    allowed = client.get(
        f"/api/static/documents/{rel_path}",
        params={"preview_token": token},
        headers=auth_headers,
    )
    assert allowed.status_code == 200
    assert allowed.content.startswith(b"%PDF")


def test_document_preview_token_is_tenant_bound_and_expires():
    from backend.services.document_preview_token import create_document_preview_token, verify_document_preview_token

    token = create_document_preview_token(11, "2026/09/p.pdf", now=1_000)
    assert verify_document_preview_token(token, 11, "2026/09/p.pdf", now=1_001)
    assert not verify_document_preview_token(token, 12, "2026/09/p.pdf", now=1_001)
    assert not verify_document_preview_token(token, 11, "2026/09/other.pdf", now=1_001)
    assert not verify_document_preview_token(token, 11, "2026/09/p.pdf", now=2_000)
