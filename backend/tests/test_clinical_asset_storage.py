from datetime import datetime
import hashlib
import json
import os
import stat
from pathlib import Path
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


@pytest.mark.skipif(os.name != "posix", reason="LOT06-C1 parent fsync proof is POSIX-only")
def test_durable_parent_barrier_sync_order(tmp_path, monkeypatch):
    """FUE-C03a: file fsync precedes atomic rename + directory fsync."""
    from backend.services import clinical_asset_storage as storage

    real_fsync = storage.os.fsync
    calls = []

    def _observed_fsync(fd):
        calls.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
        return real_fsync(fd)

    monkeypatch.setattr(storage.os, "fsync", _observed_fsync)
    target = tmp_path / "encrypted-synthetic.dcm"
    storage._atomic_write(target, b"DCM1-synthetic-payload")
    assert target.read_bytes() == b"DCM1-synthetic-payload"
    assert calls == ["file", "directory"]
    assert list(tmp_path.glob(".tmp-*")) == []
    print("LOT06C1_PARENT_DIRECTORY_SYNC_ORDER_PASS")


@pytest.mark.skipif(os.name != "posix", reason="LOT06-C1 parent fsync proof is POSIX-only")
def test_durable_parent_barrier_fails_closed_and_retries_orphan(db, tmp_path, monkeypatch):
    """FUE-C03b: parent fsync failure cannot authorize a SQL asset binding."""
    from backend.services import clinical_asset_storage as storage

    owner = _make_user(db, suffix="c1-dirsync")
    patient = _make_patient(db, owner.id, suffix="C1")
    asset = _make_asset(db, employer_id=owner.id, patient_id=patient.id)
    payload = b"synthetic-directory-durability-c1"
    real_fsync = storage.os.fsync
    failure_dirs = []

    def _reject_directory_fsync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            failure_dirs.append(True)
            raise OSError("synthetic directory sync failure")
        return real_fsync(fd)

    monkeypatch.setattr(storage.os, "fsync", _reject_directory_fsync)
    with pytest.raises(ClinicalAssetStorageError, match="directory durability barrier failed"):
        store_clinical_asset_bytes(
            db, employer_id=owner.id, patient_id=patient.id,
            asset_id=asset.id, content=payload, media_root=tmp_path,
        )

    db.refresh(asset)
    assert failure_dirs
    assert asset.storage_key is None and asset.stored_at is None
    assert asset.sha256 is None and asset.storage_format is None
    encrypted = list(tmp_path.rglob("*.dcm"))
    assert len(encrypted) == 1
    assert encrypted[0].read_bytes().startswith(b"DCM1")
    assert payload not in encrypted[0].read_bytes()
    assert list(tmp_path.rglob(".tmp-*")) == []

    successful_dirs = []

    def _accept_directory_fsync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            successful_dirs.append(True)
        return real_fsync(fd)

    monkeypatch.setattr(storage.os, "fsync", _accept_directory_fsync)
    result = store_clinical_asset_bytes(
        db, employer_id=owner.id, patient_id=patient.id,
        asset_id=asset.id, content=payload, media_root=tmp_path,
    )
    assert result.deduplicated is True
    assert successful_dirs, "REPLAY_DID_NOT_REESTABLISH_DIRECTORY_BARRIER"
    assert list(tmp_path.rglob("*.dcm")) == encrypted
    db.commit()
    db.refresh(asset)
    assert read_clinical_asset_bytes(
        db, employer_id=owner.id, patient_id=patient.id,
        asset_id=asset.id, media_root=tmp_path,
    ) == payload

    evidence_dir = Path(os.environ.get("DC06C1_EVIDENCE_DIR", str(tmp_path)))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "lot06c1-parent-fsync-fue.json").write_text(json.dumps({
        "kind": "LOT06C1_POSIX_PARENT_DIRECTORY_DURABILITY_REHEARSAL",
        "file_and_parent_fsync_tested": True,
        "failure_refuses_sql_asset_binding": True,
        "failed_sync_keeps_only_encrypted_orphan": True,
        "retry_resyncs_original_encrypted_blob_before_sql_binding": True,
        "actual_power_loss_tested": False,
        "ancestor_directory_creation_fsync_certified": False,
        "windows_durability_certified": False,
        "postgresql_transaction_certified": False,
        "product_ready": False,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("LOT06C1_DIRECTORY_SYNC_FAILURE_ORPHAN_RETRY_PASS")
