from datetime import datetime
from io import BytesIO

from PIL import Image

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash


def _png_bytes():
    image = Image.new("RGB", (800, 600), (40, 90, 130))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _patient(db, employer_id: int, suffix: str):
    patient = models.Patient(
        numero_dossier=f"C3-API-{suffix}",
        nom="Synthetic",
        prenom="API",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_c3_import_route_is_mounted_once_under_canonical_patients_prefix(client):
    from backend.main import app

    matches = [
        route
        for route in app.routes
        if getattr(route, "path", None) == "/api/patients/{patient_id}/assets/import"
        and "POST" in (getattr(route, "methods", set()) or set())
    ]
    assert len(matches) == 1


def test_authenticated_image_import_persists_encrypted_asset_and_thumbnail(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c3-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "OK")
    content = _png_bytes()

    response = client.post(
        f"/api/patients/{patient.id}/assets/import",
        headers=auth_headers,
        data={"asset_type": "PHOTO", "source_kind": "UPLOAD", "timepoint": "T0"},
        files={"file": ("clinical.png", content, "image/png")},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["patient_id"] == patient.id
    assert payload["asset_type"] == "PHOTO"
    assert payload["mime_type"] == "image/png"
    assert payload["thumbnail_asset_id"] is not None
    assert "storage_key" not in payload
    assert "sha256" not in payload

    original = db.query(ClinicalAsset).filter(ClinicalAsset.id == payload["id"]).one()
    thumb = db.query(ClinicalAsset).filter(ClinicalAsset.id == payload["thumbnail_asset_id"]).one()
    assert original.employer_id == dentiste.id
    assert original.patient_id == patient.id
    assert original.source_kind == "UPLOAD"
    assert original.provenance_json["ingestion_channel"] == "WEB_API"
    assert original.storage_key
    assert thumb.parent_asset_id == original.id
    assert thumb.source_kind == "DERIVED"

    blobs = list(tmp_path.rglob("*.dcm"))
    assert len(blobs) == 2
    for blob in blobs:
        raw = blob.read_bytes()
        assert raw.startswith(b"DCM1")
        assert raw != content


def test_api_rejects_claimed_mime_mismatch_without_db_asset_or_blob(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c3-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "MIME")
    before = db.query(ClinicalAsset).count()

    response = client.post(
        f"/api/patients/{patient.id}/assets/import",
        headers=auth_headers,
        data={"asset_type": "PHOTO"},
        files={"file": ("clinical.png", _png_bytes(), "application/pdf")},
    )

    assert response.status_code == 422
    assert "claimed MIME" in response.json()["detail"]
    assert db.query(ClinicalAsset).count() == before
    assert list(tmp_path.rglob("*.dcm")) == []


def test_api_cannot_import_into_another_tenants_patient(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c3-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)

    other = models.User(
        email="media-c3-other@cabinet.ma",
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
    before = db.query(ClinicalAsset).count()

    response = client.post(
        f"/api/patients/{patient.id}/assets/import",
        headers=auth_headers,
        data={"asset_type": "PHOTO"},
        files={"file": ("clinical.png", _png_bytes(), "image/png")},
    )

    assert response.status_code in {403, 404}
    assert db.query(ClinicalAsset).count() == before
    assert list(tmp_path.rglob("*.dcm")) == []


def test_api_rejects_over_limit_payload_before_storage(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c3-api-test-secret-key-material")
    monkeypatch.setattr("backend.routers.media_core.MAX_IMPORT_BYTES", 8)
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "SIZE")
    before = db.query(ClinicalAsset).count()

    response = client.post(
        f"/api/patients/{patient.id}/assets/import",
        headers=auth_headers,
        data={"asset_type": "PHOTO"},
        files={"file": ("clinical.png", b"0123456789", "image/png")},
    )

    assert response.status_code == 413
    assert db.query(ClinicalAsset).count() == before
    assert list(tmp_path.rglob("*.dcm")) == []


def test_api_filesystem_failure_returns_503_and_rolls_back_asset(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "c3-api-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id, "FS")
    before = db.query(ClinicalAsset).count()

    def _fail_replace(_src, _dst):
        raise OSError("synthetic storage failure")

    monkeypatch.setattr("backend.services.clinical_asset_storage.os.replace", _fail_replace)

    response = client.post(
        f"/api/patients/{patient.id}/assets/import",
        headers=auth_headers,
        data={"asset_type": "PHOTO"},
        files={"file": ("clinical.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Clinical media storage unavailable"
    assert db.query(ClinicalAsset).count() == before
    assert list(tmp_path.rglob("*.dcm")) == []
    assert list(tmp_path.rglob(".tmp-*")) == []
