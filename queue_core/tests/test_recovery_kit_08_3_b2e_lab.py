"""LOT08.3-B2-E: real synthetic SQLite + separately witnessed encrypted kit FUE.

Tests never use cabinet files, credentials, patient media, or real passwords.
"""
from datetime import datetime, timedelta, timezone
from base64 import b64decode, b64encode
from hashlib import sha256
import json
import os
import shutil
import sqlite3

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from queue_core.persistence import QueueBase
from queue_core.persistence.models import QueueTenant, QueueLine, QueueVisitRecord
from queue_core.service import backup_rotation_08_3_b2c_lab as rotation
from queue_core.service import recovery_kit_08_3_b2e_lab as kit
from queue_core.service.backup_restore_clone_08_3_b2_lab import RestoreCloneLabError
from queue_core.service.retention_lab_08_3_b import (
    SYNTHETIC_LAB_APPLICATION_ID, retain_closed_visits_lab,
)
from queue_core.service.retention_qr_08_3_b2_lab import retain_consumed_qr_ledger_lab
from queue_core.service.kiosk_qr_lab import _SCHEMA as QR_SCHEMA

NOW = datetime(2030, 4, 1, 12, tzinfo=timezone.utc)
PASSPHRASE = b"LAB_ONLY_RANDOM_LONG_PASSPHRASE_32_BYTES_FICTITIOUS"
NEW_PASSPHRASE = b"OTHER_LAB_ONLY_LONG_ENTROPIC_PHRASE_42_CHARS"


@pytest.fixture
def lab(tmp_path):
    source = tmp_path / "lot08_3_b_lab_queue_kit.sqlite"
    vault = tmp_path / "lot08_3_b_lab_vault_primary_kit"
    separate = tmp_path / "lot08_3_b_lab_kit_secondary"
    vault.mkdir()
    separate.mkdir()
    engine = create_engine(f"sqlite+pysqlite:///{source}")
    QueueBase.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(QueueTenant(
            id="T1", timezone_name="Africa/Casablanca", created_at_utc=NOW,
        ))
        session.flush()
        session.add(QueueLine(id="Q1", tenant_id="T1", queue_key="WAIT", is_active=True))
        session.flush()
        session.add_all([
            QueueVisitRecord(
                id="WAIT_SYNTH", tenant_id="T1", queue_id="Q1",
                visit_kind="WALK_IN", status="WAITING", version=1,
                scheduled_at_utc=None, queue_sequence=1,
                arrival_confirmed_at_utc=NOW-timedelta(hours=1),
                waiting_since_utc=NOW-timedelta(hours=1),
            ),
            QueueVisitRecord(
                id="DONE_SYNTH", tenant_id="T1", queue_id="Q1",
                visit_kind="APPOINTMENT", status="DONE", version=2,
                scheduled_at_utc=NOW-timedelta(days=26), queue_sequence=2,
                arrival_confirmed_at_utc=NOW-timedelta(days=25),
                waiting_since_utc=NOW-timedelta(days=25),
                closed_at_utc=NOW-timedelta(days=25),
            ),
        ])
        session.commit()
    engine.dispose()
    # sqlite3.Connection used as a context manager commits but does NOT
    # close the handle. Windows correctly refuses unlinking an open DB.
    conn = sqlite3.connect(source)
    try:
        conn.execute(f"PRAGMA application_id={SYNTHETIC_LAB_APPLICATION_ID}")
        conn.commit()
    finally:
        conn.close()
    return source, vault, separate, Fernet.generate_key(), os.urandom(32)


def _rotate(lab, at=NOW, anchor=None):
    source, vault, _, key, sign = lab
    return rotation.rotate_queue_vault_lab(
        source, vault, backup_key=key, manifest_key=sign,
        trusted_anchor=anchor, now=at,
    )


def _seal(lab, anchor, at=NOW, phrase=PASSPHRASE, prior=None, old_phrase=None):
    _, vault, directory, key, sign = lab
    return kit.seal_queue_recovery_kit_lab(
        vault, directory, backup_key=key, manifest_key=sign,
        trusted_anchor=anchor, passphrase=phrase, now=at,
        previous_witness=prior, previous_passphrase=old_phrase,
    )


def _restore(lab, fingerprint, at=NOW, phrase=PASSPHRASE, *,
             slot="daily", bucket=None, destination=None):
    source, vault, directory, _, _ = lab
    target = destination or vault.parent/"lot08_3_b_lab_restored_from_kit.sqlite"
    digest = kit.restore_queue_clone_from_kit_lab(
        vault, directory, target, passphrase=phrase,
        expected_witness=fingerprint, slot=slot,
        bucket=bucket or at.strftime("%Y-%m-%d"), now=at,
    )
    return digest, target


def _sealed_path(lab):
    return lab[2]/"sealed-recovery-kit.aead.json"


def _rows(path, sql):
    with sqlite3.connect(path) as db:
        return db.execute(sql).fetchall()


def test_separate_encrypted_kit_contains_no_plaintext_secrets_and_restores(lab):
    rotated = _rotate(lab)
    receipt = _seal(lab, rotated.anchor)
    encoded = _sealed_path(lab).read_bytes()
    assert sha256(encoded).hexdigest() == receipt.witness_fingerprint
    assert receipt.generation == rotated.generation == 1
    assert b"SQLite format 3" not in encoded
    for secret in (lab[3], lab[4], rotated.anchor.encode(), PASSPHRASE):
        assert secret not in encoded
    digest, clone = _restore(lab,receipt.witness_fingerprint)
    assert len(digest) == 64
    assert _rows(clone, "SELECT id FROM queue_visits ORDER BY id") == [
        ("DONE_SYNTH",), ("WAIT_SYNTH",)
    ]
    assert _rows(lab[0],"SELECT count(*) FROM queue_visits") == [(2,)]


def test_simulated_lost_workstation_independent_folders_restore_new_clone(lab,tmp_path):
    rotated = _rotate(lab)
    receipt = _seal(lab, rotated.anchor)
    vault2 = tmp_path / "lot08_3_b_lab_vault_after_device_loss"
    kit2 = tmp_path / "lot08_3_b_lab_kit_after_device_loss"
    shutil.copytree(lab[1],vault2)
    shutil.copytree(lab[2],kit2)
    lab[0].unlink()
    # The original fake source is unavailable; only encrypted vault+kit survive.
    target = tmp_path/"lot08_3_b_lab_restored_new_machine.sqlite"
    digest=kit.restore_queue_clone_from_kit_lab(
        vault2,kit2,target,passphrase=PASSPHRASE,
        expected_witness=receipt.witness_fingerprint,
        slot="weekly",bucket="2030-W14",now=NOW,
    )
    assert len(digest)==64 and target.is_file()
    assert _rows(target,"PRAGMA application_id")==[(SYNTHETIC_LAB_APPLICATION_ID,)]
    assert _rows(target,"SELECT id FROM queue_visits ORDER BY id")==[
        ("DONE_SYNTH",),("WAIT_SYNTH",)
    ]


def test_wrong_passphrase_fails_without_clone(lab):
    receipt=_seal(lab,_rotate(lab).anchor)
    with pytest.raises(RestoreCloneLabError,match="KIT_AUTHENTICATION_FAILED"):
        _restore(lab,receipt.witness_fingerprint,phrase=NEW_PASSPHRASE)
    assert not (lab[1].parent/"lot08_3_b_lab_restored_from_kit.sqlite").exists()


def test_missing_or_wrong_external_witness_fails_without_clone(lab):
    receipt=_seal(lab,_rotate(lab).anchor)
    for witness in ("0"*64,"", "not-a-sha"):
        with pytest.raises(RestoreCloneLabError,match="KIT_EXTERNAL_WITNESS"):
            _restore(lab,witness)
    assert sha256(_sealed_path(lab).read_bytes()).hexdigest()==receipt.witness_fingerprint


def test_tampered_kit_refused_even_with_original_passphrase(lab):
    receipt=_seal(lab,_rotate(lab).anchor)
    encrypted=bytearray(_sealed_path(lab).read_bytes())
    encrypted[-20]^=1
    _sealed_path(lab).write_bytes(encrypted)
    with pytest.raises(RestoreCloneLabError,match="KIT_EXTERNAL_WITNESS_MISMATCH"):
        _restore(lab,receipt.witness_fingerprint)
    assert not list(lab[1].parent.glob("lot08_3_b_lab_restored_from_kit.sqlite"))


def test_kit_clone_refuses_rollback_to_old_vault_manifest(lab,tmp_path):
    first=_rotate(lab)
    original=_seal(lab,first.anchor)
    vault_copy=tmp_path/"lot08_3_b_lab_vault_stale_copy"
    shutil.copytree(lab[1],vault_copy)
    second=_rotate(lab,NOW+timedelta(days=1),first.anchor)
    updated=_seal(
        lab,second.anchor,NOW+timedelta(days=1),phrase=NEW_PASSPHRASE,
        prior=original.witness_fingerprint,old_phrase=PASSPHRASE,
    )
    target=tmp_path/"lot08_3_b_lab_restored_stale_vault.sqlite"
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_MISMATCH"):
        kit.restore_queue_clone_from_kit_lab(
            vault_copy,lab[2],target,passphrase=NEW_PASSPHRASE,
            expected_witness=updated.witness_fingerprint,
            slot="daily",bucket=NOW.strftime("%Y-%m-%d"),
            now=NOW+timedelta(days=1),
        )
    assert not target.exists()


def test_stale_kit_after_new_rotation_is_refused(lab):
    first=_rotate(lab)
    receipt=_seal(lab,first.anchor)
    _rotate(lab,NOW+timedelta(days=1),first.anchor)
    with pytest.raises(RestoreCloneLabError,match="ROTATION_ANCHOR_MISMATCH"):
        _restore(lab,receipt.witness_fingerprint,NOW+timedelta(days=1))
    assert not (lab[1].parent/"lot08_3_b_lab_restored_from_kit.sqlite").exists()


def test_guarded_kit_update_and_new_passphrase_restore(lab):
    first=_rotate(lab)
    receipt1=_seal(lab,first.anchor)
    second=_rotate(lab,NOW+timedelta(days=1),first.anchor)
    receipt2=_seal(
        lab,second.anchor,NOW+timedelta(days=1),phrase=NEW_PASSPHRASE,
        prior=receipt1.witness_fingerprint,old_phrase=PASSPHRASE,
    )
    assert receipt2.generation==2
    assert receipt2.witness_fingerprint!=receipt1.witness_fingerprint
    with pytest.raises(RestoreCloneLabError,match="KIT_EXTERNAL_WITNESS_MISMATCH"):
        _restore(lab,receipt1.witness_fingerprint,NOW+timedelta(days=1),
                 phrase=NEW_PASSPHRASE)
    _,clone=_restore(lab,receipt2.witness_fingerprint,
                     NOW+timedelta(days=1),phrase=NEW_PASSPHRASE)
    assert _rows(clone,"SELECT id FROM queue_tenants")==[("T1",)]


def test_update_wrong_old_witness_and_passphrase_cannot_change_kit(lab):
    first=_rotate(lab)
    receipt1=_seal(lab,first.anchor)
    second=_rotate(lab,NOW+timedelta(days=1),first.anchor)
    before=_sealed_path(lab).read_bytes()
    with pytest.raises(RestoreCloneLabError,match="KIT_EXTERNAL_WITNESS_MISMATCH"):
        _seal(lab,second.anchor,NOW+timedelta(days=1),
              prior="0"*64,old_phrase=PASSPHRASE)
    with pytest.raises(RestoreCloneLabError,match="KIT_AUTHENTICATION_FAILED"):
        _seal(lab,second.anchor,NOW+timedelta(days=1),
              prior=receipt1.witness_fingerprint,old_phrase=NEW_PASSPHRASE)
    assert _sealed_path(lab).read_bytes()==before


def test_kit_reuse_without_new_generation_denied(lab):
    first=_rotate(lab)
    receipt=_seal(lab,first.anchor)
    before=_sealed_path(lab).read_bytes()
    with pytest.raises(RestoreCloneLabError,match="KIT_GENERATION_OR_KEY_INVALID"):
        _seal(lab,first.anchor,prior=receipt.witness_fingerprint,
              old_phrase=PASSPHRASE)
    assert _sealed_path(lab).read_bytes()==before


def test_injected_fault_before_kit_create_leaves_no_kit(lab,monkeypatch):
    first=_rotate(lab)
    def fail():
        raise RuntimeError("KIT_FAULT")
    monkeypatch.setattr(kit,"_before_kit_publish_lab",fail)
    with pytest.raises(RuntimeError,match="KIT_FAULT"):
        _seal(lab,first.anchor)
    assert not _sealed_path(lab).exists()
    assert not list(lab[2].glob("*.tmp"))
    monkeypatch.undo()
    receipt=_seal(lab,first.anchor)
    assert receipt.generation==1


def test_injected_fault_before_kit_update_preserves_previous_bytes(lab,monkeypatch):
    first=_rotate(lab)
    receipt=_seal(lab,first.anchor)
    original=_sealed_path(lab).read_bytes()
    second=_rotate(lab,NOW+timedelta(days=1),first.anchor)
    def fail():
        raise RuntimeError("KIT_UPDATE_FAULT")
    monkeypatch.setattr(kit,"_before_kit_publish_lab",fail)
    with pytest.raises(RuntimeError,match="KIT_UPDATE_FAULT"):
        _seal(lab,second.anchor,NOW+timedelta(days=1),
              prior=receipt.witness_fingerprint,old_phrase=PASSPHRASE)
    assert _sealed_path(lab).read_bytes()==original
    assert not list(lab[2].glob("*.tmp"))


def test_non_lab_kit_folder_and_nested_vault_rejected(lab,tmp_path):
    first=_rotate(lab)
    bad=tmp_path/"real_cabinet_key_escrow"
    bad.mkdir()
    for folder in (bad,lab[1]):
        with pytest.raises(RestoreCloneLabError,match="KIT_SYNTHETIC_FOLDER_REQUIRED"):
            kit.seal_queue_recovery_kit_lab(
                lab[1],folder,backup_key=lab[3],manifest_key=lab[4],
                trusted_anchor=first.anchor,passphrase=PASSPHRASE,now=NOW)
    assert not _sealed_path(lab).exists()


def test_wrong_backup_or_manifest_key_cannot_seal_valid_vault(lab):
    first=_rotate(lab)
    for bk,mk in ((Fernet.generate_key(),lab[4]),(lab[3],os.urandom(32))):
        with pytest.raises(RestoreCloneLabError,
                           match="ROTATION_BACKUP_KEY_MISMATCH|ROTATION_ANCHOR_MISMATCH"):
            kit.seal_queue_recovery_kit_lab(
                lab[1],lab[2],backup_key=bk,manifest_key=mk,
                trusted_anchor=first.anchor,passphrase=PASSPHRASE,now=NOW)
    assert not _sealed_path(lab).exists()


def test_unresolved_b2d_rotation_journal_fails_closed(lab,monkeypatch):
    first=_rotate(lab)
    receipt=_seal(lab,first.anchor)
    def fail():
        raise RuntimeError("INJECTED_B2D")
    monkeypatch.setattr(rotation,"_after_manifest_before_retire_lab",fail)
    with pytest.raises(RuntimeError,match="INJECTED_B2D"):
        _rotate(lab,NOW+timedelta(days=1),first.anchor)
    with pytest.raises(RestoreCloneLabError,match="ROTATION_RECOVERY_REQUIRED"):
        _restore(lab,receipt.witness_fingerprint,NOW+timedelta(days=1))


def test_outdated_weekly_from_kit_cannot_resurrect_purged_visit(lab):
    first=_rotate(lab)
    first_kit=_seal(lab,first.anchor)
    later=NOW+timedelta(days=8)
    assert retain_closed_visits_lab(lab[0],"T1",now=later,execute=True).eligible_visits==1
    second=_rotate(lab,later,first.anchor)
    updated=_seal(lab,second.anchor,later,
                  prior=first_kit.witness_fingerprint,old_phrase=PASSPHRASE)
    with pytest.raises(RestoreCloneLabError,match="RESTORE_OVERDUE_VISIT_DENIED"):
        _restore(lab,updated.witness_fingerprint,later,slot="weekly",bucket="2030-W14")
    assert not list(lab[1].parent.glob("lot08_3_b_lab_restored_from_kit.sqlite"))
    _,clone=_restore(lab,updated.witness_fingerprint,later)
    assert _rows(clone,"SELECT id FROM queue_visits")==[("WAIT_SYNTH",)]


def test_preexisting_clone_never_overwritten_by_kit_restore(lab):
    rotated=_rotate(lab)
    receipt=_seal(lab,rotated.anchor)
    target=lab[1].parent/"lot08_3_b_lab_restored_from_kit.sqlite"
    target.write_bytes(b"DO_NOT_TOUCH")
    with pytest.raises(RestoreCloneLabError,match="LAB_DESTINATION_REQUIRED"):
        _restore(lab,receipt.witness_fingerprint)
    assert target.read_bytes()==b"DO_NOT_TOUCH"


def test_weak_or_invalid_passphrase_and_missing_kit_refused(lab):
    first=_rotate(lab)
    with pytest.raises(RestoreCloneLabError,match="KIT_HIGH_ENTROPY_PASSPHRASE_REQUIRED"):
        _seal(lab,first.anchor,phrase=b"password")
    with pytest.raises(RestoreCloneLabError,match="KIT_STATE_INVALID"):
        _restore(lab,"0"*64)


def test_tampered_aead_ciphertext_cannot_be_authorized_by_new_sha_witness(lab):
    first=_rotate(lab)
    _seal(lab,first.anchor)
    doc=json.loads(_sealed_path(lab).read_text())
    ciphertext=bytearray(b64decode(doc["ciphertext"]))
    ciphertext[-1] ^= 1
    doc["ciphertext"]=b64encode(ciphertext).decode("ascii")
    _sealed_path(lab).write_text(json.dumps(doc))
    # Even if a wrong actor replaces the independent SHA witness, AEAD tag
    # validation still refuses decryption without the recovery passphrase.
    new_witness=sha256(_sealed_path(lab).read_bytes()).hexdigest()
    with pytest.raises(RestoreCloneLabError,match="KIT_AUTHENTICATION_FAILED"):
        _restore(lab,new_witness)
    assert not (lab[1].parent/"lot08_3_b_lab_restored_from_kit.sqlite").exists()


def test_old_weekly_kit_cannot_resurrect_expired_consumed_qr_receipt(lab):
    source,vault,directory,backup_key,manifest_key=lab
    epoch=int(NOW.timestamp())
    with sqlite3.connect(source) as db:
        # Keep the synthetic closed visit inside the 30-day window at +8d,
        # so this scenario probes the independent QR 7-day anti-resurrection.
        closed=(NOW-timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S.%f")
        db.execute("UPDATE queue_visits SET closed_at_utc=? WHERE id='DONE_SYNTH'",(closed,))
        db.executescript(QR_SCHEMA)
        db.execute(
            "INSERT INTO queue_presence_qr_lab "
            "(qr_digest,tenant_id,queue_id,visit_id,expires_epoch,consumed_epoch,"
            "consumed_device,request_digest,result_version,result_sequence) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("QR_FAKE_B2E", "T1", "Q1", "WAIT_SYNTH",
             epoch-3600,epoch-86400,"DEV_FAKE","REQ_FAKE",1,1),
        )
    first=_rotate(lab)
    receipt=_seal(lab,first.anchor)
    later=NOW+timedelta(days=8)
    assert retain_consumed_qr_ledger_lab(
        source,"T1",now=later,execute=True,
    ).eligible_receipts==1
    second=_rotate(lab,later,first.anchor)
    updated=_seal(lab,second.anchor,later,
                  prior=receipt.witness_fingerprint,old_phrase=PASSPHRASE)
    with pytest.raises(RestoreCloneLabError,match="RESTORE_OVERDUE_QR_DENIED"):
        _restore(lab,updated.witness_fingerprint,later,
                 slot="weekly",bucket="2030-W14")
    assert not (vault.parent/"lot08_3_b_lab_restored_from_kit.sqlite").exists()
    _,clone=_restore(lab,updated.witness_fingerprint,later)
    assert _rows(clone,"SELECT count(*) FROM queue_presence_qr_lab")==[(0,)]


# LOT08.3-B2-F: independently witnessed immutable export, synthetic LAB only.
from queue_core.service import custody_handoff_08_3_b2f_lab as custody


def _custody(lab, tmp_path, at=NOW, *, previous=None, phrase=PASSPHRASE,
             old_witness=None):
    root = tmp_path / "lot08_3_b_lab_custody_external_probe"
    root.mkdir(exist_ok=True)
    if old_witness is None:
        anchor = _rotate(lab, at).anchor
        sealed = _seal(lab, anchor, at, phrase=phrase)
        witness = sealed.witness_fingerprint
    else:
        witness = old_witness
    return custody.prepare_custody_bundle_lab(
        lab[1], lab[2], root, passphrase=phrase, kit_witness=witness,
        now=at, previous_external_fingerprint=previous,
    )


def _custody_restore(receipt, tmp_path, *, external=None, phrase=PASSPHRASE,
                     at=NOW, bundle=None, target=None):
    target = target or tmp_path / "lot08_3_b_lab_restored_custody.sqlite"
    result = custody.restore_custody_bundle_lab(
        bundle or receipt.bundle, target,
        external_fingerprint=external if external is not None
        else receipt.external_fingerprint, passphrase=phrase,
        slot="daily", bucket=at.strftime("%Y-%m-%d"), now=at,
    )
    return result, target


def test_b2f_immutable_bundle_restores_after_deleting_original_lab_workspace(
        lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    assert receipt.generation == 1
    assert len(receipt.external_fingerprint) == 64
    assert receipt.bundle.is_dir()
    assert receipt.bundle.parent != lab[1] and receipt.bundle.parent != lab[2]
    raw = (receipt.bundle / "custody-descriptor.json").read_bytes()
    assert sha256(raw).hexdigest() == receipt.external_fingerprint
    assert PASSPHRASE not in raw
    assert lab[3] not in raw and lab[4] not in raw
    shutil.rmtree(lab[1])
    shutil.rmtree(lab[2])
    lab[0].unlink()
    digest, clone = _custody_restore(receipt, tmp_path)
    assert len(digest) == 64 and clone.is_file()
    assert _rows(clone, "PRAGMA application_id") == [
        (SYNTHETIC_LAB_APPLICATION_ID,)
    ]
    assert _rows(clone, "SELECT id FROM queue_visits ORDER BY id") == [
        ("DONE_SYNTH",), ("WAIT_SYNTH",)
    ]


def test_b2f_unacknowledged_export_rejected_without_external_digest(lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    target = tmp_path / "lot08_3_b_lab_restored_unacknowledged.sqlite"
    for invalid in ("", "0" * 64, "not-hex"):
        with pytest.raises(RestoreCloneLabError, match="CUSTODY_EXTERNAL_WITNESS"):
            custody.restore_custody_bundle_lab(
                receipt.bundle, target, external_fingerprint=invalid,
                passphrase=PASSPHRASE, slot="daily",
                bucket=NOW.strftime("%Y-%m-%d"), now=NOW,
            )
    assert not target.exists()


def test_b2f_wrong_passphrase_refused_without_clone(lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    with pytest.raises(RestoreCloneLabError, match="KIT_AUTHENTICATION_FAILED"):
        _custody_restore(receipt, tmp_path, phrase=NEW_PASSPHRASE)
    assert not (tmp_path / "lot08_3_b_lab_restored_custody.sqlite").exists()


@pytest.mark.parametrize("file_type", ["kit", "manifest", "archive"])
def test_b2f_copied_ciphertext_and_catalog_tampering_refused(
        lab, tmp_path, file_type):
    receipt = _custody(lab, tmp_path)
    vault = receipt.bundle / "lot08_3_b_lab_vault_handoff"
    kit_folder = receipt.bundle / "lot08_3_b_lab_kit_handoff"
    if file_type == "kit":
        target = kit_folder / "sealed-recovery-kit.aead.json"
    elif file_type == "manifest":
        target = vault / "manifest.json"
    else:
        target = next(vault.glob("*.fernet"))
    blob = bytearray(target.read_bytes())
    blob[-2] ^= 1
    target.write_bytes(blob)
    with pytest.raises(RestoreCloneLabError, match="CUSTODY_BUNDLE_TAMPERED"):
        _custody_restore(receipt, tmp_path)
    assert not (tmp_path / "lot08_3_b_lab_restored_custody.sqlite").exists()


def test_b2f_unknown_extra_file_blocks_restore(lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    (receipt.bundle / "lot08_3_b_lab_vault_handoff" / "evil.txt").write_text("X")
    with pytest.raises(RestoreCloneLabError, match="CUSTODY_BUNDLE_INVALID"):
        _custody_restore(receipt, tmp_path)
    assert not (tmp_path / "lot08_3_b_lab_restored_custody.sqlite").exists()


def test_b2f_stage_interrupt_keeps_no_published_bundle(
        lab, tmp_path, monkeypatch):
    first = _rotate(lab)
    sealed = _seal(lab, first.anchor)
    root = tmp_path / "lot08_3_b_lab_custody_fault"
    root.mkdir()
    def fail():
        raise RuntimeError("synthetic power interruption before publish")
    monkeypatch.setattr(custody, "_before_bundle_publish_lab", fail)
    with pytest.raises(RuntimeError, match="synthetic power interruption"):
        custody.prepare_custody_bundle_lab(
            lab[1], lab[2], root, passphrase=PASSPHRASE,
            kit_witness=sealed.witness_fingerprint, now=NOW,
        )
    assert list(root.iterdir()) == []


def test_b2f_pending_directory_cannot_be_restored(lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    pending = receipt.bundle.parent / ".lot08_3_b_lab_pending_orphan"
    shutil.copytree(receipt.bundle, pending)
    with pytest.raises(RestoreCloneLabError, match="CUSTODY_BUNDLE_INVALID"):
        _custody_restore(receipt, tmp_path, bundle=pending)
    assert not (tmp_path / "lot08_3_b_lab_restored_custody.sqlite").exists()


def test_b2f_previous_receipt_cannot_authorize_new_generation(
        lab, tmp_path):
    first = _rotate(lab)
    kit1 = _seal(lab, first.anchor)
    root = tmp_path / "lot08_3_b_lab_custody_generations"
    root.mkdir()
    receipt1 = custody.prepare_custody_bundle_lab(
        lab[1], lab[2], root, passphrase=PASSPHRASE,
        kit_witness=kit1.witness_fingerprint, now=NOW,
    )
    later = NOW + timedelta(days=1)
    second = _rotate(lab, later, first.anchor)
    kit2 = _seal(
        lab, second.anchor, later, phrase=NEW_PASSPHRASE,
        prior=kit1.witness_fingerprint, old_phrase=PASSPHRASE,
    )
    receipt2 = custody.prepare_custody_bundle_lab(
        lab[1], lab[2], root, passphrase=NEW_PASSPHRASE,
        kit_witness=kit2.witness_fingerprint, now=later,
        previous_external_fingerprint=receipt1.external_fingerprint,
    )
    assert receipt2.generation > receipt1.generation
    descriptor = json.loads(
        (receipt2.bundle / "custody-descriptor.json").read_bytes()
    )
    assert descriptor["predecessor"] == receipt1.external_fingerprint
    with pytest.raises(RestoreCloneLabError, match="CUSTODY_EXTERNAL_WITNESS_MISMATCH"):
        _custody_restore(
            receipt1, tmp_path, external=receipt2.external_fingerprint,
            at=later, phrase=PASSPHRASE,
        )
    assert not (tmp_path / "lot08_3_b_lab_restored_custody.sqlite").exists()
    _, target = _custody_restore(receipt2, tmp_path, at=later,
                                 phrase=NEW_PASSPHRASE)
    assert target.exists()


def test_b2f_missing_archive_refuses_restore(lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    vault = receipt.bundle / "lot08_3_b_lab_vault_handoff"
    next(vault.glob("*.fernet")).unlink()
    with pytest.raises(RestoreCloneLabError, match="CUSTODY_BUNDLE_INVALID"):
        _custody_restore(receipt, tmp_path)


def test_b2f_non_lab_root_and_nested_source_refused(lab, tmp_path):
    first = _rotate(lab)
    kit1 = _seal(lab, first.anchor)
    roots = [
        tmp_path / "bad-folder",
        lab[1] / "lot08_3_b_lab_custody_inside_vault",
    ]
    for root in roots:
        root.mkdir()
        with pytest.raises(RestoreCloneLabError, match="CUSTODY_SYNTHETIC_ROOT_REQUIRED"):
            custody.prepare_custody_bundle_lab(
                lab[1], lab[2], root, passphrase=PASSPHRASE,
                kit_witness=kit1.witness_fingerprint, now=NOW,
            )


def test_b2f_wrong_initial_kit_witness_refuses_export(lab, tmp_path):
    first = _rotate(lab)
    _seal(lab, first.anchor)
    root = tmp_path / "lot08_3_b_lab_custody_witness_reject"
    root.mkdir()
    with pytest.raises(RestoreCloneLabError, match="KIT_EXTERNAL_WITNESS_MISMATCH"):
        custody.prepare_custody_bundle_lab(
            lab[1], lab[2], root, passphrase=PASSPHRASE,
            kit_witness="0" * 64, now=NOW,
        )
    assert list(root.iterdir()) == []


def test_b2f_refuses_clone_inside_custody_bundle(lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    with pytest.raises(RestoreCloneLabError, match="CUSTODY_CLONE_INSIDE_BUNDLE_DENIED"):
        _custody_restore(
            receipt, tmp_path,
            target=receipt.bundle / "lot08_3_b_lab_restored_inside.sqlite",
        )


def test_b2f_late_rotation_without_resealed_kit_refused(
        lab, tmp_path):
    first = _rotate(lab)
    kit1 = _seal(lab, first.anchor)
    _rotate(lab, NOW + timedelta(days=1), first.anchor)
    root = tmp_path / "lot08_3_b_lab_custody_stale"
    root.mkdir()
    with pytest.raises(RestoreCloneLabError, match="ROTATION_ANCHOR_MISMATCH"):
        custody.prepare_custody_bundle_lab(
            lab[1], lab[2], root, passphrase=PASSPHRASE,
            kit_witness=kit1.witness_fingerprint, now=NOW + timedelta(days=1),
        )
    assert list(root.iterdir()) == []


def test_b2f_forged_descriptor_fingerprint_cannot_authenticate_ciphertext(
        lab, tmp_path):
    receipt = _custody(lab, tmp_path)
    kitpath = receipt.bundle / "lot08_3_b_lab_kit_handoff" / "sealed-recovery-kit.aead.json"
    blob = bytearray(kitpath.read_bytes())
    blob[-20] ^= 1
    kitpath.write_bytes(blob)
    descriptor = receipt.bundle / "custody-descriptor.json"
    parsed = json.loads(descriptor.read_bytes())
    parsed["kit_sha256"] = sha256(kitpath.read_bytes()).hexdigest()
    canonical = json.dumps(
        parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    descriptor.write_bytes(canonical)
    forged = sha256(canonical).hexdigest()
    with pytest.raises(RestoreCloneLabError, match="KIT_AUTHENTICATION_FAILED|KIT_INVALID"):
        _custody_restore(receipt, tmp_path, external=forged)
    assert not (tmp_path / "lot08_3_b_lab_restored_custody.sqlite").exists()
