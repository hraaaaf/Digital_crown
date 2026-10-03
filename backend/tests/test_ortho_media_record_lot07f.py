from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path

from PIL import Image

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash
from backend.services.ortho_media_record import ORTHO_MODEL_HOOKS, ORTHO_PHOTO_SLOTS


def _png_bytes():
    image = Image.new("RGB", (640, 480), (50, 100, 150))
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def _patient(db, employer_id: int):
    patient = models.Patient(
        numero_dossier="LOT07F-MEDIA",
        nom="Synthetic",
        prenom="Ortho",
        date_naissance=datetime(2000, 1, 1),
        sexe="F",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient



def test_lot07f_runtime_registry_matches_canonical_case_contract():
    root = Path(__file__).resolve().parents[2]
    contract = json.loads((root / "docs/audits/schemas/ortho_case_record_contract_v1.json").read_text(encoding="utf-8"))
    photos = contract["photo_protocol"]
    assert list(ORTHO_PHOTO_SLOTS) == photos["extraoral"] + photos["intraoral"]
    assert photos["source_ref_namespace"] == "ORTHO_PHOTO_V1:<SLOT_ID>"
    model = contract["model_protocol"]
    assert [hook["hook_id"] for hook in ORTHO_MODEL_HOOKS] == model["record_hooks"]
    assert all(hook["accepted_formats"] == model["accepted_formats"] for hook in ORTHO_MODEL_HOOKS)
    assert model["import_gate"] == "VALIDATOR_NOT_IMPLEMENTED_FAIL_CLOSED"
    assert model["measurement_authority_before_validation"] == "NONE"

def test_lot07f_routes_are_mounted_once(client):
    from backend.main import app

    paths = [(getattr(route, "path", None), getattr(route, "methods", set()) or set()) for route in app.routes]
    assert sum(path == "/api/patients/{patient_id}/ortho-media-record" and "GET" in methods for path, methods in paths) == 1
    assert sum(path == "/api/patients/{patient_id}/ortho-media-record/photos/{slot_id}" and "POST" in methods for path, methods in paths) == 1


def test_lot07f_empty_record_exposes_exact_photo_protocol_and_fail_closed_model_hooks(
    client, db, dentiste, auth_headers
):
    patient = _patient(db, dentiste.id)
    response = client.get(f"/api/patients/{patient.id}/ortho-media-record?timepoint=T0", headers=auth_headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["schema_version"] == "ORTHO_MEDIA_RECORD_V1"
    assert [item["slot_id"] for item in payload["photo_slots"]] == list(ORTHO_PHOTO_SLOTS)
    assert all(item["state"] == "EMPTY" and item["asset"] is None for item in payload["photo_slots"])
    assert payload["photo_complete"] is False
    assert {hook["hook_id"] for hook in payload["model_hooks"]} == {"MAXILLARY_ARCH", "MANDIBULAR_ARCH", "OCCLUSION_RELATION"}
    assert all(hook["accepted_formats"] == ["STL", "PLY", "OBJ"] for hook in payload["model_hooks"])
    assert all(hook["state"] == "VALIDATOR_NOT_IMPLEMENTED" and hook["measurement_authority"] == "NONE" for hook in payload["model_hooks"])


def test_lot07f_photo_upload_binds_slot_timepoint_and_server_operator_provenance(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "lot07f-media-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id)
    acquired = "2026-10-03T09:15:00+00:00"
    response = client.post(
        f"/api/patients/{patient.id}/ortho-media-record/photos/EXTRA_PROFILE",
        headers=auth_headers,
        data={"timepoint": "T0", "acquired_at": acquired},
        files={"file": ("profile.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 201, response.text
    asset_id = response.json()["asset"]["id"]
    asset = db.query(ClinicalAsset).filter(ClinicalAsset.id == asset_id).one()
    assert asset.source_ref == "ORTHO_PHOTO_V1:EXTRA_PROFILE"
    assert asset.timepoint == "T0"
    assert asset.captured_at is not None
    assert asset.provenance_json["schema_version"] == "ORTHO_MEDIA_RECORD_V1"
    assert asset.provenance_json["slot_id"] == "EXTRA_PROFILE"
    assert asset.provenance_json["operator_or_device"] == f"user:{dentiste.id}"
    assert asset.provenance_json["patient_record_id"] == str(patient.id)
    assert asset.provenance_json["timepoint_id"] == "T0"

    record = client.get(f"/api/patients/{patient.id}/ortho-media-record?timepoint=T0", headers=auth_headers).json()
    profile = next(item for item in record["photo_slots"] if item["slot_id"] == "EXTRA_PROFILE")
    assert profile["state"] == "FILLED"
    assert profile["asset"]["asset_id"] == asset_id
    assert profile["asset"]["mime_type"] == "image/png"



def test_lot07f_generic_media_import_cannot_spoof_reserved_ortho_namespace(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "lot07f-media-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id)
    before = db.query(ClinicalAsset).count()
    response = client.post(
        f"/api/patients/{patient.id}/assets/import",
        headers=auth_headers,
        data={
            "asset_type": "PHOTO",
            "source_kind": "UPLOAD",
            "source_ref": "ORTHO_PHOTO_V1:EXTRA_PROFILE",
            "timepoint": "T0",
        },
        files={"file": ("spoof.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Reserved orthodontic source_ref namespace"
    assert db.query(ClinicalAsset).count() == before


def test_lot07f_record_ignores_reserved_ref_without_canonical_provenance(db, dentiste):
    patient = _patient(db, dentiste.id)
    asset = ClinicalAsset(
        employer_id=dentiste.id,
        patient_id=patient.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
        source_ref="ORTHO_PHOTO_V1:EXTRA_PROFILE",
        mime_type="image/png",
        byte_size=10,
        sha256="0" * 64,
        storage_key="aa/bb/fake.dcm",
        storage_format="AESGCM_V1",
        stored_at=datetime.now(timezone.utc),
        timepoint="T0",
        captured_at=datetime.now(timezone.utc),
        provenance_json={"ingestion_channel": "WEB_API"},
    )
    db.add(asset)
    db.commit()
    from backend.services.ortho_media_record import build_ortho_media_record
    record = build_ortho_media_record(db, employer_id=dentiste.id, patient_id=patient.id, timepoint="T0")
    profile = next(item for item in record["photo_slots"] if item["slot_id"] == "EXTRA_PROFILE")
    assert profile == {"slot_id": "EXTRA_PROFILE", "state": "EMPTY", "asset": None}


def test_lot07f_new_routes_preserve_tenant_patient_isolation(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "lot07f-media-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    other = models.User(
        email="lot07f-other@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Other LOT07F",
        is_active=True,
        is_licensed=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    patient = _patient(db, other.id)
    before = db.query(ClinicalAsset).count()

    read = client.get(
        f"/api/patients/{patient.id}/ortho-media-record?timepoint=T0",
        headers=auth_headers,
    )
    assert read.status_code in {403, 404}

    write = client.post(
        f"/api/patients/{patient.id}/ortho-media-record/photos/EXTRA_PROFILE",
        headers=auth_headers,
        data={"timepoint": "T0", "acquired_at": "2026-10-03T09:15:00+00:00"},
        files={"file": ("profile.png", _png_bytes(), "image/png")},
    )
    assert write.status_code in {403, 404}
    assert db.query(ClinicalAsset).count() == before

def test_lot07f_invalid_slot_and_timepoint_fail_closed_without_asset(
    client, db, dentiste, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "lot07f-media-test-secret-key-material")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    patient = _patient(db, dentiste.id)
    before = db.query(ClinicalAsset).count()
    bad_slot = client.post(
        f"/api/patients/{patient.id}/ortho-media-record/photos/INTRA_UNKNOWN",
        headers=auth_headers,
        data={"timepoint": "T0", "acquired_at": "2026-10-03T09:15:00+00:00"},
        files={"file": ("bad.png", _png_bytes(), "image/png")},
    )
    assert bad_slot.status_code == 422
    bad_timepoint = client.get(f"/api/patients/{patient.id}/ortho-media-record?timepoint=T99", headers=auth_headers)
    assert bad_timepoint.status_code == 422
    assert db.query(ClinicalAsset).count() == before
