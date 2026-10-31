"""LOT06 P0-04B: in-flight JWT/JWE command after access revocation COMMIT.

Pause at the exact boundary after FastAPI validated the JWT, loaded the
tenant-scoped active access and remote keyset, but before the real remote
worker runs. The second independent SQLAlchemy session commits revocation.
The command must fail closed without a signed positive ACK or durable write.
The pause is test-only; production handlers and crypto stay unchanged.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import uuid

import pytest
from datetime import datetime
from threading import Event

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionIdentity, PatientCompanionMessage,
    PatientCompanionRemoteReceipt, PatientCompanionRemoteKeyset,
    PatientCompanionCabinetRemoteKey,
)
from backend.routers import patient_companion_messages as message_routes
from backend.services import patient_companion_remote_worker as remote_worker
from backend.tests.test_lot06_c05b03j_http_clinic import (
    _ack, _command, _fixture, _post,
)
from backend.tests.test_lot06_c05b03i_concurrent_services import synthetic_cabinet


def test_p0_04b_revoke_after_http_auth_before_remote_worker_does_not_accept(
    synthetic_cabinet, monkeypatch,
):
    app, engine, _employer, users, _patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    patient_a, patient_b = users
    key = uuid.uuid4()
    blob = _command(patient_a, "message.send", {
        "client_message_id": str(uuid.uuid4()),
        "body": "P0-04B must NOT persist after committed revocation",
    }, key=key)

    entered_worker = Event()
    allow_worker = Event()
    original = message_routes.process_remote_envelope

    def paused_worker(db, **kwargs):
        if kwargs["access"].public_id == patient_a["public_id"]:
            entered_worker.set()
            assert allow_worker.wait(timeout=15), "test synchronization timed out"
        return original(db, **kwargs)

    monkeypatch.setattr(message_routes, "process_remote_envelope", paused_worker)

    def patient_command():
        with TestClient(app, raise_server_exceptions=False) as client:
            return client.post(
                "/contexts/" + patient_a["public_id"] + "/messages/remote-command",
                headers={"Authorization": patient_a["authorization"]},
                json={"blob": blob},
            )

    with ThreadPoolExecutor(max_workers=1) as pool:
        submitted = pool.submit(patient_command)
        try:
            assert entered_worker.wait(timeout=20), "command did not pass HTTP auth"
            with Session(engine) as db:
                access = db.get(PatientCompanionAccess, patient_a["access_id"])
                assert access.revoked_at is None
                access.revoked_at = datetime.utcnow()
                db.commit()  # Must be durable BEFORE releasing command.
            with Session(engine) as db:
                assert db.get(PatientCompanionAccess, patient_a["access_id"]).revoked_at is not None
        finally:
            allow_worker.set()
        response = submitted.result(timeout=30)

    # Even an old in-memory ORM access object must not overrule a committed
    # revocation. A 500 is not an acceptable fail-closed service response.
    assert response.status_code in {400, 401, 403, 404}, (
        response.status_code, response.text[:220],
    )
    assert "blob" not in response.text
    with Session(engine) as db:
        assert db.query(PatientCompanionMessage).filter(
            PatientCompanionMessage.access_id == patient_a["access_id"],
        ).count() == 0
        assert db.query(PatientCompanionRemoteReceipt).filter(
            PatientCompanionRemoteReceipt.access_id == patient_a["access_id"],
            PatientCompanionRemoteReceipt.idempotency_key == str(key),
        ).count() == 0

    # Revoke only A: B must be able to send and get a valid signed ACK.
    with TestClient(app) as client:
        response_b = client.post(
            "/contexts/" + patient_b["public_id"] + "/messages/remote-command",
            headers={"Authorization": patient_b["authorization"]},
            json={"blob": _command(patient_b, "message.send", {
                "client_message_id": str(uuid.uuid4()),
                "body": "Patient B is still active",
            })},
        )
    assert _ack(patient_b, response_b)["status"] == "ACCEPTED"
    print("LOT06_P0_04B_INFLIGHT_REVOKED_BEFORE_WORKER_DENIED_PASS",
          {"auth_entered": True, "revocation_committed_before_resume": True})



def test_p0_04c_command_with_sqlite_writer_lock_commits_before_revocation(
    synthetic_cabinet, monkeypatch,
):
    """If the command owns the writer lock first, revocation must wait.

    A successful ACK is legitimate ONLY when its COMMIT precedes revocation;
    after revocation COMMIT all subsequent patient commands must be denied.
    """
    app, engine, _employer, users, _patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    a = users[0]
    key = uuid.uuid4()
    blob = _command(a, "message.send", {
        "client_message_id": str(uuid.uuid4()),
        "body": "command serialized BEFORE revocation",
    }, key=key)

    claimed = Event()
    release_claim = Event()
    revocation_attempted = Event()
    revocation_committed = Event()
    original_claim = remote_worker.claim_remote_command

    def paused_claim(db, *, access, message, **kwargs):
        result = original_claim(db, access=access, message=message, **kwargs)
        if access.public_id == a["public_id"]:
            assert result.kind == "new"
            claimed.set()
            assert release_claim.wait(timeout=15), "claim hold timed out"
        return result

    monkeypatch.setattr(remote_worker, "claim_remote_command", paused_claim)

    def patient_command():
        return _post(app, a, "messages", blob)

    def revoke():
        with Session(engine) as db:
            access = db.get(PatientCompanionAccess, a["access_id"])
            access.revoked_at = datetime.utcnow()
            revocation_attempted.set()
            db.commit()  # Must wait until earlier remote command's COMMIT.
        revocation_committed.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        patient_future = pool.submit(patient_command)
        try:
            assert claimed.wait(timeout=20), "receipt not claimed before revocation"
            revocation_future = pool.submit(revoke)
            assert revocation_attempted.wait(timeout=10)
            assert not revocation_committed.wait(timeout=0.25), (
                "revocation overtook a command holding SQLite writer lock"
            )
        finally:
            release_claim.set()
        patient_response = patient_future.result(timeout=30)
        revocation_future.result(timeout=30)

    assert _ack(a, patient_response)["status"] == "ACCEPTED"
    assert revocation_committed.is_set()
    after = _post(app, a, "messages", _command(a, "message.sync", {}))
    assert after.status_code == 401
    with Session(engine) as db:
        assert db.query(PatientCompanionMessage).filter(
            PatientCompanionMessage.access_id == a["access_id"],
        ).count() == 1
        assert db.query(PatientCompanionRemoteReceipt).filter(
            PatientCompanionRemoteReceipt.access_id == a["access_id"],
            PatientCompanionRemoteReceipt.idempotency_key == str(key),
        ).count() == 1
        assert db.get(PatientCompanionAccess, a["access_id"]).revoked_at is not None
    print("LOT06_P0_04C_LOCK_FIRST_COMMAND_COMMIT_BEFORE_REVOCATION_PASS")



@pytest.mark.parametrize("revocation_kind", [
    "identity", "keyset", "cabinet_signing_key",
])
def test_p0_04d_identity_keyset_or_cabinet_key_revoked_after_auth_denies(
    synthetic_cabinet, monkeypatch, revocation_kind,
):
    """All three revocations COMMIT before the authenticated worker resumes."""
    app, engine, employer_id, users, _ = _fixture(synthetic_cabinet, monkeypatch)
    a, b = users
    intent = uuid.uuid4()
    blob = _command(a, "message.send", {
        "client_message_id": str(uuid.uuid4()),
        "body": "P0-04D pending command after " + revocation_kind,
    }, key=intent)

    arrived = Event()
    proceed = Event()
    original = message_routes.process_remote_envelope

    def pause_after_http_auth(db, **kwargs):
        if kwargs["access"].public_id == a["public_id"]:
            arrived.set()
            assert proceed.wait(timeout=15), "in-flight revocation timing"
        return original(db, **kwargs)

    monkeypatch.setattr(message_routes, "process_remote_envelope", pause_after_http_auth)

    def command():
        with TestClient(app, raise_server_exceptions=False) as client:
            return client.post(
                "/contexts/" + a["public_id"] + "/messages/remote-command",
                headers={"Authorization": a["authorization"]},
                json={"blob": blob},
            )

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(command)
        try:
            assert arrived.wait(timeout=20), "HTTP auth/keyset was not reached"
            with Session(engine) as db:
                access = db.get(PatientCompanionAccess, a["access_id"])
                if revocation_kind == "identity":
                    target = db.get(PatientCompanionIdentity, access.identity_id)
                else:
                    keyset = db.query(PatientCompanionRemoteKeyset).filter_by(
                        access_id=access.id, status="ACTIVE",
                    ).one()
                    if revocation_kind == "keyset":
                        target = keyset
                    else:
                        target = db.query(PatientCompanionCabinetRemoteKey).filter_by(
                            employer_id=employer_id,
                            kid=keyset.cabinet_signing_kid,
                            key_use="sig",
                        ).one()
                target_type, target_id = type(target), target.id
                target.revoked_at = datetime.utcnow()
                db.commit()
            with Session(engine) as db:
                assert db.get(target_type, target_id).revoked_at is not None
        finally:
            proceed.set()
        response = future.result(timeout=35)

    assert response.status_code in {400, 401, 403, 404, 409}, (
        revocation_kind, response.status_code, response.text[:240],
    )
    assert "blob" not in response.text, revocation_kind
    with Session(engine) as db:
        assert db.query(PatientCompanionMessage).filter_by(
            access_id=a["access_id"],
        ).count() == 0
        assert db.query(PatientCompanionRemoteReceipt).filter_by(
            access_id=a["access_id"], idempotency_key=str(intent),
        ).count() == 0
    # Other patient must remain authorized even when A's identity/keyset ends.
    # Cabinet signing keys are tenant-scoped and shared: their revocation
    # necessarily prevents signing ACKs for patient B as well until re-key.
    if revocation_kind != "cabinet_signing_key":
        other = _ack(b, _post(app, b, "messages", _command(b, "message.send", {
            "client_message_id": str(uuid.uuid4()),
            "body": "other patient continues despite A revocation",
        })))
        assert other["status"] == "ACCEPTED"
    print("LOT06_P0_04D_REVOKED_INFLIGHT_DENIED_PASS", revocation_kind)
