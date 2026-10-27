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
