from datetime import datetime
from io import BytesIO

from PIL import Image

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash
from backend.services.clinical_asset_service import list_clinical_assets_for_patient


def _png_bytes(color=(40, 90, 130)):
    image = Image.new("RGB", (640, 480), color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _patient(db, employer_id: int, suffix: str):
    patient = models.Patient(
        numero_dossier=f"V15-PHOTO-{suffix}",
        nom="PHOTO",
        prenom=suffix,
        date_naissance=datetime(2000, 1, 1),
        sexe="F",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _prepare_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "v15-photo-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)


def test_profile_photo_upload_sets_canonical_internal_url_and_serves_private_jpeg(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    _prepare_storage(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "UPLOAD")

    response = client.post(
        f"/api/patients/{patient.id}/photo",
        headers=auth_headers,
        files={"file": ("portrait.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["photo_url"] == f"/api/patients/{patient.id}/photo"
    assert isinstance(payload["asset_id"], int)

    db.refresh(patient)
    assert patient.photo_url == f"/api/patients/{patient.id}/photo"

    stored = (
        db.query(ClinicalAsset)
        .filter(
            ClinicalAsset.id == payload["asset_id"],
            ClinicalAsset.employer_id == dentiste.id,
            ClinicalAsset.patient_id == patient.id,
        )
        .one()
    )
    assert stored.asset_type == "PHOTO"
    assert stored.source_ref == "PATIENT_PROFILE_PHOTO"
    assert stored.mime_type == "image/jpeg"
    assert stored.storage_key
    assert stored.provenance_json["ingestion_channel"] == "PATIENT_PROFILE"

    delivered = client.get(f"/api/patients/{patient.id}/photo", headers=auth_headers)
    assert delivered.status_code == 200
    assert delivered.headers["content-type"].startswith("image/jpeg")
    assert delivered.headers["cache-control"] == "private, no-store"
    assert delivered.content.startswith(b"\xff\xd8\xff")


def test_profile_photo_replacement_keeps_stable_url_and_switches_latest_asset(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    _prepare_storage(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "REPLACE")

    first = client.post(
        f"/api/patients/{patient.id}/photo",
        headers=auth_headers,
        files={"file": ("first.png", _png_bytes((200, 20, 20)), "image/png")},
    )
    second = client.post(
        f"/api/patients/{patient.id}/photo",
        headers=auth_headers,
        files={"file": ("second.png", _png_bytes((20, 20, 200)), "image/png")},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["photo_url"] == second.json()["photo_url"]
    assert first.json()["asset_id"] != second.json()["asset_id"]

    profile_assets = (
        db.query(ClinicalAsset)
        .filter(
            ClinicalAsset.patient_id == patient.id,
            ClinicalAsset.source_ref == "PATIENT_PROFILE_PHOTO",
        )
        .order_by(ClinicalAsset.id.asc())
        .all()
    )
    assert len(profile_assets) == 2
    assert profile_assets[-1].id == second.json()["asset_id"]


def test_profile_photo_remove_clears_binding_and_get_falls_back_to_404(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    _prepare_storage(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "DELETE")

    uploaded = client.post(
        f"/api/patients/{patient.id}/photo",
        headers=auth_headers,
        files={"file": ("portrait.png", _png_bytes(), "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text

    removed = client.delete(f"/api/patients/{patient.id}/photo", headers=auth_headers)
    assert removed.status_code == 204

    db.refresh(patient)
    assert patient.photo_url is None
    assert client.get(f"/api/patients/{patient.id}/photo", headers=auth_headers).status_code == 404


def test_profile_photo_is_hidden_from_clinical_media_timeline(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    _prepare_storage(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "TIMELINE")

    uploaded = client.post(
        f"/api/patients/{patient.id}/photo",
        headers=auth_headers,
        files={"file": ("portrait.png", _png_bytes(), "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text

    timeline = list_clinical_assets_for_patient(
        db,
        employer_id=dentiste.id,
        patient_id=patient.id,
        include_derived=False,
    )
    assert all(asset.source_ref != "PATIENT_PROFILE_PHOTO" for asset in timeline)


def test_profile_photo_routes_are_tenant_scoped(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    _prepare_storage(monkeypatch, tmp_path)
    other = models.User(
        email="v15-photo-other@cabinet.ma",
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

    response = client.post(
        f"/api/patients/{patient.id}/photo",
        headers=auth_headers,
        files={"file": ("portrait.png", _png_bytes(), "image/png")},
    )

    assert response.status_code in {403, 404}
    assert (
        db.query(ClinicalAsset)
        .filter(
            ClinicalAsset.patient_id == patient.id,
            ClinicalAsset.source_ref == "PATIENT_PROFILE_PHOTO",
        )
        .count()
        == 0
    )


def test_profile_photo_rejects_invalid_file_and_direct_photo_url_mutation(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    _prepare_storage(monkeypatch, tmp_path)
    patient = _patient(db, dentiste.id, "GUARD")

    invalid = client.post(
        f"/api/patients/{patient.id}/photo",
        headers=auth_headers,
        files={"file": ("not-image.txt", b"not an image", "text/plain")},
    )
    assert invalid.status_code == 422

    direct = client.put(
        f"/api/patients/{patient.id}",
        headers=auth_headers,
        json={"photo_url": "https://tracker.invalid/patient.jpg"},
    )
    assert direct.status_code == 422
    db.refresh(patient)
    assert patient.photo_url is None


def test_patient_contract_suppresses_legacy_external_photo_url(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id, "LEGACYURL")
    patient.photo_url = "https://tracker.invalid/patient.jpg"
    db.commit()

    response = client.get(f"/api/patients/{patient.id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["photo_url"] is None
