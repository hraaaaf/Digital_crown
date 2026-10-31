"""LOT06 C05B-03J — five blocking P0 synthetic cabinet FUE.

Authentic FastAPI handlers / patient JWT / JWS-JWE / remote receipts and real
file-backed SQLite transactions. No real patient/device/Tailnet/DPAPI.
P0-04 covers operations arriving AFTER revocation COMMIT, NOT already in flight.
P0-05 injects a genuine SQLAlchemy Session before_commit failure: no positive
HTTP ACK may be returned, and the command+receipt must rollback together.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier, Event
from time import monotonic
import uuid

from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionMessage,
    PatientCompanionRemoteReceipt,
)
from backend.routers.patient_companion_messages import staff_message_thread
from backend.services.patient_companion_agenda import issue_slots
from backend.tests.test_lot06_c05b03j_http_clinic import (
    _ack, _command, _fixture, _post,
)
from backend.tests.test_lot06_c05b03i_concurrent_services import synthetic_cabinet


def _slots(engine, employer_id, users, start):
    with Session(engine) as db:
        refs = []
        for user in users:
            access = db.get(PatientCompanionAccess, user["access_id"])
            issued = issue_slots(
                db, access=access, starts=[start],
                duration_minutes=30, practitioner_id=employer_id,
            )
            assert len(issued) == 1
            refs.append(issued[0]["slot_ref"])
        db.commit()
        return refs


def _appointment_rows(engine, employer_id, start):
    with Session(engine) as db:
        return [
            (row.id, row.patient_id)
            for row in db.query(models.Appointment).filter(
                models.Appointment.employer_id == employer_id,
                models.Appointment.datetime_start == start,
            ).all()
        ]


def test_p0_01_last_slot_double_click_race_exact_one_commit_and_ack(
    synthetic_cabinet, monkeypatch,
):
    app, engine, employer_id, users, patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    timings = []
    for round_index in range(2):
        start = datetime(2030, 3, 4, 10) + timedelta(days=round_index)
        refs = _slots(engine, employer_id, users, start)
        barrier = Barrier(2)
        blobs = [
            _command(user, "agenda.create", {"slot_ref": refs[index]})
            for index, user in enumerate(users)
        ]

        def contender(index):
            barrier.wait(timeout=12)
            t0 = monotonic()
            result = _ack(users[index], _post(app, users[index], "agenda", blobs[index]))
            return result, (monotonic() - t0) * 1000

        with ThreadPoolExecutor(max_workers=2) as pool:
            fa = pool.submit(contender, 0)
            fb = pool.submit(contender, 1)
            outcomes = [fa.result(timeout=40), fb.result(timeout=40)]
        assert sorted(result["status"] for result, _ in outcomes) == [
            "ACCEPTED", "REJECTED"
        ], (round_index, outcomes)
        assert sum(result["status"] == "ACCEPTED" for result, _ in outcomes) == 1
        assert len(_appointment_rows(engine, employer_id, start)) == 1
        assert _appointment_rows(engine, employer_id, start)[0][1] in patient_ids
        timings.extend(ms for _, ms in outcomes)
    print("LOT06_P0_01_REAL_HTTP_TWO_SLOT_RACES_RATE_LIMIT_RETAINED_PASS",
          {"rounds": 2, "requests": 4, "samples": len(timings)})


def test_p0_02_lost_ack_retry_booking_idempotent_and_replay_blocked(
    synthetic_cabinet, monkeypatch,
):
    app, engine, employer_id, users, _ = _fixture(synthetic_cabinet, monkeypatch)
    user = users[0]
    start = datetime(2030, 4, 2, 10)
    ref = _slots(engine, employer_id, users, start)[0]
    key = uuid.uuid4()
    original = _command(user, "agenda.create", {"slot_ref": ref}, key=key)

    # Simulate dropped response on client: send but NEVER read/decrypt first ACK.
    network_response = _post(app, user, "agenda", original)
    assert network_response.status_code == 200
    del network_response
    retry = _command(user, "agenda.create", {"slot_ref": ref}, key=key)
    replay_ack = _ack(user, _post(app, user, "agenda", retry))
    assert replay_ack["status"] == "ACCEPTED"
    result_ref = replay_ack["result"]["appointment_ref"]
    assert isinstance(result_ref, str) and len(result_ref) == 36
    # Same signed message_id replay is forbidden; only fresh-message same-intent retries work.
    duplicate_message = _post(app, user, "agenda", original)
    assert duplicate_message.status_code == 400, duplicate_message.text[:250]
    changed_operation = _command(user, "agenda.cancel",
        {"appointment_ref": result_ref}, key=key)
    cross_operation = _post(app, user, "agenda", changed_operation)
    assert cross_operation.status_code == 400, cross_operation.text[:250]

    rows = _appointment_rows(engine, employer_id, start)
    assert len(rows) == 1
    with Session(engine) as db:
        receipts = db.query(PatientCompanionRemoteReceipt).filter_by(
            access_id=user["access_id"], idempotency_key=str(key),
        ).all()
        assert len(receipts) == 1
        assert receipts[0].status == "ACCEPTED"
        assert receipts[0].operation == "agenda.create"
    print("LOT06_P0_02_LOST_ACK_BOOKING_RETRY_ONE_DURABLE_RECEIPT_PASS")


def test_p0_03_two_patient_messages_while_staff_reads_no_leaks(
    synthetic_cabinet, monkeypatch,
):
    app, engine, employer_id, users, patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    rounds = 7
    gate = Barrier(3)

    def send_messages(index):
        user = users[index]
        gate.wait(timeout=12)
        for j in range(rounds):
            body = f"LOT06-P0-patient-{index}-message-{j}"
            ack = _ack(user, _post(app, user, "messages", _command(
                user, "message.send",
                {"client_message_id": str(uuid.uuid4()), "body": body},
            )))
            assert ack["status"] == "ACCEPTED", ack
        return True

    def dentist_read():
        gate.wait(timeout=12)
        counts = []
        for _ in range(rounds):
            with Session(engine) as db:
                doctor = db.get(models.User, employer_id)
                for index in (0, 1):
                    # Real staff handler (staff access gate, patient/tenant scoping),
                    # not staff HTTP workstation/JWT certification.
                    result = staff_message_thread(
                        patient_ids[index], Response(), None, 50, db, doctor,
                    )
                    items = result["items"]
                    assert all(
                        f"LOT06-P0-patient-{index}-" in item["body"]
                        for item in items
                    ), (index, items)
                    counts.append(len(items))
        return counts

    with ThreadPoolExecutor(max_workers=3) as pool:
        fa = pool.submit(send_messages, 0)
        fb = pool.submit(send_messages, 1)
        fc = pool.submit(dentist_read)
        assert fa.result(timeout=60) and fb.result(timeout=60)
        assert len(fc.result(timeout=60)) == rounds * 2

    with Session(engine) as db:
        doctor = db.get(models.User, employer_id)
        for index, user in enumerate(users):
            rows = db.query(PatientCompanionMessage).filter(
                PatientCompanionMessage.patient_id == patient_ids[index],
            ).all()
            assert len(rows) == rounds
            staff = staff_message_thread(
                patient_ids[index], Response(), None, 50, db, doctor,
            )
            assert len(staff["items"]) == rounds
            assert all(f"patient-{index}-" in item["body"] for item in staff["items"])
            # A patient-scoped cursor never exposes messages from the other patient.
            sync = _ack(user, _post(app, user, "messages",
                _command(user, "message.sync", {})))
            assert sync["status"] == "ACCEPTED"
            assert len(sync["result"]["items"]) == rounds
            assert all(f"patient-{index}-" in item["body"]
                       for item in sync["result"]["items"])
            assert all(item["staff_read_at"] is None
                       for item in sync["result"]["items"])
    print("LOT06_P0_03_REAL_HTTP_TWO_PATIENTS_STAFF_READ_NO_CROSS_LEAK_PASS")


def test_p0_04_revocation_committed_while_cabinet_active_denies_new_commands(
    synthetic_cabinet, monkeypatch,
):
    app, engine, _employer_id, users, _ = _fixture(synthetic_cabinet, monkeypatch)
    a, b = users
    proceed = Event()
    revoked = Event()

    def patient_after_revocation():
        assert proceed.wait(timeout=12)
        response = _post(app, a, "messages", _command(a, "message.send", {
            "client_message_id": str(uuid.uuid4()),
            "body": "message after revocation must be blocked",
        }))
        return response.status_code

    def revoke_during_other_activity():
        valid = _ack(b, _post(app, b, "messages",
            _command(b, "message.send", {
                "client_message_id": str(uuid.uuid4()),
                "body": "patient B stays active",
            })))
        assert valid["status"] == "ACCEPTED"
        with Session(engine) as db:
            db.get(PatientCompanionAccess, a["access_id"]).revoked_at = datetime.utcnow()
            db.commit()
        revoked.set()
        proceed.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(patient_after_revocation)
        action = pool.submit(revoke_during_other_activity)
        action.result(timeout=30)
        assert pending.result(timeout=30) == 401
    assert revoked.is_set()
    with Session(engine) as db:
        assert db.query(PatientCompanionMessage).filter_by(
            access_id=a["access_id"],
        ).count() == 0
        assert db.query(PatientCompanionMessage).filter_by(
            access_id=b["access_id"],
        ).count() == 1
    again = _ack(b, _post(app, b, "messages",
        _command(b, "message.sync", {})))
    assert again["status"] == "ACCEPTED" and len(again["result"]["items"]) == 1
    print("LOT06_P0_04_AFTER_REVOCATION_COMMIT_NEW_HTTP_COMMAND_DENIED_PASS",
          {"in_flight_race_proved": False})


def test_p0_05_injected_commit_failure_rolls_back_message_and_receipt_no_ack(
    synthetic_cabinet, monkeypatch,
):
    app, engine, _employer_id, users, _ = _fixture(synthetic_cabinet, monkeypatch)
    a = users[0]
    key = uuid.uuid4()
    blob = _command(a, "message.send", {
        "client_message_id": str(uuid.uuid4()),
        "body": "rollback atomicity P0 synthetic",
    }, key=key)
    state = {"raised": False}

    def crash_before_commit(session):
        if state["raised"] or session.get_bind() is not engine:
            return
        # Fault only when the exact remote receipt and domain message are
        # staged; avoid failing unrelated setup/authorization transactions.
        pending = session.query(PatientCompanionRemoteReceipt).filter_by(
            access_id=a["access_id"], idempotency_key=str(key),
        ).count()
        if pending:
            assert session.query(PatientCompanionMessage).filter_by(
                access_id=a["access_id"],
            ).count() == 1
            state["raised"] = True
            raise RuntimeError("P0 synthetic DB commit rejected before durable ACK")

    event.listen(Session, "before_commit", crash_before_commit)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            failed = client.post(
                "/contexts/" + a["public_id"] + "/messages/remote-command",
                headers={"Authorization": a["authorization"]},
                json={"blob": blob},
            )
    finally:
        event.remove(Session, "before_commit", crash_before_commit)
    assert state["raised"], "fault injection did not reach real commit boundary"
    assert failed.status_code >= 500, (failed.status_code, failed.text[:200])
    assert "blob" not in failed.text
    with Session(engine) as db:
        assert db.query(PatientCompanionMessage).filter_by(
            access_id=a["access_id"],
        ).count() == 0
        assert db.query(PatientCompanionRemoteReceipt).filter_by(
            access_id=a["access_id"], idempotency_key=str(key),
        ).count() == 0
    # Post-failure retry: identical signed command is now admissible because
    # no successful command receipt was ever committed.
    recovered = _ack(a, _post(app, a, "messages", blob))
    assert recovered["status"] == "ACCEPTED"
    with Session(engine) as db:
        assert db.query(PatientCompanionMessage).filter_by(
            access_id=a["access_id"],
        ).count() == 1
        assert db.query(PatientCompanionRemoteReceipt).filter_by(
            access_id=a["access_id"], idempotency_key=str(key),
        ).count() == 1
    print("LOT06_P0_05_FAIL_BEFORE_COMMIT_NO_ACK_NO_GHOST_RECEIPT_RETRY_PASS")
