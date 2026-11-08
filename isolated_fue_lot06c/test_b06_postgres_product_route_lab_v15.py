"""B06-4C: actual FastAPI JWT/station/two-marker route into disposable PG.

The PostgreSQL writer is a test-only candidate injected into the actual route.
This does not add production PostgreSQL persistence or activate the cabinet.
"""
from __future__ import annotations

import hashlib

import httpx
import pytest
from sqlalchemy import insert, select, func
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_media_core import ClinicalAsset
from backend.routers import imaging_acquisition_unassigned_v15 as product
from backend.services.clinical_asset_service import list_clinical_assets_for_patient
from backend.services.clinical_asset_storage import read_clinical_asset_bytes
from backend.services.imaging_acquisition_product_review_v15 import ProductReviewStore
from backend.services.imaging_acquisition_native_bridge_v15 import LocalNativeCaptureBridge
from isolated_fue_lot06c import b06_postgres_product_candidate_lab as candidate
from isolated_fue_lot06c.test_b06_postgres_clone_contract_v15 import pg_ledger
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import (
    _localhost_server, synthetic_sqlcipher_bridge,
)
from isolated_fue_lot06c.test_phase2_staff_review_media_sqlcipher_v15 import _ctx
from tools.imaging_gateway.native_inventory_protocol_v15 import UnassignedCapture


def _counts(engine):
    with engine.connect() as conn:
        return tuple(conn.execute(select(func.count()).select_from(t)).scalar_one()
                     for t in (ClinicalAsset.__table__, candidate.receipts,
                               candidate.audit, candidate.outbox))


def _setup(pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch, capture_id=601):
    source, claim, _token, station_token, _media, _src, _collector, _item, raw, \
        _private, _challenge, headers, app, _pub = _ctx(
            synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        )
    engine = pg_ledger
    # Real ORM tables, real SQL FK linking capture ledger to real ClinicalAsset
    # and tenant/patient. The schema is synthesized ONLY in isolated pg_ledger.
    for table in (models.User.__table__, models.Patient.__table__,
                  models.WorkstationMode.__table__, models.RevokedToken.__table__,
                  ClinicalAsset.__table__):
        table.create(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "ALTER TABLE patients ADD CONSTRAINT dc06_b06_lab_patient_key "
            "UNIQUE (employer_id,id)"
        )
        conn.exec_driver_sql(
            "ALTER TABLE clinical_assets ADD CONSTRAINT dc06_b06_lab_asset_key "
            "UNIQUE (employer_id,patient_id,id)"
        )
        conn.exec_driver_sql(
            "ALTER TABLE dc06_b06_product_receipts "
            "ADD CONSTRAINT dc06_b06_lab_asset_fk "
            "FOREIGN KEY (tenant,patient,asset_id) "
            "REFERENCES clinical_assets(employer_id,patient_id,id)"
        )
        conn.exec_driver_sql(
            "ALTER TABLE dc06_b06_product_receipts "
            "ADD CONSTRAINT dc06_b06_lab_tenant_patient_fk "
            "FOREIGN KEY (tenant,patient) REFERENCES patients(employer_id,id)"
        )
        for table, name in (("audit", "audit"), ("outbox", "outbox")):
            conn.exec_driver_sql(
                f"ALTER TABLE dc06_b06_product_{table} "
                f"ADD CONSTRAINT dc06_b06_lab_receipt_{name}_fk "
                "FOREIGN KEY (receipt_id) "
                "REFERENCES dc06_b06_product_receipts(receipt_id)"
            )

    # Mirror *synthetic* staff + patient + workstation records exactly into PG.
    # The same actual JWT from _ctx must resolve in the PG-backed app.
    with Session(source) as db, engine.begin() as dest:
        for table in (models.User.__table__, models.Patient.__table__,
                      models.WorkstationMode.__table__):
            data = [dict(item) for item in db.execute(select(table)).mappings()]
            assert data, table.name
            dest.execute(insert(table), data)

    capture = UnassignedCapture(
        id=capture_id, digest=hashlib.sha256(raw).hexdigest(),
        size=len(raw), mime="image/png", category="RADIOGRAPH",
    )
    active = {"capture": capture, "media": raw}
    app.state.dc06_unassigned_bridge = LocalNativeCaptureBridge(
        tenant_id=claim.tenant, workstation_id=claim.station,
        inventory_reader=lambda: active["capture"],
        media_reader=lambda _capture: active["media"],
    )
    app.state.dc06_review_store = ProductReviewStore()
    app.state.dc06_b06_media_root = tmp_path / "pg-b06-encrypted-media"
    app.state.dc06_b06_durable_enabled = True  # explicitly TEST ONLY

    async def product_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[database.get_db] = product_db

    # This is dependency injection exclusively inside a single pytest process.
    # Production product route still references fail-closed SQLCipher service.
    monkeypatch.setattr(product, "is_committed", candidate.is_committed)
    monkeypatch.setattr(product, "receipt_for", candidate.receipt_for)
    monkeypatch.setattr(product, "commit_capture", candidate.commit_capture)
    app.include_router(product.router, prefix="/api/imaging/acquisition")
    return engine, claim, station_token, {k:v for k,v in headers.items()
        if k.lower() != "content-type"}, app, active


def _review(http, claim, headers, active):
    uri = "/api/imaging/acquisition/review"
    start = {
        "capture_id": active["capture"].id,
        "capture_digest": active["capture"].digest,
        "selected_patient_id": claim.patient,
    }
    result = http.post(uri, json=start, headers=headers)
    assert result.status_code == 200, result.text[:320]
    view = result.json()
    payload = {
        "challenge": view["challenge"],
        "selected_patient_id": claim.patient,
        "dossier": view["numero_dossier"],
        "date_naissance": view["date_naissance"],
        "capture_digest": active["capture"].digest,
        "explicit_confirmation": True,
    }
    return uri + "/" + view["review_id"] + "/commit", payload


def test_b06_4c_pg_real_orm_http_jwt_station_patient_signed_c2_timeline(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    assert _counts(engine) == (0, 0, 0, 0)
    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        uri = "/api/imaging/acquisition/review"
        assert http.post(uri, json={
            "capture_id": active["capture"].id,
            "capture_digest": active["capture"].digest,
            "selected_patient_id": claim.patient,
        }).status_code in (401, 403)
        http.cookies.set("dc_workstation", "wrong-station")
        assert http.post(uri, json={
            "capture_id": active["capture"].id,
            "capture_digest": active["capture"].digest,
            "selected_patient_id": claim.patient,
        }, headers=headers).status_code == 423
        http.cookies.set("dc_workstation", station)
        commit, valid = _review(http, claim, headers, active)
        assert http.post(commit, json={**valid, "dossier": "FORGED"},
                         headers=headers).status_code == 409
        assert http.post(commit, json={**valid, "date_naissance": "1970-01-01"},
                         headers=headers).status_code == 409
        assert _counts(engine) == (0, 0, 0, 0)
        first = http.post(commit, json=valid, headers=headers)
        assert first.status_code == 200, first.text[:400]
        ack = first.json()
        assert ack["status"] == "DURABLE_MEDIA_ACK"
        assert ack["clinical_receipt_authorized"] is False
        assert ack["patient_assigned"] is True
        assert ack["media_published"] is True
        assert _counts(engine) == (1, 1, 1, 1)
        with Session(engine) as db:
            asset = db.get(ClinicalAsset, ack["asset_id"])
            assert asset.employer_id == claim.tenant
            assert asset.patient_id == claim.patient
            assert asset.source_kind == "DEVICE_CAPTURE"
            assert asset.storage_format == "AESGCM_V1"
            assert read_clinical_asset_bytes(
                db, employer_id=claim.tenant, patient_id=claim.patient,
                asset_id=ack["asset_id"],
                media_root=app.state.dc06_b06_media_root,
            ) == active["media"]
            timeline = list_clinical_assets_for_patient(
                db, employer_id=claim.tenant, patient_id=claim.patient,
            )
            assert any(a.id == ack["asset_id"] for a in timeline)
        # Worker restart: no native device or local volatile review state,
        # yet authenticated, server-bound recovery validates full signed ACK.
        app.state.dc06_review_store = ProductReviewStore()
        del app.state.dc06_unassigned_bridge
        path = f"/api/imaging/acquisition/receipts/{active['capture'].id}"
        params = {"selected_patient_id": claim.patient,
                  "capture_digest": active["capture"].digest}
        replay = http.get(path, params=params, headers=headers)
        assert replay.status_code == 200, replay.text[:300]
        assert replay.json() == ack
        assert http.get(path, params={**params,
            "selected_patient_id": claim.patient + 1},
            headers=headers).status_code in (403, 404, 409)
        assert http.get(path, params={**params,
            "capture_digest": "0" * 64}, headers=headers).status_code == 409
        assert _counts(engine) == (1, 1, 1, 1)
    print("DC06_B06_4C_PG18_REAL_HTTP_JWT_STATION_PATIENT_SIGNED_C2_TIMELINE_RESTART_PASS")


@pytest.mark.parametrize("failpoint", [
    "after_asset", "after_receipt", "after_audit",
])
def test_b06_4c_pg_real_orm_rollback_all_four_records(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch, failpoint,
):
    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        capture_id={"after_asset":602, "after_receipt":603,
                    "after_audit":604}[failpoint],
    )
    app.state.dc06_b06_lab_failpoint = failpoint
    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, valid = _review(http, claim, headers, active)
        refused = http.post(commit, json=valid, headers=headers)
        assert refused.status_code == 503, refused.text[:250]
        assert _counts(engine) == (0, 0, 0, 0)
        app.state.dc06_b06_lab_failpoint = None
        ok = http.post(commit, json=valid, headers=headers)
        assert ok.status_code == 200, ok.text[:300]
        assert _counts(engine) == (1, 1, 1, 1)
    print("DC06_B06_4C_PG18_ASSET_LEDGER_AUDIT_OUTBOX_ROLLBACK_PASS", failpoint)


@pytest.mark.parametrize("fault", [
    "encrypted_blob_corrupt",
    "encrypted_blob_missing",
    "workstation_cookie_changed",
    "bearer_missing",
    "staff_revoked",
])
def test_b06_4d_pg_ack_recovery_adversarial(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch, fault,
):
    """Disposable PG/FastAPI: never return a signed ACK after loss of proof.

    This validates a laboratory recovery boundary, not PostgreSQL product
    readiness, human sign-off, power-cut durability or cabinet migration.
    """
    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        capture_id=700,
    )
    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, valid = _review(http, claim, headers, active)
        saved = http.post(commit, json=valid, headers=headers)
        assert saved.status_code == 200, saved.text[:300]
        assert _counts(engine) == (1, 1, 1, 1)
        path = f"/api/imaging/acquisition/receipts/{active['capture'].id}"
        params = {
            "selected_patient_id": claim.patient,
            "capture_digest": active["capture"].digest,
        }
        authorized_headers = headers
        if fault in ("encrypted_blob_corrupt", "encrypted_blob_missing"):
            files = [p for p in app.state.dc06_b06_media_root.rglob("*")
                     if p.is_file()]
            assert len(files) == 1, "expected exactly one synthetic ciphertext"
            blob = files[0]
            if fault == "encrypted_blob_corrupt":
                original = blob.read_bytes()
                assert len(original) > 1
                blob.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
            else:
                blob.unlink()
        elif fault == "workstation_cookie_changed":
            http.cookies.set("dc_workstation", "wrong-station")
        elif fault == "bearer_missing":
            authorized_headers = {}
        elif fault == "staff_revoked":
            with Session(engine) as db:
                record = db.execute(select(candidate.receipts)).mappings().one()
                user = db.get(models.User, record["staff"])
                assert user is not None
                user.is_active = False
                db.commit()

        denied = http.get(path, params=params, headers=authorized_headers)
        if fault.startswith("encrypted_blob_"):
            assert denied.status_code == 409, denied.text[:300]
            assert denied.json()["detail"] == "DURABLE_RECEIPT_NOT_VERIFIED"
        elif fault == "workstation_cookie_changed":
            assert denied.status_code == 423, denied.text[:300]
        else:
            assert denied.status_code in (401, 403, 423), denied.text[:300]
        assert _counts(engine) == (1, 1, 1, 1)
    print("DC06_B06_4D_PG18_ACK_RECOVERY_ADVERSARIAL_DENIED_PASS", fault)



def test_b06_4db_pg_non_owner_role_matrix(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    """Separate PG roles in a disposable schema; no product credentials changed.

    The CI fixture owner can SET LOCAL ROLE to prove the effective permissions.
    This is not an actual non-owner product integration or a cabinet migration.
    """
    import re

    from sqlalchemy.exc import DBAPIError

    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        capture_id=721,
    )
    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, valid = _review(http, claim, headers, active)
        saved = http.post(commit, json=valid, headers=headers)
        assert saved.status_code == 200, saved.text[:300]
    assert _counts(engine) == (1, 1, 1, 1)

    with engine.connect() as conn:
        schema = conn.exec_driver_sql("SELECT current_schema()").scalar_one()
        db_identity = conn.exec_driver_sql(
            "SELECT current_database(), current_user"
        ).one()
    assert re.fullmatch(r"dc06_b06_lab_[0-9a-f]{16}", schema)
    assert tuple(db_identity) == ("dc06_b06_ci", "dc06_synthetic")
    runtime = f"{schema}_runtime"
    migrator = f"{schema}_migrator"

    read_tables = tuple(t.name for t in (
        models.User.__table__, models.Patient.__table__,
        models.WorkstationMode.__table__, models.RevokedToken.__table__,
        ClinicalAsset.__table__, candidate.receipts, candidate.audit,
        candidate.outbox,
    ))
    insert_tables = tuple(t.name for t in (
        ClinicalAsset.__table__, candidate.receipts, candidate.audit,
        candidate.outbox,
    ))
    # All dynamically quoted identifiers below are generated from the
    # fixture's exact validated schema or fixed SQLAlchemy model metadata.
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", name) for name in read_tables)
    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE ROLE "{runtime}" NOLOGIN')
        conn.exec_driver_sql(f'CREATE ROLE "{migrator}" NOLOGIN')
        conn.exec_driver_sql(f'REVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC')
        conn.exec_driver_sql(f'GRANT USAGE ON SCHEMA "{schema}" TO "{runtime}"')
        conn.exec_driver_sql(
            f'GRANT USAGE, CREATE ON SCHEMA "{schema}" TO "{migrator}"'
        )
        for name in read_tables:
            conn.exec_driver_sql(
                f'GRANT SELECT ON TABLE "{schema}"."{name}" TO "{runtime}"'
            )
        for name in insert_tables:
            conn.exec_driver_sql(
                f'GRANT INSERT ON TABLE "{schema}"."{name}" TO "{runtime}"'
            )
        conn.exec_driver_sql(
            f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "{schema}" '
            f'TO "{runtime}"'
        )
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(f'SET LOCAL ROLE "{runtime}"')
            assert conn.exec_driver_sql(
                "SELECT current_user"
            ).scalar_one() == runtime
            assert conn.exec_driver_sql(
                f'SELECT count(*) FROM "{schema}"."{candidate.receipts.name}"'
            ).scalar_one() == 1
            for name in read_tables:
                assert conn.exec_driver_sql(
                    "SELECT has_table_privilege(%s, %s, 'SELECT')",
                    (runtime, f"{schema}.{name}"),
                ).scalar_one() is True
                assert conn.exec_driver_sql(
                    "SELECT has_table_privilege(%s, %s, 'UPDATE')",
                    (runtime, f"{schema}.{name}"),
                ).scalar_one() is False
                assert conn.exec_driver_sql(
                    "SELECT has_table_privilege(%s, %s, 'DELETE')",
                    (runtime, f"{schema}.{name}"),
                ).scalar_one() is False
            for name in insert_tables:
                assert conn.exec_driver_sql(
                    "SELECT has_table_privilege(%s, %s, 'INSERT')",
                    (runtime, f"{schema}.{name}"),
                ).scalar_one() is True
            assert conn.exec_driver_sql(
                "SELECT has_schema_privilege(%s, %s, 'CREATE')",
                (runtime, schema),
            ).scalar_one() is False

        denied_sql = [
            f'CREATE TABLE "{schema}"."dc06_rogue" (id INTEGER)',
            f'ALTER TABLE "{schema}"."{candidate.receipts.name}" '
            'ADD COLUMN dc06_rogue INTEGER',
        ]
        for table in (candidate.receipts, candidate.audit, candidate.outbox):
            ident = f'"{schema}"."{table.name}"'
            denied_sql.extend([
                f'UPDATE {ident} SET event = event' if table is not candidate.receipts
                else f'UPDATE {ident} SET signature = signature',
                f'DELETE FROM {ident}',
                f'TRUNCATE {ident}',
            ])
        for sql in denied_sql:
            with pytest.raises(DBAPIError) as err:
                with engine.begin() as conn:
                    conn.exec_driver_sql(f'SET LOCAL ROLE "{runtime}"')
                    conn.exec_driver_sql(sql)
            # Permission failure, not merely the owner-enforced trigger.
            assert err.value.orig.sqlstate == "42501", (sql, err.value)

        # Distinct migrator role can perform a synthetic disposable-schema
        # DDL rehearsal but the runtime role cannot.
        with engine.begin() as conn:
            conn.exec_driver_sql(f'SET LOCAL ROLE "{migrator}"')
            assert conn.exec_driver_sql(
                "SELECT current_user"
            ).scalar_one() == migrator
            conn.exec_driver_sql(
                f'CREATE TABLE "{schema}"."dc06_role_smoke" (id INTEGER)'
            )
            conn.exec_driver_sql(
                f'DROP TABLE "{schema}"."dc06_role_smoke"'
            )
    finally:
        # Must clean up roles even when assertions fail. All grants, schemas
        # and test rows are isolated to ephemeral PostgreSQL CI state.
        with engine.begin() as conn:
            for role in (runtime, migrator):
                conn.exec_driver_sql(f'DROP OWNED BY "{role}"')
                conn.exec_driver_sql(f'DROP ROLE "{role}"')
    assert _counts(engine) == (1, 1, 1, 1)
    print("DC06_B06_4DB_PG18_SEPARATE_ROLES_RUNTIME_DDL_DML_DENIED_PASS")


def test_b06_4db_pg_key_rotation_without_keyring_fail_closed(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    """Prove the current old-ACK outage under naive key replacement.

    A historical verification keyring DOES NOT exist yet; a rotation is NOT
    supported and restoring the original synthetic key is not a rotation plan.
    """
    import os

    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        capture_id=722,
    )
    before = os.environ.get("CABINET_MASTER_KEY_HEX", "")
    assert len(before) == 64
    replacement = bytearray(bytes.fromhex(before))
    replacement[0] ^= 1
    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, valid = _review(http, claim, headers, active)
        result = http.post(commit, json=valid, headers=headers)
        assert result.status_code == 200, result.text[:300]
        receipt = result.json()
        path = f"/api/imaging/acquisition/receipts/{active['capture'].id}"
        params = {
            "selected_patient_id": claim.patient,
            "capture_digest": active["capture"].digest,
        }
        monkeypatch.setenv("CABINET_MASTER_KEY_HEX", replacement.hex())
        try:
            denied = http.get(path, params=params, headers=headers)
            assert denied.status_code == 409, denied.text[:350]
            assert denied.json()["detail"] == "DURABLE_RECEIPT_NOT_VERIFIED"
            assert _counts(engine) == (1, 1, 1, 1)
        finally:
            monkeypatch.setenv("CABINET_MASTER_KEY_HEX", before)
        restored = http.get(path, params=params, headers=headers)
        assert restored.status_code == 200, restored.text[:350]
        assert restored.json() == receipt
        assert _counts(engine) == (1, 1, 1, 1)
    print("DC06_B06_4DB_PG18_UNVERSIONED_KEY_ROTATION_FAIL_CLOSED_PASS")



def test_b06_4dc_pg_immutable_trigger_body_tamper_denied(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    """A trigger with the right name but a no-op body MUST NOT authorize ACK.

    All data and DDL live in an isolated disposable pg_ledger test schema.
    Neither a production backend nor a patient cabinet is accessed.
    """
    from backend.services.imaging_acquisition_durable_v15 import DurableCaptureDenied

    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch, 805,
    )
    assert candidate.is_committed(
        engine, tenant=claim.tenant, station=claim.station, capture=805,
    ) is False
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "CREATE OR REPLACE FUNCTION dc06_b06_lab_immutable() "
            "RETURNS trigger LANGUAGE plpgsql AS 'BEGIN RETURN NEW; END'"
        )
    # All nine existing triggers still exist and are enabled. A simple name
    # check would approve this schema despite removing their protection.
    with engine.connect() as conn:
        assert conn.exec_driver_sql(
            "SELECT count(*) FROM pg_trigger t "
            "JOIN pg_class c ON c.oid=t.tgrelid "
            "WHERE c.relname IN ('dc06_b06_product_receipts', "
            "'dc06_b06_product_audit', 'dc06_b06_product_outbox') "
            "AND t.tgenabled='O' AND NOT t.tgisinternal"
        ).scalar_one() == 9
    with pytest.raises(DurableCaptureDenied, match="PG_PRODUCT_SCHEMA_NOT_APPROVED"):
        candidate.is_committed(
            engine, tenant=claim.tenant, station=claim.station, capture=805,
        )
    assert _counts(engine) == (0, 0, 0, 0)
    print("DC06_B06_4DC_PG18_TAMPERED_TRIGGER_BODY_FAIL_CLOSED_PASS")


def test_b06_4dc_pg_distinct_login_writer(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    """Actual password-authenticated PG sockets, not SET ROLE impersonation.

    Every username is derived from an ephemeral per-test schema. Separate
    NO-SUPERUSER LOGIN principals are never installed outside disposable CI.
    The product writer continues to refuse PostgreSQL; the test-only
    candidate exercises the real HTTP/JWT/ORM route with a restricted login.
    """
    import re
    import secrets

    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import DBAPIError

    from isolated_fue_lot06c.test_b06_postgres_clone_contract_v15 import (
        _guarded_ci_dsn,
    )

    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        capture_id=731,
    )
    with engine.connect() as conn:
        schema = conn.exec_driver_sql("SELECT current_schema()").scalar_one()
    assert re.fullmatch(r"dc06_b06_lab_[0-9a-f]{16}", schema)
    runtime = f"{schema}_runtime"
    migrator = f"{schema}_migrator"
    runtime_password = secrets.token_hex(24)
    migrator_password = secrets.token_hex(24)
    names = (runtime, migrator)
    runtime_engine = None
    migrator_engine = None

    read_tables = tuple(table.name for table in (
        models.User.__table__, models.Patient.__table__,
        models.WorkstationMode.__table__, models.RevokedToken.__table__,
        ClinicalAsset.__table__, candidate.receipts, candidate.audit,
        candidate.outbox,
    ))
    insert_tables = tuple(table.name for table in (
        ClinicalAsset.__table__, candidate.receipts,
        candidate.audit, candidate.outbox,
    ))
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", name) for name in read_tables)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            f'CREATE ROLE "{runtime}" LOGIN PASSWORD \'{runtime_password}\''
        )
        conn.exec_driver_sql(
            f'CREATE ROLE "{migrator}" LOGIN PASSWORD \'{migrator_password}\''
        )
        conn.exec_driver_sql(f'REVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC')
        for role in names:
            conn.exec_driver_sql(
                f'GRANT CONNECT ON DATABASE dc06_b06_ci TO "{role}"'
            )
            conn.exec_driver_sql(
                f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"'
            )
        conn.exec_driver_sql(
            f'GRANT CREATE ON SCHEMA "{schema}" TO "{migrator}"'
        )
        for name in read_tables:
            conn.exec_driver_sql(
                f'GRANT SELECT ON TABLE "{schema}"."{name}" TO "{runtime}"'
            )
        for name in insert_tables:
            conn.exec_driver_sql(
                f'GRANT INSERT ON TABLE "{schema}"."{name}" TO "{runtime}"'
            )
        # C2 stores an asset in two steps: metadata INSERT then a bounded
        # UPDATE of storage fields. SQLAlchemy also auto-updates updated_at
        # on the ORM UPDATE; omit it and real PostgreSQL returns 42501.
        # Never grant UPDATE on patient_id, tenant, staff, provenance or the
        # append-only receipt ledger.
        conn.exec_driver_sql(
            f'GRANT UPDATE (sha256, byte_size, storage_key, storage_format, '
            f'stored_at, updated_at) ON TABLE "{schema}"."clinical_assets" TO "{runtime}"'
        )
        conn.exec_driver_sql(
            f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA "{schema}" '
            f'TO "{runtime}"'
        )
    try:
        url = make_url(_guarded_ci_dsn())
        connect_options = {"options": f"-c search_path={schema}"}
        runtime_engine = create_engine(
            url.set(username=runtime, password=runtime_password),
            connect_args=connect_options, pool_pre_ping=True,
        )
        migrator_engine = create_engine(
            url.set(username=migrator, password=migrator_password),
            connect_args=connect_options, pool_pre_ping=True,
        )
        for role, role_engine in (
            (runtime, runtime_engine), (migrator, migrator_engine)
        ):
            with role_engine.connect() as conn:
                assert tuple(conn.exec_driver_sql(
                    "SELECT current_database(), session_user, current_user, "
                    "current_schema()"
                ).one()) == ("dc06_b06_ci", role, role, schema)
        with runtime_engine.connect() as conn:
            assert conn.exec_driver_sql(
                "SELECT has_schema_privilege(current_user, current_schema(), 'CREATE')"
            ).scalar_one() is False
            for name in (candidate.receipts.name, candidate.audit.name,
                         candidate.outbox.name):
                assert conn.exec_driver_sql(
                    "SELECT has_table_privilege(current_user, %s, 'UPDATE')",
                    (f"{schema}.{name}",),
                ).scalar_one() is False
            assert conn.exec_driver_sql(
                "SELECT has_column_privilege(current_user, %s, %s, 'UPDATE')",
                (f"{schema}.clinical_assets", "patient_id"),
            ).scalar_one() is False

        # Genuine SQLAlchemy Session used by the actual FastAPI route now
        # obtains its own *non-owner* PostgreSQL LOGIN connection.
        async def limited_db():
            with Session(runtime_engine) as db:
                yield db
        app.dependency_overrides[database.get_db] = limited_db
        with _localhost_server(app) as base, httpx.Client(
            base_url=base, trust_env=False, timeout=25,
        ) as http:
            http.cookies.set("dc_workstation", station)
            commit, valid = _review(http, claim, headers, active)
            saved = http.post(commit, json=valid, headers=headers)
            assert saved.status_code == 200, saved.text[:450]
            ack = saved.json()
            assert ack["status"] == "DURABLE_MEDIA_ACK"
            assert _counts(engine) == (1, 1, 1, 1)
            path = f"/api/imaging/acquisition/receipts/{active['capture'].id}"
            params = {
                "selected_patient_id": claim.patient,
                "capture_digest": active["capture"].digest,
            }
            replay = http.get(path, params=params, headers=headers)
            assert replay.status_code == 200 and replay.json() == ack
            assert http.get(path, params={**params,
                "selected_patient_id": claim.patient + 1},
                headers=headers).status_code in (403, 404, 409)
            assert _counts(engine) == (1, 1, 1, 1)
        with Session(runtime_engine) as db:
            assert read_clinical_asset_bytes(
                db, employer_id=claim.tenant, patient_id=claim.patient,
                asset_id=ack["asset_id"],
                media_root=app.state.dc06_b06_media_root,
            ) == active["media"]

        # Real runtime socket must receive PostgreSQL 42501, not a
        # trigger's owner-only exception.
        forbidden_sql = (
            f'CREATE TABLE "{schema}".dc06_not_allowed (id INTEGER)',
            f'ALTER TABLE "{schema}"."{candidate.receipts.name}" '
            'ADD COLUMN forbidden INTEGER',
            f'UPDATE "{schema}"."{candidate.receipts.name}" '
            'SET signature = signature',
            f'DELETE FROM "{schema}"."{candidate.audit.name}"',
            f'TRUNCATE "{schema}"."{candidate.outbox.name}"',
            f'UPDATE "{schema}".clinical_assets '
            'SET patient_id = patient_id',
        )
        for stmt in forbidden_sql:
            with pytest.raises(DBAPIError) as error:
                with runtime_engine.begin() as conn:
                    conn.exec_driver_sql(stmt)
            assert error.value.orig.sqlstate == "42501", stmt
        with migrator_engine.begin() as conn:
            conn.exec_driver_sql(
                f'CREATE TABLE "{schema}".dc06_migrator_smoke (id INTEGER)'
            )
            conn.exec_driver_sql(
                f'DROP TABLE "{schema}".dc06_migrator_smoke'
            )
        assert _counts(engine) == (1, 1, 1, 1)
    finally:
        app.dependency_overrides.pop(database.get_db, None)
        if runtime_engine is not None:
            runtime_engine.dispose()
        if migrator_engine is not None:
            migrator_engine.dispose()
        with engine.begin() as conn:
            for name in names:
                conn.exec_driver_sql(f'DROP OWNED BY "{name}"')
                conn.exec_driver_sql(f'DROP ROLE "{name}"')
    print("DC06_B06_4DC_PG18_SEPARATE_PASSWORD_LOGIN_REAL_WRITER_PASS")


def test_b06_4dc_pg_dump_restore_with_encrypted_media(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    """Restore a REAL PG18 schema archive alongside AES-GCM test-only bytes.

    Uses only the pinned local GitHub job PostgreSQL 18 Docker service.
    This is an orderly synthetic PG restore, not a power cut, a clinic clone,
    production key escrow or an approved restore runbook.
    """
    import json
    import re
    import shutil
    import subprocess

    from isolated_fue_lot06c.test_b06_postgres_clone_contract_v15 import (
        _guarded_ci_dsn,
    )

    _guarded_ci_dsn()
    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        capture_id=732,
    )
    root = app.state.dc06_b06_media_root
    with engine.connect() as conn:
        schema = conn.exec_driver_sql("SELECT current_schema()").scalar_one()
        assert conn.exec_driver_sql(
            "SELECT current_database(), current_user"
        ).one() == ("dc06_b06_ci", "dc06_synthetic")
    assert re.fullmatch(r"dc06_b06_lab_[0-9a-f]{16}", schema)

    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, valid = _review(http, claim, headers, active)
        saved = http.post(commit, json=valid, headers=headers)
        assert saved.status_code == 200, saved.text[:400]
        ack = saved.json()
        assert _counts(engine) == (1, 1, 1, 1)

    # Require PostgreSQL 18's pg_dump/pg_restore, NEVER silently substitute
    # ORM row copying or a text-only table snapshot. CI has a PG18 service.
    assert shutil.which("docker"), "PG18_DOCKER_CLI_REQUIRED"
    listed = subprocess.run(
        ["docker", "ps", "--filter", "ancestor=postgres:18",
         "--format", "{{.ID}}"], check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert len(listed) == 1 and re.fullmatch(
        r"[0-9a-f]{12,64}", listed[0]
    ), "EXACTLY_ONE_GITHUB_PG18_LAB_CONTAINER_REQUIRED"
    container_id = listed[0]
    pg_dump = subprocess.run(
        ["docker", "exec", container_id, "pg_dump",
         "-U", "dc06_synthetic", "-d", "dc06_b06_ci",
         "-n", schema, "-Fc"],
        check=True, capture_output=True,
    ).stdout
    assert pg_dump.startswith(b"PGDMP")
    backup = tmp_path / "pg18-and-media-synthetic-bundle"
    backup.mkdir()
    media_snapshot = backup / "media"
    shutil.copytree(root, media_snapshot)
    blob_files = tuple(p for p in media_snapshot.rglob("*") if p.is_file())
    assert len(blob_files) == 1
    relative = blob_files[0].relative_to(media_snapshot)
    manifest = {
        "lab_database": "dc06_b06_ci",
        "schema": schema,
        "pg_dump_sha256": hashlib.sha256(pg_dump).hexdigest(),
        "encrypted_files": {
            str(relative): hashlib.sha256(blob_files[0].read_bytes()).hexdigest()
        },
    }
    (backup / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )

    def verify_bundle(dump_bytes):
        loaded = json.loads((backup / "manifest.json").read_text(
            encoding="utf-8"
        ))
        if loaded["schema"] != schema or loaded["lab_database"] != "dc06_b06_ci":
            return False
        if hashlib.sha256(dump_bytes).hexdigest() != loaded["pg_dump_sha256"]:
            return False
        return all(
            (media_snapshot / rel).is_file()
            and hashlib.sha256((media_snapshot / rel).read_bytes()).hexdigest() == expected
            for rel, expected in loaded["encrypted_files"].items()
        )

    # Tampered archive does not trigger any destructive DB operation.
    assert not verify_bundle(pg_dump[:-1] + bytes([pg_dump[-1] ^ 1]))
    assert verify_bundle(pg_dump)
    assert _counts(engine) == (1, 1, 1, 1)

    # Simulate loss of service state and encrypted on-disk data.
    shutil.rmtree(root)
    app.state.dc06_review_store = ProductReviewStore()
    del app.state.dc06_unassigned_bridge
    # Deleting the complete per-test schema deliberately simulates DB loss.
    with engine.begin() as conn:
        conn.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
    engine.dispose()
    # PG18 custom archive contains CREATE SCHEMA + tables, constraints,
    # triggers and clinical row data. Never restore into another database.
    assert verify_bundle(pg_dump)
    subprocess.run(
        ["docker", "exec", "-i", container_id, "pg_restore",
         "-U", "dc06_synthetic", "-d", "dc06_b06_ci",
         "--no-owner", "--no-acl", "--exit-on-error"],
        input=pg_dump, capture_output=True, check=True,
    )
    with engine.connect() as conn:
        assert conn.exec_driver_sql(
            "SELECT current_database(), current_schema()"
        ).one() == ("dc06_b06_ci", schema)
    assert _counts(engine) == (1, 1, 1, 1)
    # First test that DB-only restore will NOT recover signed media ACK.
    path = f"/api/imaging/acquisition/receipts/{active['capture'].id}"
    params = {
        "selected_patient_id": claim.patient,
        "capture_digest": active["capture"].digest,
    }
    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        denied = http.get(path, params=params, headers=headers)
        assert denied.status_code == 409, denied.text[:320]
        assert denied.json()["detail"] == "DURABLE_RECEIPT_NOT_VERIFIED"

        # Restore the encrypted bytes and verify the exact signed receipt.
        shutil.copytree(media_snapshot, root)
        restored = next(root.rglob("*.dcm"))
        assert hashlib.sha256(restored.read_bytes()).hexdigest() == (
            manifest["encrypted_files"][str(relative)]
        )
        recovered = http.get(path, params=params, headers=headers)
        assert recovered.status_code == 200, recovered.text[:320]
        assert recovered.json() == ack
        repeat = http.get(path, params=params, headers=headers)
        assert repeat.status_code == 200 and repeat.json() == ack
        denied_scope = http.get(path, params={**params,
            "selected_patient_id": claim.patient + 1},
            headers=headers)
        assert denied_scope.status_code in (403, 404, 409)
        assert _counts(engine) == (1, 1, 1, 1)

    with Session(engine) as db:
        assert read_clinical_asset_bytes(
            db, employer_id=claim.tenant, patient_id=claim.patient,
            asset_id=ack["asset_id"], media_root=root,
        ) == active["media"]
    print("DC06_B06_4DC_PG18_PGDUMP_MEDIA_RESTORE_SIGNED_ACK_PASS")



@pytest.mark.parametrize("fault", [
    "no_historical_key", "wrong_historical_key",
    "manifest_wrong_key_id", "manifest_tampered",
    "ciphertext_tampered", "historical_key_present",
])
def test_b06_4dd_versioned_offline_recovery_manifest_fail_closed(
    pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch, fault,
):
    """B06-4D-D: synthetic *offline* version selector, NOT a product keyring.

    The production media format and receipt remain unversioned. This lab-only
    manifest uses a separate recovery MAC key, never embeds the old master
    key and never modifies the product's encrypted blob or DB schema.
    """
    import hmac
    import json
    import os
    import secrets

    from backend.services.clinical_asset_storage import (
        ClinicalAssetStorageError, ClinicalAssetIntegrityError,
    )

    engine, claim, station, headers, app, active = _setup(
        pg_ledger, synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
        capture_id={
            "no_historical_key": 741,
            "wrong_historical_key": 742,
            "manifest_wrong_key_id": 743,
            "manifest_tampered": 744,
            "ciphertext_tampered": 745,
            "historical_key_present": 746,
        }[fault],
    )
    old_key = os.environ["CABINET_MASTER_KEY_HEX"]
    assert len(old_key) == 64
    replacement = bytearray(bytes.fromhex(old_key))
    replacement[0] ^= 0x01
    new_key = replacement.hex()
    # Separate, non-persisted recovery authentication secret. This is not
    # a production escrow, KMS, keyring or backup distribution mechanism.
    recovery_mac_key = secrets.token_bytes(32)
    old_id, new_id = "dc06-lab-key-v1", "dc06-lab-key-v2"
    with _localhost_server(app) as base, httpx.Client(
        base_url=base, trust_env=False, timeout=25,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, valid = _review(http, claim, headers, active)
        saved = http.post(commit, json=valid, headers=headers)
        assert saved.status_code == 200, saved.text[:350]
        original_ack = saved.json()
        assert _counts(engine) == (1, 1, 1, 1)
        with Session(engine) as db:
            asset = db.get(ClinicalAsset, original_ack["asset_id"])
            assert asset is not None
            storage_key = asset.storage_key
        root = app.state.dc06_b06_media_root
        ciphertext_path = root.joinpath(*storage_key.split("/"))
        original_ciphertext = ciphertext_path.read_bytes()
        manifest_body = {
            "format": "DC06-LAB-OFFLINE-RECOVERY-V1",
            "database": "dc06_b06_ci",
            "capture_id": active["capture"].id,
            "tenant": claim.tenant,
            "patient": claim.patient,
            "key_id": old_id,
            "storage_key": storage_key,
            "ciphertext_sha256": hashlib.sha256(original_ciphertext).hexdigest(),
            "ack_sha256": hashlib.sha256(
                json.dumps(original_ack, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }
        def canonical(body):
            return json.dumps(body, sort_keys=True,
                              separators=(",", ":")).encode("utf-8")
        manifest_mac = hmac.new(
            recovery_mac_key, canonical(manifest_body), hashlib.sha256
        ).hexdigest()
        assert old_key not in canonical(manifest_body).decode()
        assert new_key not in canonical(manifest_body).decode()
        manifest = dict(manifest_body)
        if fault == "manifest_wrong_key_id":
            manifest["key_id"] = new_id
        elif fault == "manifest_tampered":
            manifest["patient"] += 1
        elif fault == "ciphertext_tampered":
            ciphertext_path.write_bytes(
                original_ciphertext[:-1] +
                bytes([original_ciphertext[-1] ^ 1])
            )

        monkeypatch.setenv("CABINET_MASTER_KEY_HEX", new_key)
        uri = f"/api/imaging/acquisition/receipts/{active['capture'].id}"
        params = {
            "selected_patient_id": claim.patient,
            "capture_digest": active["capture"].digest,
        }
        denied = http.get(uri, params=params, headers=headers)
        assert denied.status_code == 409, denied.text[:350]
        assert denied.json()["detail"] == "DURABLE_RECEIPT_NOT_VERIFIED"

        # A verified version label is not enough: historical key material
        # must be supplied through an explicit, test-only offline resolver.
        keyring = {
            new_id: new_key,
            **({old_id: new_key} if fault == "wrong_historical_key" else {}),
            **({old_id: old_key} if fault in (
                "manifest_wrong_key_id", "manifest_tampered",
                "ciphertext_tampered", "historical_key_present"
            ) else {}),
        }
        def resolve_checked():
            if not hmac.compare_digest(
                hmac.new(recovery_mac_key, canonical(manifest),
                         hashlib.sha256).hexdigest(), manifest_mac
            ):
                return None
            if (
                manifest["database"] != "dc06_b06_ci"
                or manifest["tenant"] != claim.tenant
                or manifest["patient"] != claim.patient
                or manifest["capture_id"] != active["capture"].id
                or manifest["storage_key"] != storage_key
                or manifest["ciphertext_sha256"] != hashlib.sha256(
                    ciphertext_path.read_bytes()).hexdigest()
            ):
                return None
            historical = keyring.get(manifest["key_id"])
            if historical is None or historical == new_key:
                return None
            return historical

        historical_key = resolve_checked()
        if fault != "historical_key_present":
            assert historical_key is None
            assert http.get(uri, params=params, headers=headers).status_code == 409
        else:
            assert historical_key == old_key
            monkeypatch.setenv("CABINET_MASTER_KEY_HEX", historical_key)
            try:
                with Session(engine) as db:
                    assert read_clinical_asset_bytes(
                        db, employer_id=claim.tenant, patient_id=claim.patient,
                        asset_id=original_ack["asset_id"], media_root=root,
                    ) == active["media"]
                recovered = http.get(uri, params=params, headers=headers)
                assert recovered.status_code == 200, recovered.text[:350]
                assert recovered.json() == original_ack
                assert http.get(uri, params=params, headers=headers).json() == original_ack
            finally:
                monkeypatch.setenv("CABINET_MASTER_KEY_HEX", new_key)
            assert http.get(uri, params=params, headers=headers).status_code == 409
        assert _counts(engine) == (1, 1, 1, 1)
    print("DC06_B06_4DD_OFFLINE_HISTORICAL_KEY_MANIFEST_FUE_PASS", fault)
