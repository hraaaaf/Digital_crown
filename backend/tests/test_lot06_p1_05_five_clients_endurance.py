"""LOT06 P1-05: five concurrent lab clients; real services and disposable SQLite WAL.

Each separate CI runner executes this test independently with five concurrent
client sessions against ONE file-backed database on that runner. Matrix runners
DO NOT share a server, DB, or Tailnet. Never report this as a five-VM shared
network certification or physical cabinet endurance test.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from io import BytesIO
import os
from pathlib import Path
from threading import Barrier
from time import monotonic
import platform
import uuid

from PIL import Image
from sqlalchemy.orm import Session

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionMessage
from backend.services.patient_companion_agenda import create_appointment, issue_slots
from backend.services.patient_companion_messages import handle_message_send
from backend.services.clinical_asset_ingestion import ingest_clinical_asset_bytes
from backend.services.clinical_asset_storage import read_clinical_asset_bytes
from backend.tests.test_lot06_c05b03i_concurrent_services import synthetic_cabinet

CLIENT_COUNT = 5
ROUNDS = 24
TOTAL_TRANSACTIONS = CLIENT_COUNT * ROUNDS


def _jpeg(round_no: int) -> bytes:
    img = Image.new("RGB", (48, 32), (
        (50 + round_no * 3) % 255,
        (90 + round_no * 5) % 255,
        (130 + round_no * 7) % 255,
    ))
    b = BytesIO()
    img.save(b, format="JPEG")
    return b.getvalue()


def _percentile(values: list[float], percent: int) -> float:
    ordered = sorted(values)
    index = max(0, (len(ordered) * percent + 99) // 100 - 1)
    return round(ordered[index], 2)


def test_p1_05_five_clients_24_rounds_shared_sqlite_media_integrity(
    synthetic_cabinet, tmp_path, monkeypatch,
):
    assert os.environ["ENVIRONMENT"] == "test"
    assert os.environ["DIGITALCROWN_ISOLATED_RUNTIME"] == "true"
    assert os.environ["C05B03H_NETWORK_POLICY_APPROVED"] == "false"
    assert int(os.environ.get("P105_HOST_INDEX", "0")) in range(1, 6)
    engine, employer_id, access_ids, patient_ids = synthetic_cabinet
    media_root = tmp_path / "P1-05-synthetic-encrypted-media"
    monkeypatch.setenv("MEDIA_ROOT", str(media_root))
    assert not media_root.exists()
    durations: list[float] = []
    image_ids: list[int] = []
    expected_images: dict[int, bytes] = {}
    launch = monotonic()

    for round_no in range(ROUNDS):
        # Different appointment slots to avoid intentionally manufacturing
        # an overlap: P0 already certifies same-slot double booking.
        start = datetime(2034, 1, 1, 10) + timedelta(days=round_no)
        with Session(engine) as db:
            refs = []
            for offset, access_id in enumerate(access_ids):
                access = db.get(PatientCompanionAccess, access_id)
                options = issue_slots(
                    db, access=access, starts=[start + timedelta(hours=offset)],
                    duration_minutes=30, practitioner_id=employer_id,
                )
                assert len(options) == 1
                refs.append(options[0]["slot_ref"])
            db.commit()

        gate = Barrier(CLIENT_COUNT)

        def book(index: int):
            with Session(engine) as db:
                access = db.get(PatientCompanionAccess, access_ids[index])
                gate.wait(timeout=20)
                t0 = monotonic()
                result = create_appointment(db, access, {"slot_ref": refs[index]})
                assert result.status == "ACCEPTED", result.response
                db.commit()
                return ("appointment", (monotonic() - t0) * 1000, access.patient_id)

        def message(index: int):
            with Session(engine) as db:
                access = db.get(PatientCompanionAccess, access_ids[index])
                gate.wait(timeout=20)
                t0 = monotonic()
                result = handle_message_send(db, access, {
                    "client_message_id": str(uuid.uuid4()),
                    "body": f"P105 patient-{index} round-{round_no}",
                })
                assert result.status == "ACCEPTED", result.response
                db.commit()
                return ("message", (monotonic() - t0) * 1000, access.patient_id)

        photo = _jpeg(round_no)
        def media():
            with Session(engine) as db:
                gate.wait(timeout=20)
                t0 = monotonic()
                result = ingest_clinical_asset_bytes(
                    db,
                    employer_id=employer_id,
                    patient_id=patient_ids[0],
                    asset_type="PHOTO",
                    source_kind="DEVICE_CAPTURE",
                    content=photo,
                    claimed_mime_type="image/jpeg",
                    source_ref=f"P1-05-LAB-{round_no}",
                    created_by=employer_id,
                )
                db.commit()
                return ("asset", (monotonic() - t0) * 1000, result.asset.id)

        # Five distinct SQLAlchemy sessions / OS threads, concurrently entering
        # real booking, messaging and encrypted image ingestion code.
        with ThreadPoolExecutor(max_workers=CLIENT_COUNT) as pool:
            results = [
                f.result(timeout=50) for f in [
                    pool.submit(book, 0),
                    pool.submit(book, 1),
                    pool.submit(message, 0),
                    pool.submit(message, 1),
                    pool.submit(media),
                ]
            ]
        assert [r[0] for r in results] == [
            "appointment", "appointment", "message", "message", "asset",
        ]
        assert [r[2] for r in results[:4]] == [
            patient_ids[0], patient_ids[1], patient_ids[0], patient_ids[1],
        ]
        durations.extend(row[1] for row in results)
        image_ids.append(results[4][2])
        expected_images[results[4][2]] = photo

    assert len(durations) == TOTAL_TRANSACTIONS
    assert len(set(image_ids)) == ROUNDS
    elapsed_ms = (monotonic() - launch) * 1000
    engine.dispose()  # Reopen independent physical SQLite connections on disk.

    with Session(engine) as db:
        appointments = db.query(models.Appointment).filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.datetime_start >= datetime(2034, 1, 1),
            models.Appointment.datetime_start < datetime(2034, 3, 1),
        ).all()
        assert len(appointments) == 2 * ROUNDS
        assert sum(x.patient_id == patient_ids[0] for x in appointments) == ROUNDS
        assert sum(x.patient_id == patient_ids[1] for x in appointments) == ROUNDS

        for index, access_id in enumerate(access_ids):
            messages = db.query(PatientCompanionMessage).filter(
                PatientCompanionMessage.access_id == access_id,
            ).all()
            assert len(messages) == ROUNDS
            assert len({x.client_message_id for x in messages}) == ROUNDS
            assert all(x.patient_id == patient_ids[index] for x in messages)
            assert all(f"patient-{index}" in x.body for x in messages)
        originals = db.query(ClinicalAsset).filter(
            ClinicalAsset.employer_id == employer_id,
            ClinicalAsset.source_kind == "DEVICE_CAPTURE",
            ClinicalAsset.source_ref.like("P1-05-LAB-%"),
        ).all()
        assert len(originals) == ROUNDS
        assert all(x.patient_id == patient_ids[0] for x in originals)
        for asset in originals:
            assert asset.id in expected_images
            assert read_clinical_asset_bytes(
                db, employer_id=employer_id, patient_id=patient_ids[0],
                asset_id=asset.id, media_root=media_root,
            ) == expected_images[asset.id]
        derivatives = db.query(ClinicalAsset).filter(
            ClinicalAsset.parent_asset_id.in_(image_ids),
            ClinicalAsset.source_kind == "DERIVED",
        ).all()
        assert len(derivatives) == ROUNDS

    # Counts and cryptographic content are authoritative; latency is observed
    # on disposable CI VMs and is NOT a production SLA.
    measurements = {
        "runner_slot": int(os.environ["P105_HOST_INDEX"]),
        "runner_name": os.environ.get("RUNNER_NAME", "unknown"),
        "host": platform.node(),
        "parallel_sessions": CLIENT_COUNT,
        "rounds": ROUNDS,
        "transactions": len(durations),
        "elapsed_ms": round(elapsed_ms, 2),
        "observed_p50_ms": _percentile(durations, 50),
        "observed_p95_ms": _percentile(durations, 95),
        "observed_p99_ms": _percentile(durations, 99),
        "message_count": 2 * ROUNDS,
        "appointment_count": 2 * ROUNDS,
        "encrypted_asset_count": ROUNDS,
        "isolated_runner_db": True,
        "five_runners_same_backend": False,
        "tailnet_network_tested": False,
        "physical_5vm_certified": False,
    }
    print("LOT06_P1_05_FIVE_PARALLEL_CLIENTS_SHARED_DB_ENDURANCE_PASS", measurements)
