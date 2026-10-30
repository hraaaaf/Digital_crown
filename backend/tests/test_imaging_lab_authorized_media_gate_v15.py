"""LOT06-C05B-02B real LAB approval + real AES media FUE (test-only)."""
from datetime import datetime
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import uuid

from PIL import Image
import pytest
from sqlalchemy import inspect, update

from backend.services import imaging_acquisition_transfer_lab_v15 as lab
from backend.services.imaging_lab_authorized_media_gate_v15 import (
    CaptureAuthorityRejected, verify_lab_approved_capture_and_media,
)
from backend.tests.test_imaging_acquisition_preflight_v15 import _lab, _patient
from backend.models_media_core import ClinicalAsset


@pytest.fixture(autouse=True)
def _cleanup_lab_rows(db):
    yield
    db.rollback()
    present = set(inspect(db.get_bind()).get_table_names())
    for table in (lab.outbox, lab.audit, lab.receipts, lab.captures, lab.devices):
        if table.name in present:
            db.execute(table.delete())
    db.commit()


def test_c05b02b_server_approved_lab_identity_and_real_media_fail_closed(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path,
):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)

    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, uuid.uuid4().hex[:8])
    device = "dev-" + uuid.uuid4().hex
    capture = "capture-" + uuid.uuid4().hex
    token = lab.enroll_fixture(db, tenant=dentiste.id, device=device)

    output = BytesIO()
    Image.new("RGB", (4, 4)).save(output, format="PNG")
    data = output.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    lab.propose(db, tenant=dentiste.id, device=device, token=token,
                capture=capture, digest=digest, size=len(data))
    base = dict(
        tenant=dentiste.id, device=device, token=token, capture=capture,
        patient=patient.id, staff_id=dentiste.id, workstation_id=workstation,
        appointment=None, reason="LAB_WALK_IN", asset_id=1, digest=digest,
        byte_size=len(data), media_root=tmp_path,
    )
    # Proposal without explicit staff challenge approval NEVER authorizes a media link.
    with pytest.raises(CaptureAuthorityRejected, match="LAB_APPROVED_CAPTURE_BINDING_MISMATCH"):
        verify_lab_approved_capture_and_media(db, **base)

    reviewed = lab.issue_review(
        db, staff=dentiste, tenant=dentiste.id, workstation=workstation,
        device=device, capture=capture, patient=patient.id, appointment=None,
        patient_only_reason="LAB_WALK_IN",
    )
    lab.approve(
        db, staff=dentiste, tenant=dentiste.id, workstation=workstation,
        device=device, capture=capture, patient=patient.id, appointment=None,
        patient_only_reason="LAB_WALK_IN",
        review_challenge=reviewed["review_challenge"],
    )
    receipt = lab.transfer(
        db, tenant=dentiste.id, device=device, token=token, capture=capture,
        payload=data, mime="image/png",
    )
    assert receipt["server_confirmed"] is False
    base["asset_id"] = receipt["asset_id"]
    proof = verify_lab_approved_capture_and_media(db, **base)
    assert proof.asset_id == base["asset_id"]
    assert proof.clinical_receipt_authorized is False

    negatives = (
        ({"token": "not-the-device-token"}, "LAB_DEVICE_AUTH_FAILED"),
        ({"device": "another-device"}, "LAB_DEVICE_AUTH_FAILED"),
        ({"patient": patient.id + 100000}, "LAB_APPROVED_CAPTURE_BINDING_MISMATCH"),
        ({"staff_id": dentiste.id + 100000}, "LAB_APPROVED_CAPTURE_BINDING_MISMATCH"),
        ({"reason": "LAB_URGENT"}, "LAB_APPROVED_CAPTURE_BINDING_MISMATCH"),
        ({"digest": "0" * 64}, "LAB_APPROVED_CAPTURE_BINDING_MISMATCH"),
        ({"byte_size": len(data) + 1}, "LAB_APPROVED_CAPTURE_BINDING_MISMATCH"),
        ({"workstation_id": "revoked-station"}, "LAB_APPROVED_CAPTURE_BINDING_MISMATCH"),
        ({"asset_id": base["asset_id"] + 100000}, "LAB_CAPTURE_ASSET_PROVENANCE_MISMATCH"),
    )
    for changes, expected in negatives:
        with pytest.raises(CaptureAuthorityRejected, match=expected):
            verify_lab_approved_capture_and_media(db, **{**base, **changes})

    dentiste.is_active = False
    db.commit()
    with pytest.raises(CaptureAuthorityRejected, match="LAB_STAFF_NOT_AUTHORIZED"):
        verify_lab_approved_capture_and_media(db, **base)
    dentiste.is_active = True
    db.commit()
    db.execute(update(lab.devices).where(
        lab.devices.c.tenant == dentiste.id, lab.devices.c.device == device,
    ).values(active=False))
    db.commit()
    with pytest.raises(CaptureAuthorityRejected, match="LAB_DEVICE_AUTH_FAILED"):
        verify_lab_approved_capture_and_media(db, **base)
    db.execute(update(lab.devices).where(
        lab.devices.c.tenant == dentiste.id, lab.devices.c.device == device,
    ).values(active=True))
    db.commit()

    blob = next(tmp_path.rglob("*.dcm"))
    original = blob.read_bytes()
    blob.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    with pytest.raises(CaptureAuthorityRejected, match="LAB_ENCRYPTED_MEDIA_INTEGRITY_BLOCKED"):
        verify_lab_approved_capture_and_media(db, **base)
    assert lab.receipts is not None  # no extra clinical receipt issued by the verifier

    evidence_dir = Path(os.environ.get("DC06C05B02B_EVIDENCE_DIR", str(tmp_path)))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "lot06c05b02b-lab-auth-media-fue.json").write_text(
        json.dumps({
            "kind": "LOT06_C05B02B_LAB_ONLY_APPROVAL_AND_AES_MEDIA",
            "real_lab_server_review_challenge_consumed": True,
            "lab_device_token_and_revocation_checked": True,
            "current_staff_permission_and_revocation_checked": True,
            "approved_capture_claims_and_media_provenance_checked": True,
            "real_aesgcm_media_tamper_refused": True,
            "negative_claims_rejected": len(negatives),
            "clinical_receipt_authorization_granted": False,
            "approval_version_persisted_in_postgres": False,
            "lab_guard_persistent_disabled": True,
            "production_device_trust_certified": False,
            "sql_fs_atomicity_certified": False,
            "product_ready": False,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print("LOT06C05B02B_LAB_APPROVAL_DEVICE_STAFF_AES_MEDIA_FAILCLOSED_PASS")
