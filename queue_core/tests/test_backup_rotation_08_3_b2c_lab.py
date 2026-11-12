"""LOT08.3-B2-C real native synthetic SQLite/Fernet/HMAC vault FUE.

No patient fixtures, live clinic files, runtime wiring or production backup
scheduler. Tests prove bounded calendar retention and a conditional external
trusted-anchor rollback gate on disposable filesystem state.
"""
from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import (
    QueueTenant, QueueLine, QueueVisitRecord, QueueEventRecord,
)
from queue_core.service import backup_rotation_08_3_b2c_lab as rotation
from queue_core.service.backup_restore_clone_08_3_b2_lab import RestoreCloneLabError
from queue_core.service.retention_lab_08_3_b import (
    SYNTHETIC_LAB_APPLICATION_ID, retain_closed_visits_lab,
)

NOW = datetime(2030, 4, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def lab(tmp_path):
    source = tmp_path / "lot08_3_b_lab_queue_rotation.sqlite"
    vault = tmp_path / "lot08_3_b_lab_vault_primary"
    vault.mkdir()
    engine = create_engine(f"sqlite+pysqlite:///{source}")
    QueueBase.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            QueueTenant(id=t, timezone_name="Africa/Casablanca", created_at_utc=NOW)
            for t in ("T1", "T2")
        ])
        session.flush()
        session.add_all([
            QueueLine(id=f"Q{t[-1]}", tenant_id=t, queue_key="WAITING", is_active=True)
            for t in ("T1", "T2")
        ])
        session.flush()
        for n, tenant in enumerate(("T1", "T2"), 1):
            session.add(QueueVisitRecord(
                id=f"VISIT_{tenant}", tenant_id=tenant, queue_id=f"Q{n}",
                visit_kind="WALK_IN", status="WAITING", version=1,
                scheduled_at_utc=None, queue_sequence=n,
                arrival_confirmed_at_utc=NOW-timedelta(hours=3),
                waiting_since_utc=NOW-timedelta(hours=3),
            ))
        session.flush()
        session.add(QueueEventRecord(
            id="EVENT_FAKE",tenant_id="T1",visit_ref="VISIT_T1",
            aggregate_version=1,event_type="CHECK_IN",state_before="PLANNED",
            state_after="WAITING",occurred_at_utc=NOW-timedelta(hours=3),
            actor_kind="HUMAN",actor_ref="OP_SYNTH",
        ))
        session.commit()
    engine.dispose()
    with sqlite3.connect(source) as conn:
        conn.execute(f"PRAGMA application_id={SYNTHETIC_LAB_APPLICATION_ID}")
    return source, vault, Fernet.generate_key(), os.urandom(32)


def _rotate(lab, stamp, anchor=None):
    source, vault, key, signing = lab
    return rotation.rotate_queue_vault_lab(
        source, vault, backup_key=key, manifest_key=signing,
        trusted_anchor=anchor, now=stamp,
    )


def _manifest(lab):
    return json.loads((lab[1]/"manifest.json").read_text())


def _restore(lab, anchor, slot, bucket, at, clone=None):
    _, vault, key, signing = lab
    target = clone or vault.parent/"lot08_3_b_lab_restored_rotation.sqlite"
    return rotation.restore_queue_vault_clone_lab(
        vault, target, backup_key=key, manifest_key=signing,
        trusted_anchor=anchor, slot=slot, bucket=bucket, now=at,
    )


def _sql(path, sql):
    with sqlite3.connect(path) as db:
        return db.execute(sql).fetchall()


def test_real_7_daily_4_weekly_calendar_rotation_and_latest_clone(lab):
    anchor = None
    first = None
    for day in range(43):
        stamp = NOW+timedelta(days=day)
        result = _rotate(lab, stamp, anchor)
        anchor = result.anchor
        if first is None:
            first = anchor
        assert result.generation == day+1
        assert 1 <= result.daily <= 7
        assert 1 <= result.weekly <= 4
        assert result.created in (1, 2)
    assert result.daily == 7
    assert result.weekly == 4
    entries = _manifest(lab)["payload"]["entries"]
    assert len(entries) == 11
    assert len(list(lab[1].glob("*.fernet"))) == 11
    assert {e["bucket"] for e in entries if e["slot"]=="daily"} == {
        (NOW+timedelta(days=x)).strftime("%Y-%m-%d")
        for x in range(36,43)
    }
    # The manifest, not just the file names, is part of the trust contract.
    assert _manifest(lab)["mac"] == anchor
    assert first != anchor
    _restore(lab,anchor,"daily",(NOW+timedelta(days=42)).strftime("%Y-%m-%d"),
             NOW+timedelta(days=42))
    clone = lab[1].parent/"lot08_3_b_lab_restored_rotation.sqlite"
    assert _sql(clone,"SELECT id FROM queue_tenants ORDER BY id") == [("T1",),("T2",)]
    assert _sql(clone,"SELECT actor_ref FROM queue_event_log") == [("OP_SYNTH",)]
    assert _sql(lab[0],"SELECT count(*) FROM queue_visits") == [(2,)]


def test_stale_anchor_refuses_restore_and_new_rotation(lab):
    first = _rotate(lab, NOW)
    second = _rotate(lab, NOW+timedelta(days=1), first.anchor)
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_MISMATCH"):
        _restore(lab,first.anchor,"daily",NOW.strftime("%Y-%m-%d"),NOW+timedelta(days=1))
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_MISMATCH"):
        _rotate(lab,NOW+timedelta(days=2),first.anchor)
    assert _manifest(lab)["mac"] == second.anchor


def test_restoring_older_manifest_with_current_anchor_is_refused(lab):
    first = _rotate(lab, NOW)
    old_bytes = (lab[1]/"manifest.json").read_bytes()
    newer = _rotate(lab, NOW+timedelta(days=1),first.anchor)
    (lab[1]/"manifest.json").write_bytes(old_bytes)
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_MISMATCH"):
        _restore(lab,newer.anchor,"daily",NOW.strftime("%Y-%m-%d"),
                 NOW+timedelta(days=1))
    assert not list(lab[1].parent.glob("lot08_3_b_lab_restored_rotation.sqlite"))


def test_catalog_tamper_and_ciphertext_change_fail_closed(lab):
    first = _rotate(lab,NOW)
    manifest = _manifest(lab)
    manifest["payload"]["generation"] = 999
    (lab[1]/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_MISMATCH"):
        _rotate(lab,NOW+timedelta(days=1),first.anchor)
    # Separate fixture for real ciphertext modification (catalog still authentic).
    _, vault, key, signer = lab
    manifest["payload"]["generation"] = 1
    (vault/"manifest.json").write_text(json.dumps(manifest))
    assert _manifest(lab)["mac"] == first.anchor
    archive = vault / manifest["payload"]["entries"][0]["name"]
    data = bytearray(archive.read_bytes())
    data[-3] ^= 1
    archive.write_bytes(data)
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ARCHIVE_TAMPERED"):
        rotation.restore_queue_vault_clone_lab(
            vault, vault.parent/"lot08_3_b_lab_restored_tamper.sqlite",
            backup_key=key, manifest_key=signer, trusted_anchor=first.anchor,
            slot="daily",bucket=NOW.strftime("%Y-%m-%d"),now=NOW,
        )


def test_wrong_keys_refused_no_clone(lab):
    first = _rotate(lab,NOW)
    _,vault,key,manifest_key=lab
    clone=vault.parent/"lot08_3_b_lab_restored_wrong_key.sqlite"
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_MISMATCH"):
        rotation.restore_queue_vault_clone_lab(
            vault,clone,backup_key=key,manifest_key=os.urandom(32),
            trusted_anchor=first.anchor,slot="daily",
            bucket=NOW.strftime("%Y-%m-%d"),now=NOW,
        )
    with pytest.raises(RestoreCloneLabError,match="LAB_ARCHIVE_AUTHENTICATION_FAILED"):
        rotation.restore_queue_vault_clone_lab(
            vault,clone,backup_key=Fernet.generate_key(),manifest_key=manifest_key,
            trusted_anchor=first.anchor,slot="daily",
            bucket=NOW.strftime("%Y-%m-%d"),now=NOW,
        )
    assert not clone.exists()


def test_empty_rotation_unsupported_vault_path_and_lab_marker_fail_closed(lab,tmp_path):
    source,vault,key,manifest_key=lab
    wrong=tmp_path/"real_backup_volume"
    wrong.mkdir()
    with pytest.raises(RestoreCloneLabError,match="ROTATION_LAB_VAULT_REQUIRED"):
        rotation.rotate_queue_vault_lab(
            source,wrong,backup_key=key,manifest_key=manifest_key,
            trusted_anchor=None,now=NOW,
        )
    ordinary=tmp_path/"cabinet.sqlite"
    ordinary.write_bytes(source.read_bytes())
    with pytest.raises(RestoreCloneLabError,match="SYNTHETIC_LAB_FILE_REQUIRED"):
        rotation.rotate_queue_vault_lab(
            ordinary,vault,backup_key=key,manifest_key=manifest_key,
            trusted_anchor=None,now=NOW,
        )
    with sqlite3.connect(source) as conn:
        conn.execute("PRAGMA application_id=0")
    with pytest.raises(RestoreCloneLabError,match="SYNTHETIC_LAB_MARKER_REQUIRED"):
        _rotate(lab,NOW)
    assert not (vault/"manifest.json").exists()
    assert not list(vault.glob("*.fernet"))


def test_duplicate_daily_is_fail_closed_and_preserves_catalog(lab):
    first=_rotate(lab,NOW)
    prior=(lab[1]/"manifest.json").read_bytes()
    prior_archives={p.name:p.read_bytes() for p in lab[1].glob("*.fernet")}
    with pytest.raises(RestoreCloneLabError,match="ROTATION_DAILY_ALREADY_PRESENT"):
        _rotate(lab,NOW,first.anchor)
    assert (lab[1]/"manifest.json").read_bytes()==prior
    assert {p.name:p.read_bytes() for p in lab[1].glob("*.fernet")} == prior_archives


def test_failure_before_catalog_publish_rolls_back_new_files(lab,monkeypatch):
    def failure():
        raise RuntimeError("LAB_INJECTED_ROTATION_CRASH")
    monkeypatch.setattr(rotation,"_before_catalog_publish_lab",failure)
    with pytest.raises(RuntimeError,match="LAB_INJECTED_ROTATION_CRASH"):
        _rotate(lab,NOW)
    assert not (lab[1]/"manifest.json").exists()
    assert not list(lab[1].glob("*.fernet"))
    assert not list(lab[1].glob("*.tmp"))
    monkeypatch.undo()
    assert _rotate(lab,NOW).generation == 1


def test_skipped_calendar_days_do_not_keep_stale_backups(lab):
    first=_rotate(lab,NOW)
    second=_rotate(lab,NOW+timedelta(days=44),first.anchor)
    assert second.daily==1
    assert second.weekly==1
    assert second.removed==2
    assert len(list(lab[1].glob("*.fernet")))==2


def test_iso_week_year_boundary_does_not_duplicate_weekly(lab):
    dec=datetime(2030,12,31,12,tzinfo=timezone.utc)
    jan=datetime(2031,1,1,12,tzinfo=timezone.utc)
    assert dec.isocalendar()[:2] == jan.isocalendar()[:2]
    first=_rotate(lab,dec)
    assert first.weekly==1 and first.created==2
    second=_rotate(lab,jan,first.anchor)
    assert second.weekly==1 and second.daily==2 and second.created==1


def test_old_archive_cannot_resurrect_purged_closed_visit(lab):
    src,vault,_,_=lab
    with sqlite3.connect(src) as db:
        closed=(NOW-timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S.%f")
        db.execute(
            "UPDATE queue_visits SET status='DONE', closed_at_utc=? WHERE id='VISIT_T1'",
            (closed,),
        )
    first=_rotate(lab,NOW)
    later=NOW+timedelta(days=29)
    clone=vault.parent/"lot08_3_b_lab_restored_overdue.sqlite"
    with pytest.raises(RestoreCloneLabError,match="RESTORE_OVERDUE_VISIT_DENIED"):
        _restore(lab,first.anchor,"daily",NOW.strftime("%Y-%m-%d"),later,clone=clone)
    assert not clone.exists()
    assert retain_closed_visits_lab(src,"T1",now=later,execute=True).eligible_visits==1
    second=_rotate(lab,later,first.anchor)
    assert second.daily==1
    assert second.weekly==1
    assert _sql(src,"SELECT id FROM queue_visits")==[("VISIT_T2",)]
    _restore(lab,second.anchor,"daily",later.strftime("%Y-%m-%d"),later,clone=clone)
    assert _sql(clone,"SELECT id FROM queue_visits")==[("VISIT_T2",)]
    assert _sql(clone,"SELECT id FROM queue_event_log")==[("EVENT_FAKE",)]


def test_undeclared_archive_and_clock_regression_refused(lab):
    first=_rotate(lab,NOW)
    orphan=lab[1]/"mystery.fernet"
    orphan.write_bytes(b"untrusted")
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ORPHAN_OR_MISSING_ARCHIVE"):
        _rotate(lab,NOW+timedelta(days=1),first.anchor)
    orphan.unlink()
    with pytest.raises(RestoreCloneLabError,match="ROTATION_MANIFEST_INVALID"):
        _rotate(lab,NOW-timedelta(days=1),first.anchor)
    assert _manifest(lab)["mac"]==first.anchor

