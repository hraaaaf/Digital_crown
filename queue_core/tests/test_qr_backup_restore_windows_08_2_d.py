"""LOT08.2-D Windows-runner LAB: quiesced 3-store SQLite backup/restore.

Only deterministic synthetic fixtures. Not an installed cabinet restore, a
multi-file atomic snapshot under concurrent writes, or a physical outage test.
"""
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session

from queue_core.domain import QueueDomainError
from queue_core.persistence.models import QueueEventRecord, QueueVisitRecord
from queue_core.security.device_pairing_lab import DeviceIdentityError
from queue_core.security.device_store_lab import DurableDeviceStoreLab
from queue_core.security.local_auth import LocalIdentityStore
from queue_core.security.operator_store import LocalOperatorStore
from queue_core.service.authorized_queue import AuthorizedLocalQueue
from queue_core.service.kiosk_qr_lab import KioskQrArrivalLab
from queue_core.tests.test_kiosk_qr_lab_08_2_d import NOW, lab


def _check_sqlite(path: Path) -> None:
    assert path.is_file() and path.name.endswith("-synthetic.sqlite")
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def _quiesced_backup(source: Path, destination: Path) -> None:
    assert source.name == destination.name
    assert source.name.endswith("-synthetic.sqlite")
    assert not destination.exists()
    # All issuing and redemption calls finish before this function is entered.
    # Individual sqlite3.backup snapshots are consistent; the three files are
    # deliberately NOT claimed to be one distributed atomic snapshot.
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as db:
        with closing(sqlite3.connect(destination)) as out:
            db.backup(out)
    _check_sqlite(destination)


def _restored_lab(lab, directory):
    epoch = lab["epoch"][0]
    auth = LocalIdentityStore(
        directory / "auth-synthetic.sqlite",
        local_guard=lambda: None, clock=lambda: epoch,
    )
    operators = LocalOperatorStore(auth, clock=lambda: epoch)
    devices = DurableDeviceStoreLab(
        operators, directory / "devices-synthetic.sqlite",
        clock=lambda: epoch,
    )
    engine = create_engine(
        "sqlite+pysqlite:///" + str(directory / "queue-synthetic.sqlite")
    )
    queue = AuthorizedLocalQueue(operators, engine, clock=lambda: NOW)
    junction = KioskQrArrivalLab(
        queue, devices, epoch_clock=lambda: epoch, utc_clock=lambda: NOW,
    )
    return junction, devices, engine


def test_quiesced_backup_restore_preserves_committed_qr_and_revocation(lab, tmp_path):
    raw = lab["qr"].issue(lab["reception"], "V1")
    before = lab["qr"].redeem(
        lab["kiosk"], raw, tenant_id="T1",
        request_key="request-key-restore-0001",
    )
    assert (before.status, before.version) == ("WAITING", 2)
    restored = tmp_path / "quiesced-restore"
    restored.mkdir()
    originals = {
        "auth-synthetic.sqlite": Path(lab["auth"].path),
        "devices-synthetic.sqlite": Path(lab["devices"].path),
        "queue-synthetic.sqlite": Path(lab["engine"].url.database),
    }
    for name, source in originals.items():
        _check_sqlite(source)
        _quiesced_backup(source, restored / name)

    junction, devices, engine = _restored_lab(lab, restored)
    try:
        replay = junction.redeem(
            lab["kiosk"], raw, tenant_id="T1",
            request_key="request-key-restore-0001",
        )
        assert replay == before
        with Session(engine) as db:
            visit = db.get(QueueVisitRecord, "V1")
            assert (visit.status, visit.version, visit.queue_sequence) == (
                "WAITING", 2, 1,
            )
            assert db.scalar(select(func.count()).select_from(QueueEventRecord)) == 2
            receipt = db.execute(text(
                "SELECT consumed_epoch,result_version FROM queue_presence_qr_lab"
            )).mappings().one()
            assert receipt["consumed_epoch"] is not None
            assert receipt["result_version"] == 2
        with pytest.raises(QueueDomainError, match="QR_REJECTED"):
            junction.redeem(
                lab["kiosk"], raw, tenant_id="T1",
                request_key="request-key-restore-0002",
            )
        # Device revocation on restored storage must also block the old bearer.
        devices.revoke(lab["admin"], tenant_id="T1", device_id="K1")
        with pytest.raises(DeviceIdentityError):
            junction.redeem(
                lab["kiosk"], raw, tenant_id="T1",
                request_key="request-key-restore-0001",
            )
    finally:
        engine.dispose()


def test_restore_gate_refuses_missing_and_corrupted_sqlite(lab, tmp_path):
    restored = tmp_path / "invalid-restore"
    restored.mkdir()
    missing = restored / "queue-synthetic.sqlite"
    with pytest.raises(AssertionError):
        _check_sqlite(missing)
    _quiesced_backup(Path(lab["engine"].url.database), missing)
    with missing.open("r+b") as dest:
        dest.seek(0)
        dest.write(b"CORRUPT-SQLITE-HEADER")
    with pytest.raises(sqlite3.DatabaseError):
        _check_sqlite(missing)
