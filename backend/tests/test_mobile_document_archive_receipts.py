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
