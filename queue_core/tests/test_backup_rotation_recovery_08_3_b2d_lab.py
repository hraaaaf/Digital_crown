"""LOT08.3-B2-D real SQLite/Fernet recovery FUE; no real patient/cabinet data."""
from datetime import datetime, timedelta, timezone
import json
import os
import sqlite3

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import QueueTenant, QueueLine, QueueVisitRecord
from queue_core.service import backup_rotation_08_3_b2c_lab as rotation
from queue_core.service import backup_rotation_recovery_08_3_b2d_lab as recovery
from queue_core.service.retention_lab_08_3_b import SYNTHETIC_LAB_APPLICATION_ID
from queue_core.service.backup_restore_clone_08_3_b2_lab import RestoreCloneLabError

NOW = datetime(2030,4,1,12,tzinfo=timezone.utc)


@pytest.fixture
def lab(tmp_path):
    source=tmp_path/"lot08_3_b_lab_queue_recovery.sqlite"
    vault=tmp_path/"lot08_3_b_lab_vault_recovery"
    vault.mkdir()
    engine=create_engine(f"sqlite+pysqlite:///{source}")
    QueueBase.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(QueueTenant(id="T1",timezone_name="Africa/Casablanca",created_at_utc=NOW))
        session.flush()
        session.add(QueueLine(id="Q1",tenant_id="T1",queue_key="Q1",is_active=True))
        session.flush()
        session.add(QueueVisitRecord(
            id="VISIT_TEST",tenant_id="T1",queue_id="Q1",
            visit_kind="WALK_IN",status="WAITING",version=1,
            scheduled_at_utc=None,queue_sequence=1,
            arrival_confirmed_at_utc=NOW-timedelta(hours=1),
            waiting_since_utc=NOW-timedelta(hours=1),
        ))
        session.commit()
    engine.dispose()
    with sqlite3.connect(source) as db:
        db.execute(f"PRAGMA application_id={SYNTHETIC_LAB_APPLICATION_ID}")
    return source,vault,Fernet.generate_key(),os.urandom(32)


def _rotate(lab, time, anchor=None):
    source,vault,bk,mk=lab
    return rotation.rotate_queue_vault_lab(
        source,vault,backup_key=bk,manifest_key=mk,
        trusted_anchor=anchor,now=time,
    )


def _recover(lab, anchor, time):
    _,vault,bk,mk=lab
    return recovery.recover_queue_vault_rotation_lab(
        vault,backup_key=bk,manifest_key=mk,trusted_anchor=anchor,now=time,
    )


def _restore(lab,anchor,time,clone_name="lot08_3_b_lab_restored_recovered.sqlite"):
    source,vault,bk,mk=lab
    dest=vault.parent/clone_name
    result=rotation.restore_queue_vault_clone_lab(
        vault,dest,backup_key=bk,manifest_key=mk,
        trusted_anchor=anchor,slot="daily",
        bucket=time.strftime("%Y-%m-%d"),now=time,
    )
    return result,dest


def _files(lab):
    return {p.name:p.read_bytes() for p in lab[1].glob("*.fernet")}


def _journal(lab):
    return lab[1]/rotation._JOURNAL_NAME


def _crash(monkeypatch, point):
    def fail():
        raise RuntimeError("INJECTED_CRASH")
    monkeypatch.setattr(rotation,point,fail)


def test_pre_publish_fault_still_rolls_back_without_journal(lab,monkeypatch):
    _crash(monkeypatch,"_before_catalog_publish_lab")
    with pytest.raises(RuntimeError,match="INJECTED_CRASH"):
        _rotate(lab,NOW)
    assert not _journal(lab).exists()
    assert not (lab[1]/"manifest.json").exists()
    assert _files(lab)=={}
    monkeypatch.undo()
    clean=_rotate(lab,NOW)
    assert clean.generation==1


def test_signed_journal_before_first_manifest_can_roll_back(lab,monkeypatch):
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError,match="INJECTED_CRASH"):
        _rotate(lab,NOW)
    assert _journal(lab).exists()
    assert not (lab[1]/"manifest.json").exists()
    assert len(_files(lab))==2
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_REQUIRED"):
        _rotate(lab,NOW)
    result=_recover(lab,None,NOW)
    assert result.phase=="rolled_back" and result.generation==0
    assert result.trusted_anchor is None and result.removed==2
    assert _files(lab)=={} and not _journal(lab).exists()
    monkeypatch.undo()
    fresh=_rotate(lab,NOW)
    _,clone=_restore(lab,fresh.anchor,NOW)
    assert clone.is_file()


def test_signed_journal_before_manifest_on_existing_vault_retains_prior(lab,monkeypatch):
    first=_rotate(lab,NOW)
    snapshot=_files(lab)
    prior_manifest=(lab[1]/"manifest.json").read_bytes()
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError,match="INJECTED_CRASH"):
        _rotate(lab,NOW+timedelta(days=1),first.anchor)
    assert len(_files(lab))==len(snapshot)+1
    result=_recover(lab,first.anchor,NOW+timedelta(days=1))
    assert result.phase=="rolled_back" and result.trusted_anchor==first.anchor
    assert _files(lab)==snapshot
    assert (lab[1]/"manifest.json").read_bytes()==prior_manifest
    assert not _journal(lab).exists()


def test_after_first_manifest_commit_fast_forwards_from_external_old_anchor(lab,monkeypatch):
    _crash(monkeypatch,"_after_manifest_before_retire_lab")
    with pytest.raises(RuntimeError,match="INJECTED_CRASH"):
        _rotate(lab,NOW)
    assert _journal(lab).exists()
    assert (lab[1]/"manifest.json").exists()
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_REQUIRED"):
        _restore(lab,None,NOW)
    status=_recover(lab,None,NOW)
    assert status.phase=="committed" and status.generation==1
    assert status.trusted_anchor is not None and status.removed==0
    assert not _journal(lab).exists()
    _,clone=_restore(lab,status.trusted_anchor,NOW)
    with sqlite3.connect(clone) as db:
        assert db.execute("SELECT id FROM queue_visits").fetchall()==[("VISIT_TEST",)]


def test_post_manifest_crash_with_expired_retirement_is_reconciled(lab,monkeypatch):
    anchor=None
    for day in range(7):
        anchor=_rotate(lab,NOW+timedelta(days=day),anchor).anchor
    before=_files(lab)
    _crash(monkeypatch,"_after_manifest_before_retire_lab")
    at=NOW+timedelta(days=7)
    with pytest.raises(RuntimeError,match="INJECTED_CRASH"):
        _rotate(lab,at,anchor)
    journal=json.loads(_journal(lab).read_text())
    assert len(_files(lab))==len(before)+len(journal["plan"]["created"])
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_REQUIRED"):
        _rotate(lab,at+timedelta(days=1),anchor)
    status=_recover(lab,anchor,at)
    assert status.phase=="committed" and status.generation==8
    assert status.removed==1
    assert status.trusted_anchor!=anchor and not _journal(lab).exists()
    assert len(_files(lab))==len(before)+len(journal["plan"]["created"])-1
    monkeypatch.undo()
    later=_rotate(lab,at+timedelta(days=1),status.trusted_anchor)
    assert later.generation==9


def test_crash_after_one_retirement_replays_only_remaining_signed_file(lab,monkeypatch):
    first=_rotate(lab,NOW)
    # Both first daily and weekly expired. Two retirement entries.
    at=NOW+timedelta(days=44)
    _crash(monkeypatch,"_after_each_retire_lab")
    with pytest.raises(RuntimeError,match="INJECTED_CRASH"):
        _rotate(lab,at,first.anchor)
    journal=json.loads(_journal(lab).read_text())
    retired=journal["plan"]["retired"]
    assert len(retired)==2
    assert sum((lab[1]/e["name"]).exists() for e in retired)==1
    status=_recover(lab,first.anchor,at)
    assert status.phase=="committed" and status.generation==2
    assert status.removed==1
    assert len(_files(lab))==2
    assert not _journal(lab).exists()
    _,clone=_restore(lab,status.trusted_anchor,at)
    assert clone.is_file()


def test_wrong_external_anchor_does_not_mutate_journal_or_ciphertext(lab,monkeypatch):
    first=_rotate(lab,NOW)
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError):
        _rotate(lab,NOW+timedelta(days=1),first.anchor)
    before=_files(lab)
    journal=_journal(lab).read_bytes()
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_ANCHOR_DENIED"):
        _recover(lab,"0"*64,NOW+timedelta(days=1))
    assert _files(lab)==before and _journal(lab).read_bytes()==journal


def test_journal_tamper_refuses_without_deletion(lab,monkeypatch):
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError):
        _rotate(lab,NOW)
    before=_files(lab)
    j=json.loads(_journal(lab).read_text())
    j["plan"]["prior_generation"]=99
    _journal(lab).write_text(json.dumps(j))
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_SIGNATURE_DENIED"):
        _recover(lab,None,NOW)
    assert _files(lab)==before


def test_unknown_orphan_never_silently_deleted(lab,monkeypatch):
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError):
        _rotate(lab,NOW)
    other=lab[1]/"lot08_3_b_lab_backup_daily_20300401_deadbeefdeadbeefdeadbeef.fernet"
    other.write_bytes(b"UNKNOWN")
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_REQUIRED|ROTATION_ORPHAN_OR_MISSING_ARCHIVE"):
        _recover(lab,None,NOW)
    assert other.exists()


def test_signed_archive_tamper_refused_before_cleanup(lab,monkeypatch):
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError):
        _rotate(lab,NOW)
    one=next(iter(lab[1].glob("*.fernet")))
    one.write_bytes(one.read_bytes()+b"TAMPER")
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_ARCHIVE_TAMPERED"):
        _recover(lab,None,NOW)
    assert one.exists() and _journal(lab).exists()


def test_partial_pre_publish_rollback_can_resume_from_signed_journal(lab,monkeypatch):
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError):
        _rotate(lab,NOW)
    one=next(iter(lab[1].glob("*.fernet")))
    one.unlink()  # emulate prior idempotent recovery interrupted after removal
    result=_recover(lab,None,NOW)
    assert result.phase=="rolled_back" and result.removed==1
    assert not _journal(lab).exists() and _files(lab)=={}


def test_wrong_manifest_key_and_wrong_backup_key_fail_closed(lab,monkeypatch):
    first=_rotate(lab,NOW)
    _crash(monkeypatch,"_after_manifest_before_retire_lab")
    with pytest.raises(RuntimeError):
        _rotate(lab,NOW+timedelta(days=1),first.anchor)
    saved=_files(lab)
    _,vault,bk,mk=lab
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_SIGNATURE_DENIED"):
        recovery.recover_queue_vault_rotation_lab(
            vault,backup_key=bk,manifest_key=os.urandom(32),
            trusted_anchor=first.anchor,now=NOW+timedelta(days=1))
    with pytest.raises(RestoreCloneLabError,match="ROTATION_BACKUP_KEY_MISMATCH"):
        recovery.recover_queue_vault_rotation_lab(
            vault,backup_key=Fernet.generate_key(),manifest_key=mk,
            trusted_anchor=first.anchor,now=NOW+timedelta(days=1))
    assert _files(lab)==saved and _journal(lab).exists()


def test_unexpected_manifest_generation_refused_even_if_journal_valid(lab,monkeypatch):
    first=_rotate(lab,NOW)
    _crash(monkeypatch,"_after_journal_before_manifest_lab")
    with pytest.raises(RuntimeError):
        _rotate(lab,NOW+timedelta(days=1),first.anchor)
    old=(lab[1]/"manifest.json")
    document=json.loads(old.read_text())
    document["payload"]["generation"]=500
    old.write_text(json.dumps(document))
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_MANIFEST_MISMATCH|ROTATION_ANCHOR_MISMATCH"):
        _recover(lab,first.anchor,NOW+timedelta(days=1))
    assert _journal(lab).exists()


def test_no_journal_recovery_requires_journal(lab):
    normal=_rotate(lab,NOW)
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_JOURNAL_REQUIRED"):
        _recover(lab,normal.anchor,NOW)
    assert len(_files(lab))==2


def test_recovery_only_accepts_lab_vault_not_arbitrary_folder(lab,tmp_path):
    forbidden=tmp_path/"actual_cabinet_backups"
    forbidden.mkdir()
    with pytest.raises(RestoreCloneLabError,match="ROTATION_LAB_VAULT_REQUIRED"):
        recovery.recover_queue_vault_rotation_lab(
            forbidden,backup_key=lab[2],manifest_key=lab[3],
            trusted_anchor=None,now=NOW)
