"""LOT06-C05B-02A Media Core prerequisite tests (synthetic patients only).

Uses real ClinicalAsset, SQLAlchemy tenant/patient scoping, and AES-GCM bytes.
Does not exercise staff/device authority or issue any PostgreSQL receipt.
"""
from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import store_clinical_asset_bytes
from backend.services.imaging_clinical_asset_verifier_v15 import (
    MediaBindingRejected, verify_device_capture_media_binding,
)
from backend.tests.test_clinical_asset_storage import _make_patient, _make_user


def _fixture(db, tmp_path):
    owner = _make_user(db, suffix="c05b02a")
    patient = _make_patient(db, owner.id, suffix="C05B02A")
    asset = create_clinical_asset(
        db, employer_id=owner.id, patient_id=patient.id,
        asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
        mime_type="image/png", created_by=owner.id,
        provenance_json={"ingestion_channel": "LOT06_C05B02A_TEST_ONLY"},
    )
    db.commit()
    data = b"synthetic-c05b02a-capture"
    store_clinical_asset_bytes(
        db, employer_id=owner.id, patient_id=patient.id,
        asset_id=asset.id, content=data, media_root=tmp_path,
    )
    db.commit()
    db.refresh(asset)
    return owner, patient, asset, data


def test_c05b02a_actual_encrypted_asset_binding_verifies(db, tmp_path):
    owner, patient, asset, data = _fixture(db, tmp_path)
    proof = verify_device_capture_media_binding(
        db, tenant=owner.id, patient=patient.id, asset_id=asset.id,
        staff_id=owner.id, digest=hashlib.sha256(data).hexdigest(),
        byte_size=len(data), media_root=tmp_path,
    )
    assert proof.asset_id == asset.id and proof.tenant == owner.id
    assert proof.patient == patient.id
    assert proof.clinical_receipt_authorized is False
    assert asset.source_kind == "DEVICE_CAPTURE"
    assert asset.storage_format == "AESGCM_V1"
    assert any(tmp_path.rglob("*.dcm"))
    assert data not in next(tmp_path.rglob("*.dcm")).read_bytes()
    print("LOT06C05B02A_ACTUAL_AESGCM_CLINICAL_ASSET_BINDING_PASS")


def test_c05b02a_cross_scope_wrong_claims_and_tamper_fail_closed(db, tmp_path):
    owner, patient, asset, data = _fixture(db, tmp_path)
    good = dict(
        tenant=owner.id, patient=patient.id, asset_id=asset.id,
        staff_id=owner.id, digest=hashlib.sha256(data).hexdigest(),
        byte_size=len(data), media_root=tmp_path,
    )
    for changes in (
        {"tenant": owner.id + 100000},
        {"patient": patient.id + 100000},
        {"asset_id": asset.id + 100000},
        {"staff_id": owner.id + 100000},
        {"digest": "0" * 64},
        {"byte_size": len(data) + 1},
        {"digest": "not-sha256"},
        {"byte_size": 0},
    ):
        with pytest.raises(MediaBindingRejected):
            verify_device_capture_media_binding(db, **{**good, **changes})

    # Missing ciphertext and damaged AES-GCM envelope never become a receipt.
    blob = next(tmp_path.rglob("*.dcm"))
    raw = blob.read_bytes()
    blob.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    with pytest.raises(MediaBindingRejected, match="MEDIA_INTEGRITY_BLOCKED"):
        verify_device_capture_media_binding(db, **good)
    blob.unlink()
    with pytest.raises(MediaBindingRejected, match="MEDIA_INTEGRITY_BLOCKED"):
        verify_device_capture_media_binding(db, **good)

    assert db.query(ClinicalAsset).filter(ClinicalAsset.id == asset.id).count() == 1
    assert asset.storage_key is not None  # metadata persists, no false receipt created
    print("LOT06C05B02A_MEDIA_WRONG_SCOPE_TAMPER_MISSING_FAIL_CLOSED_PASS")


def test_c05b02a_upload_provenance_not_mistaken_for_device_capture(db, tmp_path):
    from backend.tests.test_clinical_asset_storage import _make_asset
    owner = _make_user(db, suffix="c05b02a-upload")
    patient = _make_patient(db, owner.id, suffix="C05B02U")
    asset = _make_asset(db, employer_id=owner.id, patient_id=patient.id)
    data = b"synthetic-upload-not-device"
    store_clinical_asset_bytes(
        db, employer_id=owner.id, patient_id=patient.id,
        asset_id=asset.id, content=data, media_root=tmp_path,
    )
    db.commit()
    with pytest.raises(MediaBindingRejected, match="MEDIA_BINDING_CONFLICT"):
        verify_device_capture_media_binding(
            db, tenant=owner.id, patient=patient.id, asset_id=asset.id,
            staff_id=owner.id, digest=hashlib.sha256(data).hexdigest(),
            byte_size=len(data), media_root=tmp_path,
        )
    print("LOT06C05B02A_NON_DEVICE_CAPTURE_REJECTED_PASS")
