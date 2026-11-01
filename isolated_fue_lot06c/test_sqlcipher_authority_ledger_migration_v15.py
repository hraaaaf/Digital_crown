"""Real unchained candidate Alembic DDL, real SQLCipher, synthetic fixture only."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlcipher3.dbapi2 import IntegrityError as CipherIntegrityError
from backend.services.imaging_clinical_asset_verifier_v15 import verify_device_capture_media_binding
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import bridge, _issue, _hash
from isolated_fue_lot06c.test_sqlcipher_clinical_asset_receipt_v15 import _root_engine

NAMES = [f"c05b03f_{x}" for x in ("devices","approvals","receipts","audit","outbox")]
MIGRATION = Path(__file__).resolve().parent / "migrations" / "c05b03f_authority_ledger_candidate.py"

def _module():
    spec = importlib.util.spec_from_file_location("c05b03f_candidate_module", MIGRATION)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.revision == "c05b03f_candidate" and mod.down_revision is None
    return mod

def _apply(conn, action):
    with Operations.context(MigrationContext.configure(conn)):
        getattr(_module(), action)()

def _present(conn):
    return {x[0] for x in conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}

def _seed(conn, claim, device_token):
    conn.exec_driver_sql(
        "INSERT INTO c05b03f_devices VALUES(?,?,?,?,?,?)",
        (claim.tenant, claim.device, claim.station, _hash(device_token), claim.generation, 1),
    )
    conn.exec_driver_sql(
        "INSERT INTO c05b03f_approvals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (claim.tenant, claim.device, claim.capture, claim.patient, claim.staff,
         claim.station, claim.station_revision, claim.generation, claim.asset_id,
         claim.digest, claim.byte_size, claim.version, claim.reason, 1),
    )

def test_c05b03f_real_alembic_migration_and_restore(bridge, tmp_path):
    engine, claim, device_token, station_token, media_root, _ = bridge
    assert os.getenv("DC06C05B03F_TEST_ONLY") == "1"
    root = media_root.parent
    dbpath = root / "clinical-asset-lab.db"
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)")
    engine.dispose()
    backup = tmp_path / "preupgrade-cipher.db"
    shutil.copy2(dbpath, backup)
    assert backup.read_bytes()[:16] != bytes.fromhex("53514c69746520666f726d6174203300")

    with engine.begin() as conn:
        before = conn.exec_driver_sql("SELECT COUNT(*) FROM clinical_assets").scalar_one()
        assert all(x not in _present(conn) for x in NAMES)
        _apply(conn, "upgrade")
        assert all(x in _present(conn) for x in NAMES)
        _apply(conn, "downgrade")
        assert all(x not in _present(conn) for x in NAMES)
        assert conn.exec_driver_sql("SELECT COUNT(*) FROM clinical_assets").scalar_one() == before
        _apply(conn, "upgrade")

    with engine.begin() as conn:
        _seed(conn, claim, device_token)
        assert conn.exec_driver_sql("SELECT COUNT(*) FROM c05b03f_approvals").scalar_one() == 1
        with pytest.raises((SAIntegrityError, CipherIntegrityError)):
            conn.exec_driver_sql(
                "INSERT INTO c05b03f_receipts VALUES(?,?,?,?,?,?,?)",
                (claim.tenant, claim.device, claim.capture, "FORGED", claim.version+1,
                 claim.asset_id, claim.digest),
            )
    rid = _issue(engine, claim, device_token, station_token, media_root)
    assert rid.startswith("LAB-ONLY-")
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "INSERT INTO c05b03f_receipts VALUES(?,?,?,?,?,?,?)",
            (claim.tenant, claim.device, claim.capture, rid,
             claim.version, claim.asset_id, claim.digest),
        )
        for tbl, evt in (("audit","CAPTURE_COMMITTED"),("outbox","MEDIA_READY")):
            conn.exec_driver_sql(f"INSERT INTO c05b03f_{tbl} VALUES(?,?)",(rid,evt))
        for tbl, field in (("receipts","version"),("audit","event"),("outbox","event")):
            with pytest.raises((SAIntegrityError, CipherIntegrityError), match="C05B03F_IMMUTABLE_LEDGER"):
                conn.exec_driver_sql(f"UPDATE c05b03f_{tbl} SET {field}=?",
                                     (99 if tbl=="receipts" else "FORGED",))
        with pytest.raises((SAIntegrityError, CipherIntegrityError), match="C05B03F_APPROVAL_FROZEN"):
            conn.exec_driver_sql("UPDATE c05b03f_approvals SET version=99")
        for name in ("receipts","audit","outbox"):
            assert conn.exec_driver_sql(f"SELECT COUNT(*) FROM c05b03f_{name}").scalar_one()==1
        with pytest.raises(RuntimeError, match="DOWNGRADE_REQUIRES_EMPTY_LEDGER"):
            _apply(conn,"downgrade")
        assert all(x in _present(conn) for x in NAMES)

    # Snapshot restore to a different isolated DB; no in-place destructive downgrade.
    restored = tmp_path / "restored"
    restored.mkdir()
    shutil.copy2(backup, restored / "clinical-asset-lab.db")
    fresh = _root_engine(restored)
    try:
        with fresh.connect() as conn:
            assert all(x not in _present(conn) for x in NAMES)
            assert conn.exec_driver_sql("SELECT COUNT(*) FROM clinical_assets").scalar_one() == before
        with Session(fresh) as db:
            proof = verify_device_capture_media_binding(
                db,tenant=claim.tenant,patient=claim.patient,asset_id=claim.asset_id,
                staff_id=claim.staff,digest=claim.digest,byte_size=claim.byte_size,
                media_root=media_root,
            )
            assert proof.clinical_receipt_authorized is False
    finally:
        fresh.dispose()

    evidence=Path(os.getenv("DC06C05B03F_EVIDENCE_DIR",str(tmp_path)))
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/"lot06c05b03f-ledger.json").write_text(json.dumps({
      "kind":"C05B03F_ALEMBIC_SQLCIPHER_CANDIDATE",
      "native_sqlcipher_migration_executed":True,
      "upgrade_empty_downgrade_executed":True,
      "real_backend_clinical_asset_preserved":True,
      "encrypted_preupgrade_snapshot_restored":True,
      "receipt_approval_version_conflict_refused":True,
      "immutable_receipt_audit_outbox_tested":True,
      "approval_frozen_after_receipt":True,
      "nonempty_downgrade_refused":True,
      "restored_encrypted_media_verified":True,
      "registered_in_production_alembic_chain":False,
      "clinical_api_http_jwt_tested":False,
      "staff_human_approval_tested":False,
      "device_enrollment_production":False,
      "clinical_receipt_authorized":False,
      "product_ready":False,
      "clinical_go":False,
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("C05B03F_CANDIDATE_SQLCIPHER_UPGRADE_DOWNGRADE_RESTORE_PASS")

def test_c05b03f_disabled_outside_isolated_test(bridge, monkeypatch):
    engine,*_=bridge
    monkeypatch.delenv("DC06C05B03F_TEST_ONLY",raising=False)
    with engine.begin() as conn,pytest.raises(RuntimeError,match="LAB_ONLY"):
        _apply(conn,"upgrade")
    monkeypatch.setenv("DC06C05B03F_TEST_ONLY","1")
    monkeypatch.setenv("ENVIRONMENT","cabinet")
    with engine.begin() as conn,pytest.raises(RuntimeError,match="LAB_ONLY"):
        _apply(conn,"upgrade")
    with engine.connect() as conn:
        assert all(x not in _present(conn) for x in NAMES)
    print("C05B03F_NO_CABINET_MIGRATION_PASS")
