"""LOT06-B transfer remains disabled outside isolated tests."""
import pytest
from backend.services.imaging_acquisition_transfer_lab_v15 import TransferLabRejected, guard


@pytest.fixture(autouse=True)
def _cleanup_isolated_lab_tables(db):
    """These intentionally separate LAB tables are NOT part of Base.metadata.

    Remove test-only receipts before the shared test fixture clears ClinicalAsset,
    so re-used SQLite asset IDs cannot collide with an earlier test's receipts.
    """
    yield
    from sqlalchemy import inspect
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab

    db.rollback()
    existing = set(inspect(db.get_bind()).get_table_names())
    tables = (lab.outbox, lab.audit, lab.receipts, lab.captures, lab.devices)
    for table in tables:
        if table.name in existing:
            db.execute(table.delete())
    db.commit()


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
    wrong_patient = client.post(
        prefix + "/approve", headers=auth_headers,
        json={**approval, "patient_id": patient.id + 100000},
    )
    assert wrong_patient.status_code == 404, wrong_patient.text
    assert wrong_patient.json()["detail"] == "PATIENT_NOT_FOUND"
    denied = client.post(
        prefix + "/approve", headers=auth_headers,
        json={**approval, "explicit_staff_action": False},
    )
    assert denied.status_code == 403, denied.text
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
    # An immutable SQL receipt does not permit serving a damaged encrypted blob.
    blob = tmp_path.joinpath(*asset.storage_key.split("/"))
    assert blob.is_file()
    blob.write_bytes(b"synthetic-corrupted-ciphertext")
    with pytest.raises(lab.TransferLabRejected, match="RECEIPT_INTEGRITY_BLOCKED"):
        lab.lookup(db, tenant=dentiste.id, device=device,
                   token=device_token, capture=capture)
    assert len(db.execute(select(lab.receipts).where(
        lab.receipts.c.tenant == dentiste.id,
        lab.receipts.c.device == device,
        lab.receipts.c.capture == capture,
    )).all()) == 1


def test_lab_failure_injection_rolls_back_receipt_audit_and_outbox(
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

    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, uuid.uuid4().hex[:8])
    device = "fault-" + uuid.uuid4().hex
    capture = "fault-" + uuid.uuid4().hex
    token = lab.enroll_fixture(db, tenant=dentiste.id, device=device)
    out = BytesIO()
    Image.new("RGB", (4, 4)).save(out, format="PNG")
    content = out.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    lab.propose(db, tenant=dentiste.id, device=device, token=token,
                capture=capture, digest=digest, size=len(content))
    review = lab.issue_review(db, staff=dentiste, tenant=dentiste.id,
                              workstation=workstation, device=device, capture=capture,
                              patient=patient.id, appointment=None)
    lab.approve(db, staff=dentiste, tenant=dentiste.id,
                workstation=workstation, device=device, capture=capture,
                patient=patient.id, appointment=None,
                review_challenge=review["review_challenge"])
    args = dict(tenant=dentiste.id, device=device, token=token,
                capture=capture, payload=content, mime="image/png")
    base_assets = db.query(ClinicalAsset).count()
    baseline = [len(db.execute(select(t)).all()) for t in (lab.receipts, lab.audit, lab.outbox)]
    for boundary in ("after_ingest", "after_receipt", "after_audit", "after_outbox"):
        with pytest.raises(lab.TransferLabRejected, match="INJECTED_LAB_ROLLBACK"):
            lab.transfer(db, **args, fail_at=boundary)
        assert db.query(ClinicalAsset).count() == base_assets
        assert [len(db.execute(select(t)).all()) for t in (
            lab.receipts, lab.audit, lab.outbox
        )] == baseline
        assert lab.lookup(db, tenant=dentiste.id, device=device,
                          token=token, capture=capture)["status"] == "PENDING"
    # Orphan ciphertext remains intentionally non-authoritative pending reconciler review.
    assert list(tmp_path.rglob("*.dcm"))
    committed = lab.transfer(db, **args)
    assert committed["status"] == "LAB_SERVER_RECEIPT"
    assert committed["server_confirmed"] is False
    assert lab.transfer(db, **args) == committed
    assert [len(db.execute(select(t)).all()) for t in (
        lab.receipts, lab.audit, lab.outbox
    )] == [n + 1 for n in baseline]


def test_lab_device_and_staff_revocation_prevent_receipt_creation(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path
):
    import hashlib
    import uuid
    from io import BytesIO
    from PIL import Image
    from sqlalchemy import update, select
    from backend.tests.test_imaging_acquisition_preflight_v15 import _lab, _patient
    from backend.services import imaging_acquisition_transfer_lab_v15 as lab
    from backend.models_media_core import ClinicalAsset

    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    monkeypatch.setattr("backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path)
    station = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, uuid.uuid4().hex[:8])
    device, capture = "revoke-" + uuid.uuid4().hex, "revoke-" + uuid.uuid4().hex
    token = lab.enroll_fixture(db, tenant=dentiste.id, device=device)
    out = BytesIO()
    Image.new("RGB", (4, 4)).save(out, format="PNG")
    data = out.getvalue()
    lab.propose(db, tenant=dentiste.id, device=device, token=token,
                capture=capture, digest=hashlib.sha256(data).hexdigest(), size=len(data))
    review = lab.issue_review(db, staff=dentiste, tenant=dentiste.id,
                              workstation=station, device=device, capture=capture,
                              patient=patient.id, appointment=None)
    lab.approve(db, staff=dentiste, tenant=dentiste.id, workstation=station,
                device=device, capture=capture, patient=patient.id, appointment=None,
                review_challenge=review["review_challenge"])
    args = dict(tenant=dentiste.id, device=device, token=token,
                capture=capture, payload=data, mime="image/png")
    scope = (lab.devices.c.tenant == dentiste.id) & (lab.devices.c.device == device)
    db.execute(update(lab.devices).where(scope).values(active=False))
    db.commit()
    with pytest.raises(lab.TransferLabRejected, match="DEVICE_AUTH_REQUIRED"):
        lab.transfer(db, **args)
    db.execute(update(lab.devices).where(scope).values(active=True))
    dentiste.is_active = False
    db.commit()
    with pytest.raises(lab.TransferLabRejected, match="STAFF_REVOKED"):
        lab.transfer(db, **args)
    dentiste.is_active = True
    db.commit()
    assert lab.transfer(db, **args)["status"] == "LAB_SERVER_RECEIPT"
    assert len(db.execute(select(lab.receipts).where(
        lab.receipts.c.tenant == dentiste.id,
        lab.receipts.c.device == device,
        lab.receipts.c.capture == capture,
    )).all()) == 1
    assert db.query(ClinicalAsset).filter(ClinicalAsset.employer_id == dentiste.id,
                                          ClinicalAsset.patient_id == patient.id,
                                          ClinicalAsset.source_kind == "DEVICE_CAPTURE").count() == 1
