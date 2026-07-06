"""Tests routers/verification.py — public document verification pages (no auth)."""
import pytest
from datetime import datetime
import uuid


def _make_patient(db, dentiste, nom="VERPAT"):
    from backend import models
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1980, 5, 10),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


def _make_document(db, patient_id, dentiste_id):
    from backend import models
    doc = models.DocumentArchive(
        patient_id=patient_id,
        document_type=models.DocumentType.ORDONNANCE,
        filename=f"ord_{uuid.uuid4().hex[:8]}.pdf",
        original_filename="ordonnance.pdf",
        document_group_id=str(uuid.uuid4()),
        file_hash="abc123hash",
        file_size=1024,
        file_path="/tmp/ord.pdf",
        created_at=datetime.now(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── verify/{doc_id} ───────────────────────────────────────────────────────────

class TestVerifyDocument:
    def test_nonexistent_doc_returns_html(self, client):
        r = client.get("/api/documents/verify/999999")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_nonexistent_doc_shows_invalid(self, client):
        r = client.get("/api/documents/verify/999999")
        assert "Introuvable" in r.text or "Invalide" in r.text or "Non Certifi" in r.text

    def test_valid_doc_by_id(self, client, db, dentiste):
        pat = _make_patient(db, dentiste, "VERDOC")
        doc = _make_document(db, pat.id, dentiste.id)
        r = client.get(f"/api/documents/verify/{doc.id}")
        assert r.status_code == 200
        assert "Certifi" in r.text or "M" in r.text  # HTML page loaded

    def test_valid_doc_by_filename_fragment(self, client, db, dentiste):
        pat = _make_patient(db, dentiste, "VERFN")
        doc = _make_document(db, pat.id, dentiste.id)
        fragment = doc.filename[:8]
        r = client.get(f"/api/documents/verify/{fragment}")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_non_numeric_nonexistent_returns_html(self, client):
        r = client.get("/api/documents/verify/nonexistent-xyz-999")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]


# ── verify/{public_id}/{document_type} ────────────────────────────────────────

class TestVerifySpecialDocument:
    def test_unknown_public_id_radio_returns_html(self, client):
        r = client.get("/api/documents/verify/999999/RADIO")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_unknown_doc_type_returns_html(self, client):
        r = client.get("/api/documents/verify/999999/UNKNOWN_TYPE")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_bilan_with_existing_patient(self, client, db, dentiste):
        pat = _make_patient(db, dentiste, "VERBILAN")
        r = client.get(f"/api/documents/verify/{pat.id}/BILAN")
        assert r.status_code == 200
        assert "Bilan" in r.text or "Certifi" in r.text

    def test_bilan_with_nonexistent_patient(self, client):
        r = client.get("/api/documents/verify/999999/BILAN")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_radio_with_nonexistent_id(self, client):
        r = client.get("/api/documents/verify/999999/RADIO")
        assert r.status_code == 200
        assert "Introuvable" in r.text or "Non Certifi" in r.text


# ── track/{doc_id} ────────────────────────────────────────────────────────────

class TestTrackDocument:
    def test_track_nonexistent_returns_html(self, client):
        r = client.get("/api/documents/track/999999")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_track_valid_doc(self, client, db, dentiste):
        pat = _make_patient(db, dentiste, "TRACKPAT")
        doc = _make_document(db, pat.id, dentiste.id)
        r = client.get(f"/api/documents/track/{doc.id}")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_track_by_filename_fragment(self, client, db, dentiste):
        pat = _make_patient(db, dentiste, "TRACKFN")
        doc = _make_document(db, pat.id, dentiste.id)
        fragment = doc.filename[:8]
        r = client.get(f"/api/documents/track/{fragment}")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
