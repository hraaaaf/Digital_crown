from __future__ import annotations

import base64
import hashlib
import uuid
from datetime import datetime, timedelta, timezone, timedelta, timezone
from io import BytesIO

from PIL import Image

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionEmergencyPhotoChunk,
    PatientCompanionEmergencyPhotoUpload,
    PatientCompanionIdentity,
)
from backend.services.clinical_asset_storage import read_clinical_asset_bytes
from backend.services.patient_companion_remote_crypto import generate_p256_keypair, sign_and_encrypt
from relay.contract import RELAY_MAX_BLOB_BYTES

from backend.services.patient_companion_remote_crypto import generate_p256_keypair, sign_and_encrypt
from backend.services.patient_companion_emergency_photo import (
    PC07_CHUNK_BYTES,
    begin_emergency_photo,
    finalize_emergency_photo,
    submit_emergency_photo_chunk,
)


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


def _jpeg_bytes(*, with_metadata: bool = False, size=(1280, 960)) -> bytes:
    image = (
        Image.effect_noise(size, 100).convert("RGB")
        if max(size) >= 1500
        else Image.new("RGB", size, (120, 70, 45))
    )
    output = BytesIO()
    if with_metadata:
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "sensitive metadata"
        image.save(output, format="JPEG", quality=95, exif=exif)
    else:
        image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def _begin_payload(raw: bytes, upload_id: str | None = None, *, sha: str | None = None):
    upload_id = upload_id or str(uuid.uuid4())
    return {
        "upload_id": upload_id,
        "object_sha256": sha or hashlib.sha256(raw).hexdigest(),
        "byte_size": len(raw),
        "chunk_count": (len(raw) + PC07_CHUNK_BYTES - 1) // PC07_CHUNK_BYTES,
        "captured_at": "2026-09-21T08:00:00Z",
    }


def _chunks(raw: bytes, upload_id: str):
    result = []
    for index in range(0, len(raw), PC07_CHUNK_BYTES):
        part = raw[index:index + PC07_CHUNK_BYTES]
        result.append({
            "upload_id": upload_id,
            "chunk_index": index // PC07_CHUNK_BYTES,
            "chunk_sha256": hashlib.sha256(part).hexdigest(),
            "chunk_b64": base64.b64encode(part).decode("ascii"),
        })
    return result


def _send_all(db, access, raw: bytes, *, reverse: bool = False):
    begin_payload = _begin_payload(raw)
    begin = begin_emergency_photo(db, access, begin_payload)
    assert begin.status == "ACCEPTED"
    chunks = _chunks(raw, begin_payload["upload_id"])
    if reverse:
        chunks = list(reversed(chunks))
    for payload in chunks:
        result = submit_emergency_photo_chunk(db, access, payload)
        assert result.status == "ACCEPTED"
    return begin_payload["upload_id"]


def test_pc07_chunked_photo_exact_patient_strips_metadata_and_accepts_out_of_order(
    db, dentiste, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "pc07-media-storage-test-secret")
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root",
        lambda: tmp_path,
    )
    patient, access = _access(db, dentiste)
    raw = _jpeg_bytes(with_metadata=True, size=(2200, 1600))
    upload_id = _send_all(db, access, raw, reverse=True)

    result = finalize_emergency_photo(db, access, {"upload_id": upload_id})

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
    assert asset.provenance_json["upload_id"] == upload_id

    stored = read_clinical_asset_bytes(
        db,
        employer_id=dentiste.id,
        patient_id=patient.id,
        asset_id=asset.id,
    )
    with Image.open(BytesIO(stored)) as image:
        assert image.format == "JPEG"
        assert image.getexif().get(274) is None
        assert image.getexif().get(270) is None

    upload = db.query(PatientCompanionEmergencyPhotoUpload).filter(
        PatientCompanionEmergencyPhotoUpload.public_id == upload_id
    ).one()
    assert upload.status == "RECEIVED"
    assert upload.asset_id == asset.id
    assert db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id == upload.id
    ).count() == 0


def test_pc07_duplicate_chunk_is_idempotent_and_conflict_fails(db, dentiste):
    _patient, access = _access(db, dentiste)
    raw = _jpeg_bytes(size=(1800, 1200))
    payload = _begin_payload(raw)
    assert begin_emergency_photo(db, access, payload).status == "ACCEPTED"
    first = _chunks(raw, payload["upload_id"])[0]

    assert submit_emergency_photo_chunk(db, access, first).status == "ACCEPTED"
    assert submit_emergency_photo_chunk(db, access, first).status == "ACCEPTED"

    upload = db.query(PatientCompanionEmergencyPhotoUpload).filter(
        PatientCompanionEmergencyPhotoUpload.public_id == payload["upload_id"]
    ).one()
    stored_chunk = db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id == upload.id
    ).one()
    assert bytes(stored_chunk.content) != base64.b64decode(first["chunk_b64"])
    assert not bytes(stored_chunk.content).startswith(base64.b64decode(first["chunk_b64"])[:16])
    assert db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id == upload.id
    ).count() == 1

    conflict = dict(first)
    different = b"x" * len(base64.b64decode(first["chunk_b64"]))
    conflict["chunk_b64"] = base64.b64encode(different).decode("ascii")
    conflict["chunk_sha256"] = hashlib.sha256(different).hexdigest()
    rejected = submit_emergency_photo_chunk(db, access, conflict)
    assert rejected.status == "REJECTED"
    assert rejected.response == {"code": "CHUNK_CONFLICT"}


def test_pc07_finalize_rejects_missing_chunk_without_asset(db, dentiste):
    _patient, access = _access(db, dentiste)
    raw = b"x" * (PC07_CHUNK_BYTES + 17)
    payload = _begin_payload(raw)
    assert payload["chunk_count"] == 2
    assert begin_emergency_photo(db, access, payload).status == "ACCEPTED"
    assert submit_emergency_photo_chunk(
        db, access, _chunks(raw, payload["upload_id"])[0]
    ).status == "ACCEPTED"

    before = db.query(ClinicalAsset).count()
    result = finalize_emergency_photo(db, access, {"upload_id": payload["upload_id"]})
    assert result.status == "REJECTED"
    assert result.response == {"code": "UPLOAD_INCOMPLETE"}
    assert db.query(ClinicalAsset).count() == before


def test_pc07_finalize_rejects_object_digest_mismatch_without_asset(db, dentiste):
    _patient, access = _access(db, dentiste)
    raw = _jpeg_bytes()
    payload = _begin_payload(raw, sha="0" * 64)
    assert begin_emergency_photo(db, access, payload).status == "ACCEPTED"
    for chunk in _chunks(raw, payload["upload_id"]):
        assert submit_emergency_photo_chunk(db, access, chunk).status == "ACCEPTED"

    before = db.query(ClinicalAsset).count()
    result = finalize_emergency_photo(db, access, {"upload_id": payload["upload_id"]})
    assert result.status == "REJECTED"
    assert result.response == {"code": "OBJECT_DIGEST_MISMATCH"}
    assert db.query(ClinicalAsset).count() == before


def test_pc07_upload_is_scoped_to_exact_access(db, dentiste):
    _patient_a, access_a = _access(db, dentiste, "A")
    _patient_b, access_b = _access(db, dentiste, "B")
    raw = _jpeg_bytes()
    payload = _begin_payload(raw)
    assert begin_emergency_photo(db, access_a, payload).status == "ACCEPTED"

    chunk = _chunks(raw, payload["upload_id"])[0]
    cross = submit_emergency_photo_chunk(db, access_b, chunk)
    assert cross.status == "REJECTED"
    assert cross.response == {"code": "UPLOAD_NOT_FOUND"}


def test_pc07_finalize_is_domain_idempotent_even_with_new_command_key(
    db, dentiste, tmp_path, monkeypatch
):
    monkeypatch.setenv("SECRET_KEY", "pc07-idempotency-test-secret")
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root",
        lambda: tmp_path,
    )
    _patient, access = _access(db, dentiste)
    raw = _jpeg_bytes()
    upload_id = _send_all(db, access, raw)

    first = finalize_emergency_photo(db, access, {"upload_id": upload_id})
    second = finalize_emergency_photo(db, access, {"upload_id": upload_id})

    assert first.status == "ACCEPTED"
    assert second.status == "ACCEPTED"
    assert first.response["asset_id"] == second.response["asset_id"]
    assert db.query(ClinicalAsset).filter(
        ClinicalAsset.id == first.response["asset_id"]
    ).count() == 1


def test_pc07_begin_rejects_injected_or_inconsistent_contract(db, dentiste):
    _patient, access = _access(db, dentiste)
    raw = _jpeg_bytes()
    payload = _begin_payload(raw)
    payload["patient_id"] = 999999
    injected = begin_emergency_photo(db, access, payload)
    assert injected.status == "REJECTED"
    assert injected.response == {"code": "INVALID_REQUEST"}

    inconsistent = _begin_payload(raw)
    inconsistent["chunk_count"] += 1
    result = begin_emergency_photo(db, access, inconsistent)
    assert result.status == "REJECTED"
    assert result.response == {"code": "INVALID_REQUEST"}


def test_pc07_96k_chunk_fits_real_compact_jose_relay_limit():
    signing_kid = str(uuid.uuid4())
    encryption_kid = str(uuid.uuid4())
    signing_private, _signing_public = generate_p256_keypair(kid=signing_kid, use="sig")
    _encryption_private, encryption_public = generate_p256_keypair(kid=encryption_kid, use="enc")

    raw = b"x" * PC07_CHUNK_BYTES
    now = datetime.now(timezone.utc)
    payload = {
        "protocol_version": "dc-pc-remote-v1",
        "message_id": str(uuid.uuid4()),
        "access_id": str(uuid.uuid4()),
        "sent_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "idempotency_key": str(uuid.uuid4()),
        "operation": "emergency_photo.chunk",
        "payload": {
            "upload_id": str(uuid.uuid4()),
            "chunk_index": 0,
            "chunk_sha256": hashlib.sha256(raw).hexdigest(),
            "chunk_b64": base64.b64encode(raw).decode("ascii"),
        },
    }

    blob = sign_and_encrypt(
        payload,
        sender_signing_private_jwk=signing_private,
        recipient_encryption_public_jwk=encryption_public,
        sender_signing_kid=signing_kid,
        recipient_encryption_kid=encryption_kid,
    )

    assert len(blob.encode("utf-8")) < RELAY_MAX_BLOB_BYTES


def test_pc07_begin_reports_only_contiguous_received_prefix(db, dentiste):
    _patient, access = _access(db, dentiste)
    raw = b"a" * (PC07_CHUNK_BYTES * 2)
    payload = _begin_payload(raw)
    assert begin_emergency_photo(db, access, payload).status == "ACCEPTED"
    chunks = _chunks(raw, payload["upload_id"])

    assert submit_emergency_photo_chunk(db, access, chunks[1]).status == "ACCEPTED"
    resumed = begin_emergency_photo(db, access, payload)
    assert resumed.status == "ACCEPTED"
    assert resumed.response["received_chunks"] == 0

    assert submit_emergency_photo_chunk(db, access, chunks[0]).status == "ACCEPTED"
    resumed = begin_emergency_photo(db, access, payload)
    assert resumed.response["received_chunks"] == 2


def test_pc07_96k_chunk_fits_real_jose_relay_limit():
    sender_kid = str(uuid.uuid4())
    recipient_kid = str(uuid.uuid4())
    sender_private, _sender_public = generate_p256_keypair(kid=sender_kid, use="sig")
    _recipient_private, recipient_public = generate_p256_keypair(kid=recipient_kid, use="enc")
    now = datetime.now(timezone.utc)
    raw = b"x" * PC07_CHUNK_BYTES
    payload = {
        "protocol_version": "dc-pc-remote-v1",
        "message_id": str(uuid.uuid4()),
        "access_id": str(uuid.uuid4()),
        "sent_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "idempotency_key": str(uuid.uuid4()),
        "operation": "emergency_photo.chunk",
        "payload": {
            "upload_id": str(uuid.uuid4()),
            "chunk_index": 0,
            "chunk_sha256": hashlib.sha256(raw).hexdigest(),
            "chunk_b64": base64.b64encode(raw).decode("ascii"),
        },
    }
    token = sign_and_encrypt(
        payload,
        sender_signing_private_jwk=sender_private,
        recipient_encryption_public_jwk=recipient_public,
        sender_signing_kid=sender_kid,
        recipient_encryption_kid=recipient_kid,
    )
    assert len(token.encode("utf-8")) < 256 * 1024
