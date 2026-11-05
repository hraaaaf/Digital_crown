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
