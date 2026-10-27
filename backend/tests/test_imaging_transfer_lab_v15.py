"""LOT06-B transfer remains disabled outside isolated tests."""
import pytest
from backend.services.imaging_acquisition_transfer_lab_v15 import TransferLabRejected, guard


def test_transfer_is_disabled_in_production(db, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    with pytest.raises(TransferLabRejected, match="ISOLATED_TRANSFER_DISABLED"):
        guard(db)


def test_sql_lab_proposal_replay_conflict(db, dentiste, monkeypatch):
    import hashlib
    import uuid
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    device = "test-" + uuid.uuid4().hex
    capture = "capture-" + uuid.uuid4().hex
    token = lab.enroll_fixture(db, tenant=dentiste.id, device=device)
    digest = hashlib.sha256(b"fixture").hexdigest()
    args = dict(tenant=dentiste.id, device=device, capture=capture, digest=digest, size=7)
    result = lab.propose(db, token=token, **args)
    assert result["status"] == "AWAITING_STAFF"
    assert result["server_confirmed"] is False
    assert lab.propose(db, token=token, **args) == result
    with pytest.raises(lab.TransferLabRejected, match="CAPTURE_IDENTITY_CONFLICT"):
        lab.propose(db, token=token, **{**args, "digest": "0" * 64})
    with pytest.raises(lab.TransferLabRejected, match="DEVICE_AUTH_REQUIRED"):
        lab.propose(db, token="invalid", **args)


def test_real_encrypted_media_core_receipt_replay_lab(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path
):
    import hashlib
    import uuid
    from io import BytesIO
    from PIL import Image
    from sqlalchemy import select
    from backend.tests.test_imaging_acquisition_preflight_v15 import _lab, _patient
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab
    from backend.models_media_core import ClinicalAsset

    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, uuid.uuid4().hex[:8])
    device = "d-" + uuid.uuid4().hex
    capture = "c-" + uuid.uuid4().hex
    device_token = lab.enroll_fixture(db, tenant=dentiste.id, device=device)
    output = BytesIO()
    Image.new("RGB", (4, 4)).save(output, format="PNG")
    content = output.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    prefix = "/api/imaging-acquisitions/lab"
    device_headers = {"X-DC06B-Lab-Device-Token": device_token}
    proposal = dict(tenant=dentiste.id, device=device, capture=capture,
                    sha256=digest, byte_size=len(content))
    assert client.post(prefix + "/propose", json=proposal).status_code == 401
    proposed = client.post(prefix + "/propose", json=proposal, headers=device_headers)
    assert proposed.status_code == 200, proposed.text
    approval = dict(workstation_id=workstation, device=device, capture=capture,
                    patient_id=patient.id, explicit_staff_action=True)
    approved = client.post(prefix + "/approve", json=approval, headers=auth_headers)
    assert approved.status_code == 200, approved.text
    def send(payload=content):
        return client.post(
            prefix + "/transfer", headers=device_headers,
            data=dict(tenant=str(dentiste.id), device=device, capture=capture),
            files={"file": ("fixture.png", payload, "image/png")},
        )
    assert send(b"tampered").status_code == 409
    reply = send()
    assert reply.status_code == 200, reply.text
    original = reply.json()
    assert original["status"] == "LAB_SERVER_RECEIPT"
    assert original["server_confirmed"] is False
    assert send().json() == original
    receipt = client.get(prefix + "/receipt", headers=device_headers,
                         params=dict(tenant=dentiste.id, device=device, capture=capture))
    assert receipt.status_code == 200 and receipt.json() == original
    asset = db.query(ClinicalAsset).filter(ClinicalAsset.id == original["asset_id"]).one()
    assert asset.patient_id == patient.id
    assert asset.sha256 == digest
    assert asset.provenance_json["ingestion_channel"] == "LOT06B_LAB_ONLY"
    assert len(list(tmp_path.rglob("*.dcm"))) >= 1
    for table in (lab.receipts, lab.audit, lab.outbox):
        assert len(db.execute(select(table)).all()) >= 1
