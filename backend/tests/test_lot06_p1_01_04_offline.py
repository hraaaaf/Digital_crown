"""LOT06 P1-01..04 synthetic no-network integration FUE.

Real ORM, file-backed SQLite, real HTTPS-in-process JWS/JWE for recovery,
encrypted Media Core files. No clinical workstation, hardware, or Tailnet.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import BytesIO
from threading import Barrier
from time import monotonic
import uuid

from fastapi import HTTPException
from PIL import Image
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.core.appointment_revision_ddl import install_appointment_revision_guard
from backend.models_media_core import ClinicalAsset
from backend.models_patient_companion import (
    PatientCompanionAccess, PatientCompanionMessage, PatientCompanionRemoteReceipt,
)
from backend.routers import appointments, mobile_resource_bridge as mobile
from backend.services.patient_companion_agenda import create_appointment, issue_slots
from backend.services.patient_companion_messages import handle_message_send
from backend.services.clinical_asset_ingestion import ingest_clinical_asset_bytes
from backend.tests.test_lot06_c05b03i_concurrent_services import synthetic_cabinet
from backend.tests.test_lot06_c05b03j_http_clinic import (
    _ack, _command, _fixture, _post,
)


class _Photo:
    filename = "synthetic.jpeg"
    content_type = "image/jpeg"
    def __init__(self, data: bytes):
        self.data, self.closed = data, False
    async def read(self, _n):
        return self.data
    async def close(self):
        self.closed = True


def _jpeg(rgb=(180, 120, 60)) -> bytes:
    image = Image.new("RGB", (80, 60), color=rgb)
    stream = BytesIO()
    image.save(stream, "JPEG")
    return stream.getvalue()


def _p95(ms: list[float]) -> float:
    ordered = sorted(ms)
    return round(ordered[max(0, (len(ms) * 95 + 99) // 100 - 1)], 2)


def test_p1_01_two_staff_independent_sessions_stale_revision_refused(synthetic_cabinet):
    engine, owner_id, _accesses, patient_ids = synthetic_cabinet
    with engine.begin() as connection:
        install_appointment_revision_guard(connection)
    with Session(engine) as db:
        secretary = models.User(
            email="p1-secretary@example.invalid", hashed_password="no-login",
            role="SECRETAIRE", nom_complet="Secretary Synthetic",
            employer_id=owner_id, permissions={"agenda": True}, is_active=True,
        )
        appt = models.Appointment(
            patient_id=patient_ids[0], employer_id=owner_id, praticien_id=owner_id,
            datetime_start=datetime(2032, 2, 3, 10), duration_minutes=30,
            status=models.AppointmentStatus.CONFIRME,
            notes="original",
        )
        untouched = models.Appointment(
            patient_id=patient_ids[1], employer_id=owner_id, praticien_id=owner_id,
            datetime_start=datetime(2032, 2, 4, 10), duration_minutes=30,
            notes="control",
        )
        db.add_all([secretary, appt, untouched])
        db.commit()
        ids = (appt.id, untouched.id, secretary.id)
    barrier = Barrier(2)

    def edit(actor_id, text):
        with Session(engine) as db:
            user = db.get(models.User, actor_id)
            # Both forms were loaded when the same DB revision was current.
            expected = db.get(models.Appointment, ids[0]).clinical_revision
            assert expected == 0
            barrier.wait(timeout=15)
            try:
                result = appointments.update_appointment(
                    ids[0],
                    schemas.AppointmentUpdate(notes=text, expected_clinical_revision=expected),
                    db=db, current_user=user,
                )
                return 200, result.clinical_revision
            except HTTPException as exc:
                db.rollback()
                return exc.status_code, str(exc.detail)

    with ThreadPoolExecutor(max_workers=2) as pool:
        doctor = pool.submit(edit, owner_id, "doctor edit")
        assistant = pool.submit(edit, ids[2], "secretary edit")
        results = [doctor.result(timeout=35), assistant.result(timeout=35)]
    assert sorted(code for code, _ in results) == [200, 409], results
    assert any(value == "APPOINTMENT_STALE_REVISION" for code, value in results if code == 409)
    with Session(engine) as db:
        revised = db.get(models.Appointment, ids[0])
        assert revised.notes in {"doctor edit", "secretary edit"}
        assert revised.clinical_revision == 1
        assert db.get(models.Appointment, ids[1]).notes == "control"
        assert db.query(models.AuditLog).filter_by(
            resource_type="Appointment", resource_id=str(ids[0]), action="UPDATE",
        ).count() == 1
    print("LOT06_P1_01_STALE_CLINICAL_REVISION_ONE_WRITER_ONE_409_PASS")


def test_p1_02_real_mobile_capture_bound_to_patient_and_idempotent(
    synthetic_cabinet, monkeypatch, tmp_path,
):
    engine, employer_id, _access_ids, patients = synthetic_cabinet
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "p1-media-encrypted"))
    with Session(engine) as db:
        # Captures use a real cabinet user and the real _patient_resource()
        # tenant check; the mobile device credential decoder itself is stubbed
        # ONLY because these are synthetic isolated test principals.
        user = db.get(models.User, employer_id)
        assert mobile.has_permission(user, "clinical")
    context = {"resource_type": "patient", "resource_id": patients[0], "device_id": "synthetic-device-a"}
    def context_for_request(db, _auth, _key):
        return db.get(models.User, employer_id), context
    monkeypatch.setattr(mobile, "_validated_mobile_context", context_for_request)
    # Audit log occurs after media DB COMMIT; do not stub the actual Media Core.
    capture_id = str(uuid.uuid4())
    data = _jpeg()

    def capture(payload, identifier=capture_id):
        with Session(engine) as db:
            return asyncio.run(mobile.upload_resource_context_photo(
                context_key="synthetic-patient-device-context",
                file=_Photo(payload), capture_id=identifier,
                authorization="Bearer synthetic-only", db=db,
            ))

    first = capture(data)
    assert first["success"] is True
    first_asset_id = first["asset"]["id"]
    with Session(engine) as db:
        assert db.get(ClinicalAsset, first_asset_id).patient_id == patients[0]
        assert db.get(ClinicalAsset, first_asset_id).stored_at is not None
    second = capture(data)
    assert second["asset"]["id"] == first_asset_id
    assert second["asset"]["thumbnail_asset_id"] == first["asset"]["thumbnail_asset_id"]
    with Session(engine) as db:
        assert db.query(ClinicalAsset).filter(
            ClinicalAsset.source_ref == "MOBILE_RESOURCE_BRIDGE:" + capture_id,
        ).count() == 1
        assert db.query(ClinicalAsset).filter(
            ClinicalAsset.parent_asset_id == first_asset_id,
        ).count() == 1

    try:
        capture(_jpeg((12, 26, 42)))
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("changed bytes with capture_id reused must be denied")

    context["resource_id"] = patients[1]
    try:
        capture(data)
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("same capture_id must never migrate patients")

    # Reconnect after client ACK loss: a retry must identify the durable asset.
    context["resource_id"] = patients[0]
    engine.dispose()
    assert capture(data)["asset"]["id"] == first_asset_id
    print("LOT06_P1_02_ENCRYPTED_CAPTURE_IDEMPOTENT_PATIENT_BOUND_PASS")


def test_p1_03_mixed_agenda_message_and_media_persist_without_cross_patient(
    synthetic_cabinet, monkeypatch, tmp_path,
):
    engine, employer_id, access_ids, patient_ids = synthetic_cabinet
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "mixed-clinic-media"))
    durations = []
    for cycle in range(3):
        start = datetime(2032, 3, 2, 10) + timedelta(days=cycle)
        with Session(engine) as db:
            access = db.get(PatientCompanionAccess, access_ids[0])
            slot = issue_slots(
                db, access=access, starts=[start],
                duration_minutes=30, practitioner_id=employer_id,
            )[0]["slot_ref"]
            db.commit()
        barrier = Barrier(3)
        photo = _jpeg((50+cycle, 70+cycle, 90+cycle))

        def book():
            with Session(engine, expire_on_commit=False) as db:
                a = db.get(PatientCompanionAccess, access_ids[0])
                barrier.wait(timeout=15)
                t0 = monotonic()
                res = create_appointment(db, a, {"slot_ref": slot})
                if res.status == "ACCEPTED":
                    db.commit()
                else:
                    db.rollback()
                return res.status, (monotonic()-t0)*1000

        def send():
            with Session(engine) as db:
                b = db.get(PatientCompanionAccess, access_ids[1])
                barrier.wait(timeout=15)
                t0 = monotonic()
                res = handle_message_send(db, b, {
                    "client_message_id": str(uuid.uuid4()),
                    "body": f"mixed cycle {cycle} recipient B",
                })
                assert res.status == "ACCEPTED"
                db.commit()
                return res.status, (monotonic()-t0)*1000

        def ingest():
            with Session(engine) as db:
                barrier.wait(timeout=15)
                t0 = monotonic()
                result = ingest_clinical_asset_bytes(
                    db, employer_id=employer_id, patient_id=patient_ids[0],
                    asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
                    content=photo, claimed_mime_type="image/jpeg",
                    created_by=employer_id, source_ref=f"P1-MIXED-{cycle}",
                )
                db.commit()
                return result.asset.id, (monotonic()-t0)*1000

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(book), pool.submit(send), pool.submit(ingest)]
            results = [future.result(timeout=40) for future in futures]
        assert results[0][0] == results[1][0] == "ACCEPTED"
        durations.extend([value for _, value in results])
    with Session(engine) as db:
        assert db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_ids[0],
            models.Appointment.datetime_start >= datetime(2032, 3, 2),
        ).count() == 3
        assert db.query(PatientCompanionMessage).filter_by(
            patient_id=patient_ids[1],
        ).count() == 3
        assert db.query(PatientCompanionMessage).filter_by(
            patient_id=patient_ids[0],
        ).count() == 0
        assert db.query(ClinicalAsset).filter(
            ClinicalAsset.patient_id == patient_ids[0],
            ClinicalAsset.source_ref.like("P1-MIXED-%"),
        ).count() == 3
    assert len(durations) == 9
    print("LOT06_P1_03_MIXED_LAB_NO_CROSS_PATIENT_PASS",
          {"samples": len(durations), "observed_p95_ms": _p95(durations),
           "http_429_under_mixed_load_proved": False, "sla_proved": False})


def test_p1_04_client_loses_signed_ack_reopen_connection_replay_is_once(
    synthetic_cabinet, monkeypatch,
):
    app, engine, _tenant, users, patient_ids = _fixture(synthetic_cabinet, monkeypatch)
    a = users[0]
    intent = uuid.uuid4()
    req = {
        "client_message_id": str(uuid.uuid4()),
        "body": "single durable recovery after lost HTTP response",
    }
    first = _ack(a, _post(app, a, "messages", _command(
        a, "message.send", req, key=intent,
    )))
    assert first["status"] == "ACCEPTED"
    # Simulate a disconnected client that never received the previous ACK.
    engine.dispose()
    duplicate = _ack(a, _post(app, a, "messages", _command(
        a, "message.send", req, key=intent,
    )))
    assert duplicate["status"] == "ACCEPTED"
    assert duplicate["result"] == first["result"]
    with Session(engine) as db:
        assert db.query(PatientCompanionMessage).filter_by(
            access_id=a["access_id"], patient_id=patient_ids[0],
        ).count() == 1
        assert db.query(PatientCompanionRemoteReceipt).filter_by(
            access_id=a["access_id"], idempotency_key=str(intent),
        ).count() == 1
    print("LOT06_P1_04_LOST_ACK_RECONNECT_ONE_RECEIPT_AND_MESSAGE_PASS")
