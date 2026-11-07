"""Isolated SQLite tests for the opt-in Pocket archive receipt registry."""
from __future__ import annotations
import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.services.mobile_document_archive_receipts import (
    MobileDocumentArchiveReceipt, claim_archive_intent, read_scoped_receipt,
    complete_archive_in_current_transaction, normalize_intent_key,
)

def _args(key, digest="a" * 64):
    return dict(tenant_id=101, actor_id=102, device_id="device-103",
                key=key, patient_id=104, document_type="certificat",
                request_sha256=digest)

@pytest.fixture
def isolated_receipts(tmp_path):
    engine = create_engine("sqlite:///" + str(tmp_path / "receipts.db"),
                           connect_args={"check_same_thread": False})
    MobileDocumentArchiveReceipt.__table__.create(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()

def test_duplicate_intent_is_single_writer(isolated_receipts):
    key = str(uuid.uuid4())
    with isolated_receipts() as db:
        original, new = claim_archive_intent(db, **_args(key))
        assert new and original.state == "PROCESSING"
    with isolated_receipts() as db:
        repeat, new = claim_archive_intent(db, **_args(key))
        assert not new and repeat.id == original.id
        assert db.query(func.count(MobileDocumentArchiveReceipt.id)).scalar() == 1
        with pytest.raises(HTTPException) as collision:
            claim_archive_intent(db, **_args(key, "b" * 64))
        assert collision.value.status_code == 409

def test_uuid_version_gate():
    assert normalize_intent_key(str(uuid.uuid4()))
    with pytest.raises(HTTPException) as e:
        normalize_intent_key(str(uuid.uuid1()))
    assert e.value.status_code == 422

def test_atomic_completion_and_restart(isolated_receipts):
    from types import SimpleNamespace
    key = str(uuid.uuid4())
    with isolated_receipts() as db:
        receipt, _ = claim_archive_intent(db, **_args(key))
        db.info["_mobile_document_archive_receipt_id"] = receipt.id
        fake = SimpleNamespace(id=900, patient_id=104, uploaded_by_id=102, file_hash="c" * 64)
        complete_archive_in_current_transaction(db, archive=fake)
        db.rollback()
        pending = read_scoped_receipt(db, tenant_id=101, actor_id=102, device_id="device-103", key=key)
        assert pending.state == "PROCESSING" and pending.archive_id is None
        complete_archive_in_current_transaction(db, archive=fake)
        db.commit()
    with isolated_receipts() as db:
        saved = read_scoped_receipt(db, tenant_id=101, actor_id=102, device_id="device-103", key=key)
        assert saved.state == "COMPLETED" and saved.archive_id == 900
        assert saved.archive_sha256 == "c" * 64

def test_receipt_is_scoped_to_device_and_cabinet(isolated_receipts):
    key = str(uuid.uuid4())
    with isolated_receipts() as db:
        claim_archive_intent(db, **_args(key))
        assert read_scoped_receipt(db, tenant_id=101, actor_id=102, device_id="other", key=key) is None
        assert read_scoped_receipt(db, tenant_id=999, actor_id=102, device_id="device-103", key=key) is None

def test_concurrent_same_key_has_only_one_claim(isolated_receipts):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    key = str(uuid.uuid4())
    gate = Barrier(2)
    def worker(_index):
        with isolated_receipts() as db:
            gate.wait(timeout=5)
            receipt, created = claim_archive_intent(db, **_args(key))
            return receipt.id, created
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(worker, (0, 1)))
    assert [created for _id, created in results].count(True) == 1
    assert results[0][0] == results[1][0]
    with isolated_receipts() as db:
        assert db.query(func.count(MobileDocumentArchiveReceipt.id)).scalar() == 1

def test_missing_schema_never_creates_cabinet_table(tmp_path):
    from sqlalchemy import inspect
    from backend.services.mobile_document_archive_receipts import assert_receipt_schema
    engine = create_engine("sqlite:///" + str(tmp_path / "without-migration.db"))
    with sessionmaker(bind=engine)() as db:
        with pytest.raises(HTTPException) as error:
            assert_receipt_schema(db)
        assert error.value.status_code == 503
        assert not inspect(engine).has_table("mobile_document_archive_receipts")
    engine.dispose()

def test_fresh_process_after_worker_death_keeps_processing_lock(isolated_receipts):
    """Real process exit after durable claim; nobody may silently replay it."""
    import os
    import subprocess
    import sys

    key = str(uuid.uuid4())
    with isolated_receipts() as db:
        database_path = db.bind.url.database
    code = (
        "import os\n"
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import sessionmaker\n"
        "from backend.services.mobile_document_archive_receipts import claim_archive_intent\n"
        "engine=create_engine('sqlite:///'+os.environ['CPV2_RECEIPT_DB'])\n"
        "with sessionmaker(bind=engine)() as db:\n"
        "    receipt, created = claim_archive_intent(db, tenant_id=101, actor_id=102, "
        "device_id='device-103', key=os.environ['CPV2_RECEIPT_KEY'], patient_id=104, "
        "document_type='certificat', request_sha256='a'*64)\n"
        "    assert created and receipt.state=='PROCESSING'\n"
        "os._exit(73)\n"
    )
    env = {**os.environ, "CPV2_RECEIPT_DB": database_path, "CPV2_RECEIPT_KEY": key}
    crashed = subprocess.run(
        [sys.executable, "-c", code],
        env=env, capture_output=True, text=True, timeout=30, check=False,
    )
    assert crashed.returncode == 73, crashed.stderr[-1000:]
    with isolated_receipts() as reopened:
        old, created = claim_archive_intent(reopened, **_args(key))
        assert not created
        assert old.state == "PROCESSING" and old.archive_id is None
        assert reopened.query(func.count(MobileDocumentArchiveReceipt.id)).scalar() == 1
        # An inspector can identify the incident but must never delete the
        # receipt, unlock the intent or guess whether an orphan PDF exists.
