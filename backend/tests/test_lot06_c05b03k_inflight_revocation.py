"""LOT06 P0-04B: in-flight JWT/JWE command after access revocation COMMIT.

Pause at the exact boundary after FastAPI validated the JWT, loaded the
tenant-scoped active access and remote keyset, but before the real remote
worker runs. The second independent SQLAlchemy session commits revocation.
The command must fail closed without a signed positive ACK or durable write.
The pause is test-only; production handlers and crypto stay unchanged.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Event

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionMessage, PatientCompanionRemoteReceipt,
)
from backend.routers import patient_companion_messages as message_routes
from backend.tests.test_lot06_c05b03j_http_clinic import (
    _ack, _command, _fixture, _post,
)
from backend.tests.test_lot06_c05b03i_concurrent_services import synthetic_cabinet


def test_p0_04b_revoke_after_http_auth_before_remote_worker_does_not_accept(
    synthetic_cabinet, monkeypatch,
):
    app, engine, _employer, users, _patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    patient_a, patient_b = users
    key = __import__("uuid").uuid4()
    blob = _command(patient_a, "message.send", {
        "client_message_id": str(__import__("uuid").uuid4()),
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
                "client_message_id": str(__import__("uuid").uuid4()),
                "body": "Patient B is still active",
            })},
        )
    assert _ack(patient_b, response_b)["status"] == "ACCEPTED"
    print("LOT06_P0_04B_INFLIGHT_REVOKED_BEFORE_WORKER_DENIED_PASS",
          {"auth_entered": True, "revocation_committed_before_resume": True})
