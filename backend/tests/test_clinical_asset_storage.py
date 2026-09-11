from datetime import datetime
import hashlib
from pathlib import PurePosixPath

import pytest

from backend.models import Patient, User
from backend.security import get_password_hash
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import (
    ClinicalAssetIntegrityError,
    ClinicalAssetStorageError,
    read_clinical_asset_bytes,
    store_clinical_asset_bytes,
    verify_clinical_asset_storage,
)


def _make_user(db, *, suffix: str):
    user = User(
        email=f"media-c2-{suffix}@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet=f"Dr C2 {suffix}",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_patient(db, employer_id: int, *, suffix: str):
    patient = Patient(
        numero_dossier=f"C2-{suffix}",
        nom=f"Synthetic{suffix}",
        prenom="Media",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _make_asset(db, *, employer_id: int, patient_id: int):
    asset = create_clinical_asset(
        db,
        employer_id=employer_id,
        patient_id=patient_id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
        original_filename="synthetic.png",
        mime_type="image/png",
    )
    db.commit()
    db.refresh(asset)
    return asset


def _stored_path(root, storage_key: str):
    return root.joinpath(*PurePosixPath(storage_key).parts)


def test_store_computes_digest_encrypts_and_roundtrips(db, tmp_path):
    owner = _make_user(db, suffix="roundtrip")
    patient = _make_patient(db, owner.id, suffix="001")
    asset = _make_asset(db, employer_id=owner.id, patient_id=patient.id)
    plaintext = b"synthetic-clinical-photo-bytes-c2"

    result = store_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_id=asset.id,
        content=plaintext,
        media_root=tmp_path,
    )
    db.commit()
    db.refresh(asset)

    expected_digest = hashlib.sha256(plaintext).hexdigest()
    assert result.deduplicated is False
    assert asset.sha256 == expected_digest
    assert asset.byte_size == len(plaintext)
    assert asset.storage_format == "AESGCM_V1"
    assert asset.storage_key.startswith("clinical-assets/t-")
    assert "tenant-" not in asset.storage_key
    assert expected_digest not in asset.storage_key
    assert "synthetic" not in asset.storage_key
    assert asset.original_filename not in asset.storage_key

    stored = _stored_path(tmp_path, asset.storage_key)
    payload = stored.read_bytes()
    assert payload.startswith(b"DCM1")
    assert payload != plaintext
    assert len(payload) > len(plaintext)

    assert read_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_id=asset.id,
        media_root=tmp_path,
    ) == plaintext
    assert verify_clinical_asset_storage(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_id=asset.id,
        media_root=tmp_path,
    ) is True


def test_identical_content_deduplicates_only_inside_same_tenant(db, tmp_path):
    owner = _make_user(db, suffix="dedupe")
    patient_a = _make_patient(db, owner.id, suffix="DA")
    patient_b = _make_patient(db, owner.id, suffix="DB")
    asset_a = _make_asset(db, employer_id=owner.id, patient_id=patient_a.id)
    asset_b = _make_asset(db, employer_id=owner.id, patient_id=patient_b.id)
    plaintext = b"same-clinical-content"

    first = store_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient_a.id,
        asset_id=asset_a.id,
        content=plaintext,
        media_root=tmp_path,
    )
    db.commit()
    second = store_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient_b.id,
        asset_id=asset_b.id,
        content=plaintext,
        media_root=tmp_path,
    )
    db.commit()

    assert first.deduplicated is False
    assert second.deduplicated is True
    assert asset_a.storage_key == asset_b.storage_key
    assert len(list(tmp_path.rglob("*.dcm"))) == 1


def test_same_content_isolated_between_tenants(db, tmp_path):
    owner_a = _make_user(db, suffix="tenant-a")
    owner_b = _make_user(db, suffix="tenant-b")
    patient_a = _make_patient(db, owner_a.id, suffix="TA")
    patient_b = _make_patient(db, owner_b.id, suffix="TB")
    asset_a = _make_asset(db, employer_id=owner_a.id, patient_id=patient_a.id)
    asset_b = _make_asset(db, employer_id=owner_b.id, patient_id=patient_b.id)
    plaintext = b"same-bytes-different-cabinets"

    result_a = store_clinical_asset_bytes(
        db,
        employer_id=owner_a.id,
        patient_id=patient_a.id,
        asset_id=asset_a.id,
        content=plaintext,
        media_root=tmp_path,
    )
    db.commit()
    result_b = store_clinical_asset_bytes(
        db,
        employer_id=owner_b.id,
        patient_id=patient_b.id,
        asset_id=asset_b.id,
        content=plaintext,
        media_root=tmp_path,
    )
    db.commit()

    assert result_a.deduplicated is False
    assert result_b.deduplicated is False
    assert asset_a.sha256 == asset_b.sha256
    assert asset_a.storage_key != asset_b.storage_key
    assert asset_a.sha256 not in asset_a.storage_key
    assert asset_b.sha256 not in asset_b.storage_key
    assert len(list(tmp_path.rglob("*.dcm"))) == 2

    with pytest.raises(ClinicalAssetStorageError, match="not found"):
        read_clinical_asset_bytes(
            db,
            employer_id=owner_a.id,
            patient_id=patient_b.id,
            asset_id=asset_b.id,
            media_root=tmp_path,
        )


def test_corruption_fails_closed_and_is_not_silently_overwritten(db, tmp_path):
    owner = _make_user(db, suffix="corrupt")
    patient = _make_patient(db, owner.id, suffix="COR")
    asset = _make_asset(db, employer_id=owner.id, patient_id=patient.id)
    plaintext = b"authenticated-clinical-media"

    store_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_id=asset.id,
        content=plaintext,
        media_root=tmp_path,
    )
    db.commit()
    stored = _stored_path(tmp_path, asset.storage_key)
    payload = bytearray(stored.read_bytes())
    payload[-1] ^= 0x01
    stored.write_bytes(bytes(payload))
    corrupted = stored.read_bytes()

    with pytest.raises(ClinicalAssetIntegrityError):
        read_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_id=asset.id,
            media_root=tmp_path,
        )

    with pytest.raises(ClinicalAssetIntegrityError):
        store_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_id=asset.id,
            content=plaintext,
            media_root=tmp_path,
        )

    assert stored.read_bytes() == corrupted


def test_storage_key_escape_is_rejected_before_filesystem_read(db, tmp_path):
    owner = _make_user(db, suffix="escape")
    patient = _make_patient(db, owner.id, suffix="ESC")
    asset = _make_asset(db, employer_id=owner.id, patient_id=patient.id)
    asset.sha256 = "a" * 64
    asset.byte_size = 10
    asset.storage_key = "../outside.dcm"
    asset.storage_format = "AESGCM_V1"
    asset.stored_at = datetime.utcnow()
    db.commit()

    with pytest.raises(ClinicalAssetStorageError, match="invalid clinical media storage key"):
        read_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_id=asset.id,
            media_root=tmp_path,
        )


def test_filesystem_failure_does_not_bind_unverified_storage_metadata(db, tmp_path, monkeypatch):
    owner = _make_user(db, suffix="write-fail")
    patient = _make_patient(db, owner.id, suffix="WF")
    asset = _make_asset(db, employer_id=owner.id, patient_id=patient.id)

    def _fail_replace(_src, _dst):
        raise OSError("synthetic replace failure")

    monkeypatch.setattr("backend.services.clinical_asset_storage.os.replace", _fail_replace)

    with pytest.raises(OSError, match="synthetic replace failure"):
        store_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_id=asset.id,
            content=b"will-not-bind",
            media_root=tmp_path,
        )

    db.refresh(asset)
    assert asset.storage_key is None
    assert asset.storage_format is None
    assert asset.stored_at is None
    assert list(tmp_path.rglob("*.dcm")) == []
    assert list(tmp_path.rglob(".tmp-*")) == []
