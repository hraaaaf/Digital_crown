"""LOT06-C05A: real ephemeral PostgreSQL transactions, synthetic entities ONLY.

Unlike the earlier SQLCipher test ledger, these exercises acquire PostgreSQL row
locks using separate clients and test an OS process exit after real COMMIT.
Not the production clinical router, storage authority, or permission system.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
from sqlalchemy import create_engine, func, select

from backend.services import imaging_pg_receipt_authority_v15 as pg


@pytest.fixture(scope="module")
def db_engine():
    dsn = os.environ.get("DC06C05A_TEST_DSN", "")
    if not dsn:
        pytest.fail("C05A_PG_DSN_REQUIRED_NO_SQLITE_FALLBACK")
    engine = create_engine(dsn, pool_size=8, max_overflow=2)
    pg.guard(engine)
    pg.metadata.drop_all(bind=engine, checkfirst=True)
    pg.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        pg.metadata.drop_all(bind=engine, checkfirst=True)
        engine.dispose()


def _claim(capture: str, *, asset_id: int) -> pg.ApprovalClaim:
    return pg.ApprovalClaim(
        tenant=31, device="synthetic-device", capture=capture,
        digest=hashlib.sha256(("media:" + capture).encode()).hexdigest(),
        byte_size=127, patient=73, staff=81, approval_version=2,
        asset_id=asset_id, reason="LAB_WALK_IN",
    )


def _counts(engine, claim: pg.ApprovalClaim):
    with engine.connect() as conn:
        return (
            conn.execute(select(func.count()).select_from(pg.receipts)).scalar_one(),
            conn.execute(select(func.count()).select_from(pg.audit)).scalar_one(),
            conn.execute(select(func.count()).select_from(pg.outbox)).scalar_one(),
        )


def test_c05a_guard_blocks_unauthorized_runtime(db_engine, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(pg.AuthorityRejected, match="ISOLATED_PG_AUTHORITY_DISABLED"):
        pg.guard(db_engine)
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DC06C05A_PG_TEST", "0")
    with pytest.raises(pg.AuthorityRejected, match="ISOLATED_PG_AUTHORITY_DISABLED"):
        pg.guard(db_engine)


def test_c05a_concurrent_writers_rollback_and_lost_ack(db_engine, tmp_path):
    claim = _claim("capture-" + uuid.uuid4().hex, asset_id=1001)
    pg.seed_test_approval(db_engine, claim)
    assert pg.lookup_test_receipt(db_engine, claim) is None

    for point in ("after_receipt", "after_audit", "after_outbox"):
        with pytest.raises(pg.AuthorityRejected, match="INJECTED_POSTGRES_ROLLBACK"):
            pg.issue_test_receipt(db_engine, claim, fail_at=point)
        assert _counts(db_engine, claim) == (0, 0, 0)
        assert pg.lookup_test_receipt(db_engine, claim) is None

    # Six genuine concurrent PostgreSQL writers, each with its own
    # transaction/connection. Row lock serializes attempts to one receipt.
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(
            lambda _i: pg.issue_test_receipt(db_engine, claim), range(6)
        ))
    assert len({r["receipt_id"] for r in responses}) == 1
    assert all(r == responses[0] and r["server_confirmed"] is False for r in responses)
    assert _counts(db_engine, claim) == (1, 1, 1)
    assert pg.lookup_test_receipt(db_engine, claim) == responses[0]

    for conflict in (
        {"tenant": 32}, {"device": "wrong-device"}, {"capture": "wrong-capture"},
        {"digest": "0" * 64}, {"byte_size": 128}, {"patient": 74},
        {"staff": 82}, {"approval_version": 3}, {"asset_id": 2001},
        {"reason": "LAB_URGENT"},
    ):
        with pytest.raises(pg.AuthorityRejected, match="SERVER_APPROVAL_BINDING_CONFLICT"):
            pg.issue_test_receipt(db_engine, replace(claim, **conflict))
    assert _counts(db_engine, claim) == (1, 1, 1)

    # New capture: a separate OS process returns NO ACK to the caller after
    # its SQL transaction is committed. Parent process must find it again.
    ack_claim = _claim("lost-ack-" + uuid.uuid4().hex, asset_id=1002)
    pg.seed_test_approval(db_engine, ack_claim)
    env = os.environ.copy()
    env["DC06C05A_CLAIM_JSON"] = json.dumps(asdict(ack_claim))
    script = """
import json, os
from sqlalchemy import create_engine
from backend.services.imaging_pg_receipt_authority_v15 import ApprovalClaim, issue_test_receipt
engine = create_engine(os.environ["DC06C05A_TEST_DSN"])
claim = ApprovalClaim(**json.loads(os.environ["DC06C05A_CLAIM_JSON"]))
issue_test_receipt(engine, claim)
os._exit(75)
"""
    done = subprocess.run(
        [sys.executable, "-c", script], env=env,
        text=True, capture_output=True, timeout=45, check=False,
    )
    assert done.returncode == 75, (
        f"POSTGRES_POSTCOMMIT_TEST_PROCESS_EXIT_{done.returncode}"
    )
    assert env["DC06C05A_TEST_DSN"] not in done.stdout + done.stderr
    persisted = pg.lookup_test_receipt(db_engine, ack_claim)
    assert persisted and persisted["receipt_id"]
    assert all(pg.issue_test_receipt(db_engine, ack_claim) == persisted for _ in range(3))
    assert _counts(db_engine, claim) == (2, 2, 2)

    evidence_dir = Path(os.environ.get("DC06C05A_EVIDENCE_DIR", str(tmp_path)))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "lot06c05a-postgres-authority-fue.json").write_text(
        json.dumps({
            "kind": "LOT06_C05A_REAL_POSTGRES_CANDIDATE_NOT_CLINICAL",
            "real_ephemeral_postgres_server_used": True,
            "six_concurrent_independent_pg_transactions_same_receipt": True,
            "approval_version_and_binding_conflicts_rejected": True,
            "receipt_audit_outbox_atomic_on_injected_failures": True,
            "postcommit_os_exit_before_ack_recovered": True,
            "replay_same_receipt_after_restart": True,
            "sql_db_recovery_and_uniqueness_verified": True,
            "clinical_device_staff_authorization_wired": False,
            "aes_media_verified_in_authority": False,
            "clinical_migration_applied": False,
            "clinical_endpoint_enabled": False,
            "actual_power_cut_tested": False,
            "product_ready": False,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    print("LOT06C05A_PG_CONCURRENT_APPROVAL_COMMIT_ACK_RECOVERY_PASS")
