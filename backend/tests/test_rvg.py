"""Tests RVG-SECURE-UPLOAD-1 — Upload et affichage sécurisé RVG.

Le endpoint /patients/{id}/rvg permet l'upload de radios intra-orales
via DocumentArchive (pas de nouvelle table).
"""
from io import BytesIO
from datetime import datetime
from fastapi.testclient import TestClient
from backend import models, schemas
from backend.tests.conftest import make_user


def _create_patient(db, dentiste, nom="RVGPAT"):
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=dentiste.get_employer_id(),
    )
    db.add(pat)
    db.commit()
    db.refresh(pat)
    return pat


class TestRVGUploadSecurity:
    """Tests sécurité upload RVG."""

    def test_upload_rvg_anonymous_401(self, client: TestClient):
        """Upload sans auth → 401."""
        file_content = BytesIO(b"fake image data")

        response = client.post(
            "/api/documents/patients/1/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
        )
        assert response.status_code == 401

    def test_upload_rvg_wrong_cabinet_403(self, client: TestClient, db, dentiste, auth_headers):
        """Upload pour patient d'un autre cabinet → 403/404."""
        other_user = make_user(db)
        other_patient = _create_patient(db, other_user, nom="OtherCabinet")

        file_content = BytesIO(b"fake image data")
        response = client.post(
            f"/api/documents/patients/{other_patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers=auth_headers,
        )
        assert response.status_code in (403, 404)

    def test_upload_rvg_mime_not_allowed_422(self, client: TestClient, db, dentiste, auth_headers):
        """MIME type non autorisé → 422."""
        patient = _create_patient(db, dentiste)
        file_content = BytesIO(b"fake executable data")
        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.exe", file_content, "application/octet-stream")},
            data={"radio_type": "rvg"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_upload_rvg_file_too_large_413(self, client: TestClient, db, dentiste, auth_headers):
        """Fichier > 10 MB → 413."""
        patient = _create_patient(db, dentiste)
        large_data = b"x" * (11 * 1024 * 1024)
        file_content = BytesIO(large_data)

        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers=auth_headers,
        )
        assert response.status_code == 413

    def test_upload_rvg_success_201(self, client: TestClient, db, dentiste, auth_headers):
        """Upload valide → 200/201, DocumentArchive créé."""
        patient = _create_patient(db, dentiste)
        file_content = BytesIO(b"fake jpeg image data")
        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={
                "radio_type": "periapical",
                "tooth_number": "16",
                "sector": "UR",
                "acquisition_date": "2025-01-01",
                "note": "Clear view",
            },
            headers=auth_headers,
        )
        assert response.status_code in (200, 201), response.text

        data = response.json()
        assert data["patient_id"] == patient.id
        assert "download_url" in data
        assert data["document_type"] == "RADIOGRAPHIE"
        assert data["clinical_data"]["radio_type"] == "periapical"
        assert data["clinical_data"]["tooth_number"] == "16"

        doc = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == data["id"]
        ).first()
        assert doc is not None
        assert doc.document_type == schemas.DocumentType.RADIOGRAPHIE
        assert doc.patient_id == patient.id
        assert "rvg" in (doc.tags or [])


class TestRVGListSecurity:
    """Tests sécurité listing RVG."""

    def test_list_rvg_anonymous_401(self, client: TestClient):
        """List sans auth → 401."""
        response = client.get("/api/documents/patients/1/rvg")
        assert response.status_code == 401

    def test_list_rvg_wrong_cabinet_403(self, client: TestClient, db, dentiste, auth_headers):
        """List pour patient d'un autre cabinet → 403/404."""
        other_user = make_user(db)
        other_patient = _create_patient(db, other_user, nom="OtherCabinet2")

        response = client.get(
            f"/api/documents/patients/{other_patient.id}/rvg",
            headers=auth_headers,
        )
        assert response.status_code in (403, 404)

    def test_list_rvg_empty(self, client: TestClient, db, dentiste, auth_headers):
        """List patient sans RVG → []."""
        patient = _create_patient(db, dentiste)
        response = client.get(f"/api/documents/patients/{patient.id}/rvg", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_rvg_includes_uploaded(self, client: TestClient, db, dentiste, auth_headers):
        """List affiche les RVG uploadés."""
        patient = _create_patient(db, dentiste)
        file_content = BytesIO(b"fake image")
        upload_resp = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers=auth_headers,
        )
        assert upload_resp.status_code in (200, 201)

        list_resp = client.get(f"/api/documents/patients/{patient.id}/rvg", headers=auth_headers)
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data) > 0
        assert data[0]["document_type"] == "RADIOGRAPHIE"
        assert "download_url" in data[0]


class TestRVGMetadata:
    """Tests métadonnées RVG."""

    def test_rvg_clinical_data_stored(self, client: TestClient, db, dentiste, auth_headers):
        """clinical_data RVG est stocké dans DocumentArchive."""
        patient = _create_patient(db, dentiste)
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={
                "radio_type": "bitewing",
                "tooth_number": "27",
                "sector": "LR",
                "acquisition_date": "2025-01-05",
                "note": "Interproximal caries suspected",
            },
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)

        data = response.json()
        clinical = data["clinical_data"]
        assert clinical["radio_type"] == "bitewing"
        assert clinical["tooth_number"] == "27"
        assert clinical["sector"] == "LR"
        assert clinical["note"] == "Interproximal caries suspected"

    def test_rvg_optional_fields(self, client: TestClient, db, dentiste, auth_headers):
        """Champs optionnels (tooth_number, sector, date, note) peuvent être None."""
        patient = _create_patient(db, dentiste)
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "other"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)

        data = response.json()
        clinical = data["clinical_data"]
        assert clinical["tooth_number"] is None
        assert clinical["sector"] is None
        assert clinical["note"] is None


class TestRVGDownloadUrl:
    """Tests que RVG est accessible via route protégée /documents/{id}/download."""

    def test_rvg_download_url_is_protected(self, client: TestClient, db, dentiste, auth_headers):
        """RVG download_url utilise /api/documents/{id}/download (route protégée)."""
        patient = _create_patient(db, dentiste)
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)

        data = response.json()
        download_url = data["download_url"]
        assert "/api/documents/" in download_url
        assert "/download" in download_url
        assert "/api/static/uploads" not in download_url

    def test_no_public_static_uploads_in_response(self, client: TestClient, db, dentiste, auth_headers):
        """Upload response n'expose jamais /api/static/uploads."""
        patient = _create_patient(db, dentiste)
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers=auth_headers,
        )

        import json
        response_text = json.dumps(response.json())
        assert "/api/static/uploads" not in response_text


class TestRVGRegressions:
    """Tests que les RVG ne cassent pas les documents existants."""

    def test_other_documents_not_affected(self, client: TestClient, db, dentiste, auth_headers):
        """Ajouter un RVG ne casse pas les autres DocumentArchive."""
        import uuid
        patient = _create_patient(db, dentiste)
        other_doc = models.DocumentArchive(
            patient_id=patient.id,
            document_type=schemas.DocumentType.ORDONNANCE,
            filename="prescription.pdf",
            original_filename="prescription.pdf",
            document_group_id=str(uuid.uuid4()),
            file_hash="dummy-hash",
            file_size=100,
            file_path="static/archives/1/ORDONNANCE/2025/1/test.pdf",
            status=schemas.DocumentStatus.ACTIF,
        )
        db.add(other_doc)
        db.commit()

        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/documents/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)

        other_still_exists = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == other_doc.id
        ).first()
        assert other_still_exists is not None
        assert other_still_exists.document_type == schemas.DocumentType.ORDONNANCE
