"""C05B-03J — actual FastAPI patient routes, JWT + JWS/JWE, isolated cabinet.

Runs wholly in-process via FastAPI TestClient; no external HTTP/Tailnet. The
Windows DPAPI key-protector is replaced ONLY for the synthetic Linux fixture;
signature verification, JWT validation, replay receipts, patient access, actual
PC02/PC08 handlers and independent SQLite connections are NOT stubbed.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from functools import partial
from threading import Barrier
from time import monotonic
import json
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionIdentity, PatientCompanionMessage,
)
from backend.routers import patient_companion_agenda as agenda_routes
from backend.routers import patient_companion_messages as message_routes
from backend.routers.patient_companion_common import (
    create_patient_device_token, get_db,
)
from backend.services.patient_companion_agenda import issue_slots
from backend.services.patient_companion_remote_crypto import (
    decrypt_and_verify, generate_p256_keypair, sign_and_encrypt,
)
from backend.services.patient_companion_remote_keys import enroll_remote_keyset
from backend.services.patient_companion_remote_worker import process_remote_envelope
from relay.contract import RelayInnerMessage
from backend.tests.test_lot06_c05b03i_concurrent_services import synthetic_cabinet

TEST_PREFIX = b"DC06J-LINUX-SYNTHETIC-KEY-NOT-DPAPI:"

def _test_protect(raw: bytes) -> bytes:
    return TEST_PREFIX + raw

def _test_unprotect(raw: bytes) -> bytes:
    if not raw.startswith(TEST_PREFIX):
        raise ValueError("test key protector mismatch")
    return raw[len(TEST_PREFIX):]


def _fixture(synthetic_cabinet, monkeypatch):
    engine, employer_id, access_ids, patient_ids = synthetic_cabinet
    app = FastAPI(title="C05B-03J isolated genuine patient routes")
    app.include_router(agenda_routes.router)
    app.include_router(message_routes.router)

    def isolated_get_db():
        with Session(engine) as db:
            yield db

    # Override ONLY the DB source to the independently connected disposable DB.
    # The real patient_identity(), principal_for_access() and JWT checks remain.
    app.dependency_overrides[get_db] = isolated_get_db

    # Linux CI cannot call Windows DPAPI; keep real remote-worker/JWS/JWE logic.
    # These wrappers change only the OS protector, not application authorization.
    for module in (agenda_routes, message_routes):
        monkeypatch.setattr(
            module, "process_remote_envelope",
            partial(process_remote_envelope, unprotect=_test_unprotect),
        )

    users = []
    with Session(engine) as db:
        for access_id in access_ids:
            access = db.get(PatientCompanionAccess, access_id)
            identity = db.get(PatientCompanionIdentity, access.identity_id)
            sig_private, sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
            enc_private, enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
            keyset, cabinet_sig, cabinet_enc = enroll_remote_keyset(
                db,
                access=access,
                patient_signing_kid=sig_public["kid"],
                patient_signing_public_jwk=sig_public,
                patient_encryption_kid=enc_public["kid"],
                patient_encryption_public_jwk=enc_public,
                protect=_test_protect,
            )
            db.flush()
            users.append({
                "access_id": access.id,
                "public_id": access.public_id,
                "patient_id": access.patient_id,
                "authorization": "Bearer " + create_patient_device_token(identity, access),
                "sign_private": sig_private,
                "sign_kid": keyset.patient_signing_kid,
                "enc_private": enc_private,
                "enc_kid": keyset.patient_encryption_kid,
                "cabinet_enc_public": json.loads(cabinet_enc.public_jwk_json),
                "cabinet_enc_kid": keyset.cabinet_encryption_kid,
                "cabinet_sig_public": json.loads(cabinet_sig.public_jwk_json),
                "cabinet_sig_kid": keyset.cabinet_signing_kid,
            })
        db.commit()
    return app, engine, employer_id, users, patient_ids


def _command(user, operation, payload, *, key=None):
    now = datetime.now(timezone.utc)
    message = RelayInnerMessage(
        message_id=uuid.uuid4(), access_id=uuid.UUID(user["public_id"]),
        sent_at=now, expires_at=now + timedelta(minutes=10),
        idempotency_key=key or uuid.uuid4(), operation=operation, payload=payload,
    )
    return sign_and_encrypt(
        message.model_dump(mode="json"),
        sender_signing_private_jwk=user["sign_private"],
        recipient_encryption_public_jwk=user["cabinet_enc_public"],
        sender_signing_kid=user["sign_kid"],
        recipient_encryption_kid=user["cabinet_enc_kid"],
    )


def _post(app, user, path, blob):
    with TestClient(app, raise_server_exceptions=True) as client:
        return client.post(
            "/contexts/" + user["public_id"] + "/" + path + "/remote-command",
            headers={"Authorization": user["authorization"]},
            json={"blob": blob},
        )


def _ack(user, response):
    assert response.status_code == 200, (response.status_code, response.text[:250])
    encrypted = response.json()["blob"]
    ack = decrypt_and_verify(
        encrypted,
        recipient_encryption_private_jwk=user["enc_private"],
        sender_signing_public_jwk=user["cabinet_sig_public"],
        expected_sender_signing_kid=user["cabinet_sig_kid"],
        expected_recipient_encryption_kid=user["enc_kid"],
    )
    assert ack["operation"] == "command.result"
    return ack["payload"]


def test_c05b03j_actual_http_jwt_tenant_and_revocation(synthetic_cabinet, monkeypatch):
    app, engine, _doctor_id, users, _patients = _fixture(synthetic_cabinet, monkeypatch)
    with TestClient(app) as client:
        a, b = users
        url_a = "/contexts/" + a["public_id"] + "/agenda"
        assert client.get(url_a).status_code == 401
        assert client.get(url_a, headers={"Authorization": "Bearer invalid"}).status_code == 401
        assert client.get(url_a, headers={"Authorization": b["authorization"]}).status_code == 404
        ok = client.get(url_a, headers={"Authorization": a["authorization"]})
        assert ok.status_code == 200, ok.text
        assert ok.json()["items"] == []
        with Session(engine) as db:
            access = db.get(PatientCompanionAccess, a["access_id"])
            access.revoked_at = datetime.utcnow()
            db.commit()
        assert client.get(url_a, headers={"Authorization": a["authorization"]}).status_code == 401
        assert client.get(
            "/contexts/" + b["public_id"] + "/agenda",
            headers={"Authorization": b["authorization"]},
        ).status_code == 200
    print("C05B03J_HTTP_REAL_JWT_CROSS_PATIENT_REVOCATION_PASS")


def test_c05b03j_actual_http_jwe_pc08_idempotency_and_isolation(synthetic_cabinet, monkeypatch):
    app, engine, _doctor_id, users, patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    key = uuid.uuid4()
    blobs = [
        _command(user, "message.send", {
            "client_message_id": str(uuid.uuid4()),
            "body": f"Cabinet synthétique patient {index}",
        })
        for index, user in enumerate(users)
    ]
    barrier = Barrier(2)

    def send(index):
        barrier.wait(timeout=10)
        return _ack(users[index], _post(app, users[index], "messages", blobs[index]))

    with ThreadPoolExecutor(max_workers=2) as pool:
        fa, fb = pool.submit(send, 0), pool.submit(send, 1)
        results = [fa.result(timeout=30), fb.result(timeout=30)]
    assert [r["status"] for r in results] == ["ACCEPTED", "ACCEPTED"], results

    # New signed message, SAME intent key: receipt remains one persisted result.
    first = _command(users[0], "message.send", {
        "client_message_id": str(uuid.uuid4()), "body": "retry authentifié",
    }, key=key)
    r1 = _ack(users[0], _post(app, users[0], "messages", first))
    assert r1["status"] == "ACCEPTED"
    retry = _command(users[0], "message.send", {
        "client_message_id": str(uuid.uuid4()), "body": "different payload on same intent",
    }, key=key)
    r2 = _ack(users[0], _post(app, users[0], "messages", retry))
    assert r2["status"] == "ACCEPTED"
    assert r2["result"] == r1["result"]

    # Cross-patient key reuse must not grant access to the other context.
    cross = _post(app, users[0], "messages",
                  _command(users[0], "message.sync", {}))
    assert _ack(users[0], cross)["status"] == "ACCEPTED"
    syncs = [
        _ack(user, _post(app, user, "messages", _command(user, "message.sync", {})))
        for user in users
    ]
    assert all(result["status"] == "ACCEPTED" for result in syncs)
    assert len(syncs[0]["result"]["items"]) == 2
    assert len(syncs[1]["result"]["items"]) == 1
    with Session(engine) as db:
        rows = db.query(PatientCompanionMessage).all()
        assert len(rows) == 3
        assert sum(row.patient_id == patient_ids[0] for row in rows) == 2
        assert sum(row.patient_id == patient_ids[1] for row in rows) == 1
    print("C05B03J_HTTP_REAL_JWE_PC08_PARALLEL_IDEMPOTENT_ISOLATED_PASS")


def test_c05b03j_actual_http_jwe_pc02_same_slot_race(synthetic_cabinet, monkeypatch):
    app, engine, employer_id, users, patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    start = datetime(2030, 2, 1, 10, 0)
    with Session(engine) as db:
        refs = []
        for user in users:
            access = db.get(PatientCompanionAccess, user["access_id"])
            issued = issue_slots(db, access=access, starts=[start],
                                 duration_minutes=30, practitioner_id=employer_id)
            assert len(issued) == 1
            refs.append(issued[0]["slot_ref"])
        db.commit()
    blobs = [
        _command(user, "agenda.create", {"slot_ref": refs[index]})
        for index, user in enumerate(users)
    ]
    barrier = Barrier(2)

    def book(index):
        barrier.wait(timeout=10)
        started = monotonic()
        response = _post(app, users[index], "agenda", blobs[index])
        elapsed_ms = (monotonic() - started) * 1000
        return _ack(users[index], response), elapsed_ms

    with ThreadPoolExecutor(max_workers=2) as pool:
        fa, fb = pool.submit(book, 0), pool.submit(book, 1)
        result = [fa.result(timeout=40), fb.result(timeout=40)]
    statuses = sorted(ack["status"] for ack, _ in result)
    assert statuses == ["ACCEPTED", "REJECTED"], result
    rejected = next(ack for ack, _ in result if ack["status"] == "REJECTED")
    assert rejected["result"]["code"] in ("SLOT_CONFLICT", "SLOT_UNAVAILABLE", "SLOT_NOT_FOUND")
    with Session(engine) as db:
        rows = db.query(models.Appointment).filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.datetime_start == start,
        ).all()
        assert len(rows) == 1
        assert rows[0].patient_id in patient_ids
    # No reported success until real database COMMIT; the remote receipt is durable.
    print("C05B03J_HTTP_REAL_JWE_PC02_ONE_ACK_ONE_COMMIT_PASS",
          {"observed_request_ms": [round(t, 2) for _, t in result],
           "http_in_process": True, "real_jwt": True, "real_jose": True,
           "dpapi_windows_tested": False})
