from datetime import datetime
import hashlib

import pytest

from backend.models import Patient, User
from backend.security import get_password_hash
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import ClinicalAssetStorageError, store_clinical_asset_bytes


def _owner_and_patient(db, suffix: str):
    owner = User(
        email=f"media-c2-failclosed-{suffix}@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet=f"Dr C2 Failclosed {suffix}",
        is_active=True,
        is_licensed=True,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    patient = Patient(
        numero_dossier=f"C2-FC-{suffix}",
        nom="Synthetic",
        prenom="Failclosed",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return owner, patient


def test_c2_server_digest_overwrites_untrusted_c1_digest_metadata(db, tmp_path):
    owner, patient = _owner_and_patient(db, "digest")
    asset = create_clinical_asset(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_type="DOCUMENT",
        source_kind="IMPORT",
        sha256="f" * 64,
        byte_size=999,
    )
    db.commit()
    db.refresh(asset)

    content = b"server-authoritative-clinical-bytes"
    expected = hashlib.sha256(content).hexdigest()
    assert asset.sha256 != expected

    store_clinical_asset_bytes(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_id=asset.id,
        content=content,
        media_root=tmp_path,
    )
    db.commit()
    db.refresh(asset)

    assert asset.sha256 == expected
    assert asset.byte_size == len(content)
    assert expected not in asset.storage_key


def test_missing_encryption_key_refuses_storage_without_binding_or_blob(db, tmp_path, monkeypatch):
    owner, patient = _owner_and_patient(db, "missing-key")
    asset = create_clinical_asset(
        db,
        employer_id=owner.id,
        patient_id=patient.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
    )
    db.commit()
    db.refresh(asset)

    monkeypatch.delenv("CABINET_MASTER_KEY_HEX", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ClinicalAssetStorageError, match="encryption key is unavailable"):
        store_clinical_asset_bytes(
            db,
            employer_id=owner.id,
            patient_id=patient.id,
            asset_id=asset.id,
            content=b"must-not-be-written",
            media_root=tmp_path,
        )

    db.refresh(asset)
    assert asset.storage_key is None
    assert asset.storage_format is None
    assert asset.stored_at is None
    assert list(tmp_path.rglob("*.dcm")) == []
