"""LOT08.2-D LAB FUE-I: real local SQLite auth/device/Queue join.

Only synthetic stores under pytest tmp_path; no patient, API, physical device,
clinical migrations or installer. Prove QR consumption shares the queue COMMIT.
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timedelta, timezone
from threading import Event
import sqlite3

import pytest
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session

from queue_core.domain import QueueDomainError
from queue_core.persistence.base import QueueBase
from queue_core.persistence.models import (
    QueueTenant, QueueLine, QueueVisitRecord, QueueEventRecord,
)
from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.device_pairing_lab import (
    DeviceKind, DeviceCapability, DeviceIdentityError,
)
from queue_core.security.device_store_lab import DurableDeviceStoreLab
from queue_core.security.rbac import Role, AuthorizationError
from queue_core.service.authorized_queue import AuthorizedLocalQueue
from queue_core.service.kiosk_qr_lab import KioskQrArrivalLab


NOW = datetime(2030, 2, 1, 10, tzinfo=timezone.utc)
PASS = "SyntheticOnly!!Password2026"


@pytest.fixture
def lab(tmp_path):
    epoch = [1_800_000_000]
    auth = LocalIdentityStore(
        tmp_path / "auth-synthetic.sqlite",
        local_guard=lambda: None, clock=lambda: epoch[0],
    )
    challenge = auth.begin_bootstrap()
    auth.enroll_first_admin(challenge, "syntheticadmin", PASS)
    admin = auth.login("syntheticadmin", PASS)
    operators = LocalOperatorStore(auth, clock=lambda: epoch[0])
    operators.bind_first_admin(first_admin_session=admin, tenant_id="T1")
    operators.create_operator(
        admin, "reception1", PASS, Role.RECEPTION, queue_ids=("Q1",),
    )
    reception = operators.login_operator("T1", "reception1", PASS)

    engine = create_engine("sqlite+pysqlite:///" + str(tmp_path / "queue-synthetic.sqlite"))
    QueueBase.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            QueueTenant(id="T1", timezone_name="Africa/Casablanca", created_at_utc=NOW),
            QueueTenant(id="T2", timezone_name="Africa/Casablanca", created_at_utc=NOW),
            QueueLine(id="Q1", tenant_id="T1", queue_key="LAB-Q1", is_active=True),
            QueueLine(id="Q2", tenant_id="T2", queue_key="LAB-Q2", is_active=True),
            QueueVisitRecord(
                id="V1", tenant_id="T1", queue_id="Q1", visit_kind="APPOINTMENT",
                status="PLANNED", scheduled_at_utc=NOW-timedelta(hours=1), version=0,
            ),
            QueueVisitRecord(
                id="V2", tenant_id="T1", queue_id="Q1", visit_kind="APPOINTMENT",
                status="EN_ROUTE", scheduled_at_utc=NOW+timedelta(hours=1), version=0,
            ),
            QueueVisitRecord(
                id="V3", tenant_id="T2", queue_id="Q2", visit_kind="APPOINTMENT",
                status="PLANNED", scheduled_at_utc=NOW, version=0,
            ),
            QueueVisitRecord(
                id="W1", tenant_id="T1", queue_id="Q1", visit_kind="WALK_IN",
                status="PLANNED", scheduled_at_utc=None, version=0,
            ),
            QueueVisitRecord(
                id="N1", tenant_id="T1", queue_id="Q1", visit_kind="APPOINTMENT",
                status="NO_SHOW", scheduled_at_utc=NOW, version=0,
            ),
        ])
        db.commit()
    queue = AuthorizedLocalQueue(operators, engine, clock=lambda: NOW)
    devices = DurableDeviceStoreLab(
        operators, tmp_path / "devices-synthetic.sqlite", clock=lambda: epoch[0],
    )
    devices.initialize_lab()
    qr = KioskQrArrivalLab(
        queue, devices, epoch_clock=lambda: epoch[0], utc_clock=lambda: NOW,
    )
    qr.initialize_lab()
    ticket = devices.issue(
        admin, tenant_id="T1", device_id="K1", kind=DeviceKind.KIOSK,
    )
    kiosk = devices.redeem(tenant_id="T1", device_id="K1", ticket=ticket)
    return {
        "auth":auth, "admin":admin, "operators":operators,
        "reception":reception, "engine":engine, "devices":devices,
        "kiosk":kiosk, "service":queue, "qr":qr, "epoch":epoch,
    }


def _events(lab):
    with Session(lab["engine"]) as db:
        return list(db.scalars(select(QueueEventRecord).order_by(
            QueueEventRecord.aggregate_version,
        )))


def _visit(lab, key="V1"):
    with Session(lab["engine"]) as db:
        row = db.get(QueueVisitRecord, key)
        return (row.status, row.version, row.queue_sequence)


def _receipt(lab):
    with lab["engine"].connect() as db:
        return db.execute(text(
            "SELECT consumed_epoch,request_digest,result_version,result_sequence "
            "FROM queue_presence_qr_lab"
        )).mappings().all()


def test_qr_issue_redeem_and_idempotent_same_request_exactly_two_device_events(lab):
    qr = lab["qr"].issue(lab["reception"], "V1")
    original = lab["qr"].redeem(
        lab["kiosk"], qr, tenant_id="T1", request_key="request-key-000001",
    )
    assert (original.id, original.status, original.version, original.queue_sequence) == (
        "V1", "WAITING", 2, 1,
    )
    events = _events(lab)
    assert [x.event_type for x in events] == ["ARRIVED", "WAITING_ENTERED"]
    assert [x.aggregate_version for x in events] == [1, 2]
    assert all(x.actor_kind == "DEVICE" and x.method == "KIOSK_QR" for x in events)
    assert all(x.actor_ref.startswith("dev_") and "K1" not in x.actor_ref for x in events)
    assert lab["qr"].redeem(
        lab["kiosk"], qr, tenant_id="T1", request_key="request-key-000001",
    ) == original
    assert len(_events(lab)) == 2
    with pytest.raises(QueueDomainError, match="QR_REJECTED"):
        lab["qr"].redeem(
            lab["kiosk"], qr, tenant_id="T1", request_key="request-key-000002",
        )
    assert len(_events(lab)) == 2


def test_issue_wrong_role_tenant_walkin_and_no_show_fail_closed(lab):
    for visit in ("V3", "W1", "N1"):
        with pytest.raises((AuthorizationError, QueueDomainError)):
            lab["qr"].issue(lab["reception"], visit)
    with pytest.raises(AuthorizationError):
        lab["qr"].issue(lab["admin"], "V1")
    assert _events(lab) == []


def test_device_wall_wrong_tenant_revocation_expiry_deny_without_arrival(lab):
    qr = lab["qr"].issue(lab["reception"], "V1", ttl_seconds=300)
    ticket = lab["devices"].issue(
        lab["admin"], tenant_id="T1", device_id="W1", kind=DeviceKind.WALL,
    )
    wall = lab["devices"].redeem(tenant_id="T1", device_id="W1", ticket=ticket)
    with pytest.raises(DeviceIdentityError):
        lab["qr"].redeem(
            wall, qr, tenant_id="T1", request_key="request-key-000001",
        )
    with pytest.raises(DeviceIdentityError):
        lab["qr"].redeem(
            lab["kiosk"], qr, tenant_id="T2", request_key="request-key-000001",
        )
    lab["epoch"][0] += 300
    with pytest.raises(QueueDomainError, match="QR_REJECTED"):
        lab["qr"].redeem(
            lab["kiosk"], qr, tenant_id="T1", request_key="request-key-000001",
        )
    lab["devices"].revoke(lab["admin"], tenant_id="T1", device_id="K1")
    with pytest.raises(DeviceIdentityError):
        lab["qr"].redeem(
            lab["kiosk"], qr, tenant_id="T1", request_key="request-key-000001",
        )
    assert _visit(lab) == ("PLANNED", 0, None)
    assert _events(lab) == []


def test_reissue_invalidates_old_qr_and_en_route_is_allowed(lab):
    old = lab["qr"].issue(lab["reception"], "V2")
    current = lab["qr"].issue(lab["reception"], "V2")
    with pytest.raises(QueueDomainError, match="QR_REJECTED"):
        lab["qr"].redeem(
            lab["kiosk"], old, tenant_id="T1", request_key="request-key-000003",
        )
    arrived = lab["qr"].redeem(
        lab["kiosk"], current, tenant_id="T1", request_key="request-key-000004",
    )
    assert arrived.status == "WAITING"
    assert _visit(lab, "V2") == ("WAITING", 2, 1)
    assert len(_events(lab)) == 2


def test_rollback_after_sql_flush_preserves_unconsumed_qr_and_visit(lab, monkeypatch):
    token = lab["qr"].issue(lab["reception"], "V1")
    original = lab["service"]._commit_plan

    def fail_after_sql_flush(db, row, plan, now):
        original(db, row, plan, now)
        db.flush()
        raise RuntimeError("synthetic-fault-before-qr-consumption")

    monkeypatch.setattr(lab["service"], "_commit_plan", fail_after_sql_flush)
    with pytest.raises(RuntimeError, match="synthetic-fault"):
        lab["qr"].redeem(
            lab["kiosk"], token, tenant_id="T1", request_key="request-key-000001",
        )
    assert _visit(lab) == ("PLANNED", 0, None)
    assert len(_events(lab)) == 0
    assert _receipt(lab)[0]["consumed_epoch"] is None
    monkeypatch.setattr(lab["service"], "_commit_plan", original)
    result = lab["qr"].redeem(
        lab["kiosk"], token, tenant_id="T1", request_key="request-key-000001",
    )
    assert result.status == "WAITING"
    assert len(_events(lab)) == 2


def test_concurrent_two_qr_scans_have_one_winner_one_replay_denied(lab):
    token = lab["qr"].issue(lab["reception"], "V1")

    def redeem(key):
        try:
            return lab["qr"].redeem(
                lab["kiosk"], token, tenant_id="T1", request_key=key,
            ).status
        except QueueDomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(redeem, (
            "request-key-000001", "request-key-000002",
        )))
    assert sorted(statuses) == ["QR_REJECTED", "WAITING"]
    assert _visit(lab) == ("WAITING", 2, 1)
    assert len(_events(lab)) == 2


def test_revoke_while_kiosk_is_in_queue_commit_waits_then_blocks_new_requests(lab, monkeypatch):
    token = lab["qr"].issue(lab["reception"], "V1")
    reached = Event()
    release = Event()
    revoked_started = Event()
    original = lab["service"]._commit_plan

    def paused(db, row, plan, now):
        reached.set()
        assert release.wait(timeout=12)
        original(db, row, plan, now)

    monkeypatch.setattr(lab["service"], "_commit_plan", paused)

    def revoke():
        revoked_started.set()
        lab["devices"].revoke(
            lab["admin"], tenant_id="T1", device_id="K1",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        arrival = pool.submit(
            lab["qr"].redeem, lab["kiosk"], token,
            tenant_id="T1", request_key="request-key-000001",
        )
        assert reached.wait(timeout=9)
        revoking = pool.submit(revoke)
        assert revoked_started.wait(timeout=9)
        with pytest.raises(TimeoutError):
            revoking.result(timeout=0.2)
        release.set()
        assert arrival.result(timeout=12).status == "WAITING"
        assert revoking.result(timeout=12) is None
    with pytest.raises(DeviceIdentityError):
        lab["qr"].redeem(
            lab["kiosk"], token, tenant_id="T1", request_key="request-key-000001",
        )
    assert len(_events(lab)) == 2


def test_no_raw_credential_stored_in_any_database(lab):
    qr = lab["qr"].issue(lab["reception"], "V1")
    lab["qr"].redeem(
        lab["kiosk"], qr, tenant_id="T1", request_key="request-key-000001",
    )
    for database in (
        lab["operators"].auth.path,
        lab["devices"].path,
        lab["engine"].url.database,
    ):
        data = open(database, "rb").read()
        assert qr.encode() not in data
        assert lab["kiosk"].encode() not in data


def test_invalid_idempotency_key_rejected_before_any_commit(lab):
    qr = lab["qr"].issue(lab["reception"], "V1")
    with pytest.raises(QueueDomainError, match="QR_REQUEST_INVALID"):
        lab["qr"].redeem(
            lab["kiosk"], qr, tenant_id="T1", request_key="too-short",
        )
    assert _receipt(lab)[0]["consumed_epoch"] is None
    assert _visit(lab) == ("PLANNED", 0, None)


def test_real_os_kill_after_qr_consumption_sql_before_commit_recovers_all_facts(
    lab, tmp_path,
):
    """Separate process SIGKILL after QR update SQL, before Queue commit.

    The Queue visit, 2 events and QR consumption must all roll back together.
    This does not simulate a physical power cut or a real patient/device.
    """
    import os
    from pathlib import Path
    import subprocess
    import sys
    import time

    ticket = lab["qr"].issue(lab["reception"], "V1")
    marker = tmp_path / "qr-commit-in-flight.marker"
    child = r'''
import os
from pathlib import Path
import time
from datetime import datetime, timezone
from sqlalchemy import create_engine, event

from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.security.device_store_lab import DurableDeviceStoreLab
from queue_core.service.authorized_queue import AuthorizedLocalQueue
from queue_core.service.kiosk_qr_lab import KioskQrArrivalLab

epoch = 1_800_000_000
auth = LocalIdentityStore(
    os.environ["LAB_AUTH_DB"], clock=lambda: epoch,
    local_guard=lambda: None,
)
operators = LocalOperatorStore(auth, clock=lambda: epoch)
engine = create_engine("sqlite+pysqlite:///" + os.environ["LAB_QUEUE_DB"])
queue = AuthorizedLocalQueue(
    operators, engine,
    clock=lambda: datetime(2030, 2, 1, 10, tzinfo=timezone.utc),
)
devices = DurableDeviceStoreLab(
    operators, os.environ["LAB_DEVICE_DB"], clock=lambda: epoch,
)

@event.listens_for(engine, "after_cursor_execute")
def freeze_after_qr_update(conn, cursor, statement, parameters, context, many):
    if "UPDATE queue_presence_qr_lab SET" in statement:
        Path(os.environ["LAB_OS_KILL_MARKER"]).write_text(
            "AFTER_QR_CONSUMED_SQL_BEFORE_COMMIT"
        )
        time.sleep(120)

junction = KioskQrArrivalLab(
    queue, devices, epoch_clock=lambda: epoch,
    utc_clock=lambda: datetime(2030, 2, 1, 10, tzinfo=timezone.utc),
)
junction.redeem(
    os.environ["LAB_DEVICE_BEARER"],
    os.environ["LAB_QR_BEARER"],
    tenant_id="T1",
    request_key="request-key-os-kill-0001",
)
'''
    env = os.environ.copy()
    env.update({
        "LAB_AUTH_DB": str(lab["auth"].path),
        "LAB_DEVICE_DB": str(lab["devices"].path),
        "LAB_QUEUE_DB": str(lab["engine"].url.database),
        "LAB_DEVICE_BEARER": lab["kiosk"],
        "LAB_QR_BEARER": ticket,
        "LAB_OS_KILL_MARKER": str(marker),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    process = subprocess.Popen(
        [sys.executable, "-B", "-c", child],
        cwd=Path(__file__).resolve().parents[2], env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 22
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        if not marker.exists():
            error = process.stderr.read(1900).decode(errors="replace") if process.poll() is not None else "deadline"
            pytest.fail("child did not reach uncommitted QR SQL: " + error)
        assert marker.read_text() == "AFTER_QR_CONSUMED_SQL_BEFORE_COMMIT"
        assert process.poll() is None
        process.kill()
        assert process.wait(timeout=10) != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        process.stdout.close()
        process.stderr.close()

    recovered = create_engine(lab["engine"].url)
    try:
        with Session(recovered) as db:
            row = db.get(QueueVisitRecord, "V1")
            assert row.status == "PLANNED" and row.version == 0
            assert db.scalar(select(func.count()).select_from(QueueEventRecord)) == 0
            receipt = db.execute(text(
                "SELECT consumed_epoch, result_version FROM queue_presence_qr_lab"
            )).mappings().one()
            assert receipt["consumed_epoch"] is None
            assert receipt["result_version"] is None
    finally:
        recovered.dispose()

    result = lab["qr"].redeem(
        lab["kiosk"], ticket, tenant_id="T1",
        request_key="request-key-os-kill-0001",
    )
    assert result.status == "WAITING" and result.version == 2
    assert len(_events(lab)) == 2
