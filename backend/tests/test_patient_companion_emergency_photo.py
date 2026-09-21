from __future__ import annotations

import base64
import uuid
from datetime import datetime
from io import BytesIO

from PIL import Image

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.services.clinical_asset_storage import read_clinical_asset_bytes
from backend.services.patient_companion_emergency_photo import submit_emergency_photo


def _access(db, dentiste, suffix: str = "A"):
    patient = models.Patient(
        numero_dossier=f"PC07-{suffix}-{uuid.uuid4().hex[:6]}",
        nom=f"Emergency-{suffix}",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"pc07:{suffix}:{uuid.uuid4()}",
    )
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.flush()
    return patient, access


def _jpeg_bytes(*, with_metadata: bool = False) -> bytes:
    image = Image.new("RGB", (640, 480), (120, 70, 45))
    output = BytesIO()
    if with_metadata:
        exif = Image.Exif()
        exif[270] = "sensitive metadata"
        image.save(output, format="JPEG", quality=90, exif=exif)
    else:
        image.save(output, format="JPEG", quality=90)
    return output.getvalue()


def _payload(raw: bytes, **extra):
    return {
        "image_b64": base64.b64encode(raw).decode("ascii"),
        **extra,
    }


def test_pc07_emergency_photo_uses_exact_access_patient_and_strips_metadata(
    db, dentiste, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "pc07-media-storage-test-secret")
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root",
        lambda: tmp_path,
    )
    patient, access = _access(db, dentiste)

    result = submit_emergency_photo(
        db,
        access,
        _payload(_jpeg_bytes(with_metadata=True), captured_at="2026-09-21T08:00:00Z"),
    )

    assert result.status == "ACCEPTED"
    assert result.response["state"] == "received"
    asset = db.query(ClinicalAsset).filter(ClinicalAsset.id == result.response["asset_id"]).one()
    assert asset.employer_id == dentiste.id
    assert asset.patient_id == patient.id
    assert asset.asset_type == "PHOTO"
    assert asset.source_kind == "DEVICE_CAPTURE"
    assert asset.source_ref == "PATIENT_COMPANION_EMERGENCY_PHOTO"
    assert asset.created_by is None
    assert asset.provenance_json["ingestion_channel"] == "PATIENT_COMPANION"
    assert asset.provenance_json["capture_kind"] == "EMERGENCY_PHOTO"
    assert asset.provenance_json["access_public_id"] == access.public_id

    stored = read_clinical_asset_bytes(
        db,
        employer_id=dentiste.id,
        patient_id=patient.id,
        asset_id=asset.id,
    )
    with Image.open(BytesIO(stored)) as image:
        assert image.format == "JPEG"
        assert image.getexif().get(270) is None


def test_pc07_emergency_photo_rejects_payload_injection_without_mutation(db, dentiste):
    _patient, access = _access(db, dentiste)
    before = db.query(ClinicalAsset).count()

    result = submit_emergency_photo(
        db,
        access,
        {
            "image_b64": base64.b64encode(_jpeg_bytes()).decode("ascii"),
            "patient_id": 999999,
        },
    )

    assert result.status == "REJECTED"
    assert result.response == {"code": "INVALID_REQUEST"}
    assert db.query(ClinicalAsset).count() == before


def test_pc07_emergency_photo_rejects_invalid_base64_without_mutation(db, dentiste):
    _patient, access = _access(db, dentiste)
    before = db.query(ClinicalAsset).count()

    result = submit_emergency_photo(db, access, {"image_b64": "***not-base64***"})

    assert result.status == "REJECTED"
    assert result.response == {"code": "INVALID_IMAGE_ENCODING"}
    assert db.query(ClinicalAsset).count() == before


def test_pc07_emergency_photo_rejects_invalid_image_without_mutation(db, dentiste):
    _patient, access = _access(db, dentiste)
    before = db.query(ClinicalAsset).count()

    result = submit_emergency_photo(db, access, _payload(b"not-an-image"))

    assert result.status == "REJECTED"
    assert result.response == {"code": "INVALID_IMAGE"}
    assert db.query(ClinicalAsset).count() == before


def test_pc07_emergency_photo_rejects_invalid_capture_timestamp(db, dentiste):
    _patient, access = _access(db, dentiste)

    result = submit_emergency_photo(
        db,
        access,
        _payload(_jpeg_bytes(), captured_at="definitely-not-a-date"),
    )

    assert result.status == "REJECTED"
    assert result.response == {"code": "INVALID_CAPTURED_AT"}
