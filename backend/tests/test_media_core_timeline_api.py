from datetime import datetime
from io import BytesIO

from PIL import Image

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash
from backend.services.clinical_asset_service import create_clinical_asset


def _png_bytes(color=(40, 90, 130)):
    image = Image.new("RGB", (800, 600), color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _patient(db, employer_id: int, suffix: str):
    patient = models.Patient(
        numero_dossier=f"C4-API-{suffix}",
        nom="Synthetic",
        prenom="Timeline",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _import_image(client, auth_headers, patient_id: int, content: bytes, timepoint: str = "T0"):
    response = client.post(
        f"/api/patients/{patient_id}/assets/import",
        headers=auth_headers,
        data={"asset_type": "PHOTO", "source_kind": "UPLOAD", "timepoint": timepoint},
        files={"file": (f"clinical-{timepoint}.png", content, "image/png")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_c4_read_routes_are_mounted_once_under_canonical_patients_prefix(client):
    from backend.main import app

    expected = {
        ("/api/patients/{patient_id}/assets", "GET"),
        ("/api/patients/{patient_id}/assets/{asset_id}/content", "GET"),
    }
    for path, method in expected:
        matches = [
            route
            for route in app.routes
            if getattr(route, "path", None) == path
            and method in (getattr(route, "methods", set()) or set())
        ]
        assert len(matches) == 1


def test_timeline_lists_primary_asset_only_and_keeps_storage_secrets_private(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c4-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "LIST")
    imported = _import_image(client, auth_headers, patient.id, _png_bytes(), "T0")

    response = client.get(f"/api/patients/{patient.id}/assets", headers=auth_headers)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["limit"] == 200
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["id"] == imported["id"]
    assert item["timepoint"] == "T0"
    assert item["source_kind"] == "UPLOAD"
    assert item["thumbnail_asset_id"] == imported["thumbnail_asset_id"]
    assert "storage_key" not in item
    assert "sha256" not in item

    derived = db.query(ClinicalAsset).filter(
        ClinicalAsset.patient_id == patient.id,
        ClinicalAsset.source_kind == "DERIVED",
    ).all()
    assert len(derived) == 1
    assert derived[0].id not in {entry["id"] for entry in payload["items"]}


def test_timeline_ignores_newer_metadata_only_thumbnail_candidate(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c4-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "THUMB-BIND")
    imported = _import_image(client, auth_headers, patient.id, _png_bytes(), "T0")

    metadata_only = create_clinical_asset(
        db,
        employer_id=dentiste.id,
        patient_id=patient.id,
        asset_type="PHOTO",
        source_kind="DERIVED",
        mime_type="image/jpeg",
        parent_asset_id=imported["id"],
        created_by=dentiste.id,
    )
    db.commit()
    assert metadata_only.id > imported["thumbnail_asset_id"]

    response = client.get(f"/api/patients/{patient.id}/assets", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.json()["items"][0]["thumbnail_asset_id"] == imported["thumbnail_asset_id"]


def test_timeline_hides_metadata_only_asset_without_verified_blob(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "META")
    metadata_only = create_clinical_asset(
        db,
        employer_id=dentiste.id,
        patient_id=patient.id,
        asset_type="PHOTO",
        source_kind="IMPORT",
        mime_type="image/png",
        timepoint="T0",
        created_by=dentiste.id,
    )
    db.commit()

    response = client.get(f"/api/patients/{patient.id}/assets", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.json()["items"] == []
    assert db.query(ClinicalAsset).filter(ClinicalAsset.id == metadata_only.id).one().storage_key is None


def test_authenticated_content_read_returns_verified_plaintext_with_no_store_headers(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c4-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "CONTENT")
    content = _png_bytes((10, 140, 60))
    imported = _import_image(client, auth_headers, patient.id, content)

    response = client.get(
        f"/api/patients/{patient.id}/assets/{imported['id']}/content",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.content == content
    assert response.headers["content-type"].startswith("image/png")
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-disposition"] == "inline"


def test_thumbnail_is_read_through_same_authenticated_patient_scope(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c4-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "THUMB")
    imported = _import_image(client, auth_headers, patient.id, _png_bytes())

    response = client.get(
        f"/api/patients/{patient.id}/assets/{imported['thumbnail_asset_id']}/content",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.content.startswith(b"\xff\xd8\xff")
    assert response.headers["content-type"].startswith("image/jpeg")


def test_asset_content_cannot_be_rebound_to_a_different_patient_path(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c4-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient_a = _patient(db, dentiste.id, "A")
    patient_b = _patient(db, dentiste.id, "B")
    imported = _import_image(client, auth_headers, patient_a.id, _png_bytes())

    response = client.get(
        f"/api/patients/{patient_b.id}/assets/{imported['id']}/content",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_timeline_rejects_another_tenants_patient(
    client, db, dentiste, auth_headers
):
    other = models.User(
        email="media-c4-other@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Other",
        is_active=True,
        is_licensed=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    patient = _patient(db, other.id, "OTHER")

    response = client.get(f"/api/patients/{patient.id}/assets", headers=auth_headers)

    assert response.status_code in {403, 404}
