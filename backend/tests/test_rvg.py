"""Tests RVG-SECURE-UPLOAD-1 — Upload et affichage sécurisé RVG.

Le endpoint /patients/{id}/rvg permet l'upload de radios intra-orales
via DocumentArchive (pas de nouvelle table).
"""
import pytest
from io import BytesIO
from datetime import date
from fastapi.testclient import TestClient
from backend import models, schemas


class TestRVGUploadSecurity:
    """Tests sécurité upload RVG."""

    def test_upload_rvg_anonymous_401(self, client: TestClient):
        """Upload sans auth → 401."""
        file_content = BytesIO(b"fake image data")
        file_content.name = "test.jpg"

        response = client.post(
            "/api/patients/1/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
        )
        assert response.status_code == 401

    def test_upload_rvg_wrong_cabinet_403(
        self, client: TestClient, db_session, current_user, other_employer
    ):
        """Upload pour patient d'un autre cabinet → 403/404."""
        # Create patient in other employer
        other_patient = models.Patient(
            employer_id=other_employer.id,
            patient_id="P999",
            nom="Test",
            prenom="Other",
        )
        db_session.add(other_patient)
        db_session.commit()

        file_content = BytesIO(b"fake image data")
        response = client.post(
            f"/api/patients/{other_patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        # Should be 403 or 404 (cross-tenant protection)
        assert response.status_code in (403, 404)

    def test_upload_rvg_mime_not_allowed_422(
        self, client: TestClient, db_session, current_user, patient
    ):
        """MIME type non autorisé → 422."""
        file_content = BytesIO(b"fake executable data")
        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.exe", file_content, "application/octet-stream")},
            data={"radio_type": "rvg"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 422

    def test_upload_rvg_file_too_large_413(
        self, client: TestClient, current_user, patient
    ):
        """Fichier > 10 MB → 413."""
        # Create a 11 MB file in memory
        large_data = b"x" * (11 * 1024 * 1024)
        file_content = BytesIO(large_data)

        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 413

    def test_upload_rvg_success_201(
        self, client: TestClient, current_user, patient, db_session
    ):
        """Upload valide → 201, DocumentArchive créé."""
        file_content = BytesIO(b"fake jpeg image data")
        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={
                "radio_type": "periapical",
                "tooth_number": "16",
                "sector": "UR",
                "acquisition_date": "2025-01-01",
                "note": "Clear view",
            },
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code in (200, 201)

        # Verify response structure
        data = response.json()
        assert data["patient_id"] == patient.id
        assert "download_url" in data
        assert data["document_type"] == "RADIOGRAPHIE"
        assert data["clinical_data"]["radio_type"] == "periapical"
        assert data["clinical_data"]["tooth_number"] == "16"

        # Verify DocumentArchive was created
        doc = db_session.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == data["id"]
        ).first()
        assert doc is not None
        assert doc.document_type == schemas.DocumentType.RADIOGRAPHIE
        assert doc.patient_id == patient.id
        assert doc.employer_id == current_user.employer_id
        assert doc.uploaded_by_id == current_user.id
        assert "rvg" in (doc.tags or [])


class TestRVGListSecurity:
    """Tests sécurité listing RVG."""

    def test_list_rvg_anonymous_401(self, client: TestClient):
        """List sans auth → 401."""
        response = client.get("/api/patients/1/rvg")
        assert response.status_code == 401

    def test_list_rvg_wrong_cabinet_403(
        self, client: TestClient, db_session, current_user, other_employer
    ):
        """List pour patient d'un autre cabinet → 403."""
        other_patient = models.Patient(
            employer_id=other_employer.id,
            patient_id="P888",
            nom="Test",
            prenom="Other",
        )
        db_session.add(other_patient)
        db_session.commit()

        response = client.get(
            f"/api/patients/{other_patient.id}/rvg",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code in (403, 404)

    def test_list_rvg_empty(self, client: TestClient, current_user, patient):
        """List patient sans RVG → []."""
        response = client.get(
            f"/api/patients/{patient.id}/rvg",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_rvg_includes_uploaded(
        self, client: TestClient, current_user, patient, db_session
    ):
        """List affiche les RVG uploadés."""
        # Upload first
        file_content = BytesIO(b"fake image")
        upload_resp = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert upload_resp.status_code in (200, 201)

        # List
        list_resp = client.get(
            f"/api/patients/{patient.id}/rvg",
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data) > 0
        assert data[0]["document_type"] == "RADIOGRAPHIE"
        assert "download_url" in data[0]


class TestRVGMetadata:
    """Tests métadonnées RVG."""

    def test_rvg_clinical_data_stored(
        self, client: TestClient, current_user, patient, db_session
    ):
        """clinical_data RVG est stocké dans DocumentArchive."""
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={
                "radio_type": "bitewing",
                "tooth_number": "27",
                "sector": "LR",
                "acquisition_date": "2025-01-05",
                "note": "Interproximal caries suspected",
            },
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code in (200, 201)

        data = response.json()
        clinical = data["clinical_data"]
        assert clinical["radio_type"] == "bitewing"
        assert clinical["tooth_number"] == "27"
        assert clinical["sector"] == "LR"
        assert clinical["note"] == "Interproximal caries suspected"

    def test_rvg_optional_fields(self, client: TestClient, current_user, patient):
        """Champs optionnels (tooth_number, sector, date, note) peuvent être None."""
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "other"},  # Only required fields
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code in (200, 201)

        data = response.json()
        clinical = data["clinical_data"]
        assert clinical["tooth_number"] is None
        assert clinical["sector"] is None
        assert clinical["note"] is None


class TestRVGDownloadUrl:
    """Tests que RVG est accessible via route protégée /documents/{id}/download."""

    def test_rvg_download_url_is_protected(
        self, client: TestClient, current_user, patient, db_session
    ):
        """RVG download_url utilise /api/documents/{id}/download (route protégée)."""
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code in (200, 201)

        data = response.json()
        download_url = data["download_url"]
        # Verify it's a protected route, not /api/static/uploads
        assert "/api/documents/" in download_url
        assert "/download" in download_url
        assert "/api/static/uploads" not in download_url

    def test_no_public_static_uploads_in_response(
        self, client: TestClient, current_user, patient
    ):
        """Upload response n'expose jamais /api/static/uploads."""
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )

        import json
        response_text = json.dumps(response.json())
        assert "/api/static/uploads" not in response_text


class TestRVGRegressions:
    """Tests que les RVG ne cassent pas les documents existants."""

    def test_other_documents_not_affected(
        self, client: TestClient, current_user, patient, db_session
    ):
        """Ajouter un RVG ne casse pas les autres DocumentArchive."""
        # Create a non-RVG document (e.g., prescription)
        other_doc = models.DocumentArchive(
            patient_id=patient.id,
            employer_id=current_user.employer_id,
            document_type=schemas.DocumentType.ORDONNANCE,
            filename="prescription.pdf",
            original_filename="prescription.pdf",
            file_path="static/archives/1/ORDONNANCE/2025/1/test.pdf",
            status=schemas.DocumentStatus.ACTIF,
        )
        db_session.add(other_doc)
        db_session.commit()

        # Upload RVG
        file_content = BytesIO(b"fake image")
        response = client.post(
            f"/api/patients/{patient.id}/rvg",
            files={"file": ("test.jpg", file_content, "image/jpeg")},
            data={"radio_type": "rvg"},
            headers={"Authorization": f"Bearer {current_user.access_token}"},
        )
        assert response.status_code in (200, 201)

        # Verify other document still exists
        other_still_exists = db_session.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == other_doc.id
        ).first()
        assert other_still_exists is not None
        assert other_still_exists.document_type == schemas.DocumentType.ORDONNANCE
