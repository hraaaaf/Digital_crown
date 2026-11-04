"""B06-3 LAB FUE: actual product JWT+workstation routes, SQLCipher ledger.

Product's durable gate is OFF by default. Tables are provisioned explicitly
ONLY in this synthetic test database; no clinic migration, device or deploy.
"""
import hashlib
from pathlib import Path

import httpx
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend import database, models
from backend.models_media_core import ClinicalAsset
from backend.routers import imaging_acquisition_unassigned_v15
from backend.services.imaging_acquisition_durable_v15 import (
    metadata, receipts, audit, outbox,
)
from backend.services.imaging_acquisition_native_bridge_v15 import LocalNativeCaptureBridge
from backend.services.imaging_acquisition_product_review_v15 import ProductReviewStore
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import _localhost_server
from isolated_fue_lot06c.test_phase2_staff_review_media_sqlcipher_v15 import _ctx
from tools.imaging_gateway.native_inventory_protocol_v15 import UnassignedCapture


def _setup(synthetic_sqlcipher_bridge, tmp_path, monkeypatch, capture_id):
    (engine, claim, _token, station_token, _media, _source, _collector, _item,
     raw, _private, _challenge, headers, app, _pub) = _ctx(
         synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
     )
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
    app.state.dc06_b06_durable_enabled = True  # trusted LAB-only setup
    app.state.dc06_b06_media_root = tmp_path / "product-c2-encrypted"
    async def product_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[database.get_db] = product_db
    app.include_router(
        imaging_acquisition_unassigned_v15.router,
        prefix="/api/imaging/acquisition",
    )
    return engine, claim, station_token, headers, app, active


def _start(http, claim, active, headers):
    request = {
        "capture_id": active["capture"].id,
        "capture_digest": active["capture"].digest,
        "selected_patient_id": claim.patient,
    }
    result = http.post("/api/imaging/acquisition/review", json=request, headers=headers)
    assert result.status_code == 200, result.text[:300]
    payload = result.json()
    commit = "/api/imaging/acquisition/review/" + payload["review_id"] + "/commit"
    data = {
        "challenge": payload["challenge"],
        "selected_patient_id": claim.patient,
        "dossier": payload["numero_dossier"],
        "date_naissance": payload["date_naissance"],
        "capture_digest": active["capture"].digest,
        "explicit_confirmation": True,
    }
    return commit, data


def _counts(engine):
    with Session(engine) as db:
        return [
            db.execute(select(func.count()).select_from(table)).scalar_one()
            for table in (ClinicalAsset.__table__, receipts, audit, outbox)
        ]


def test_b06_3_schema_and_enablement_fail_closed_before_any_write(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    engine, claim, station, headers, app, active = _setup(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch, 81,
    )
    with _localhost_server(app) as origin, httpx.Client(
        base_url=origin, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, data = _start(http, claim, active, headers)
        app.state.dc06_b06_durable_enabled = False
        assert http.post(commit, json=data, headers=headers).status_code == 503
        app.state.dc06_b06_durable_enabled = True
        assert http.post(commit, json=data, headers=headers).status_code == 503
        with Session(engine) as db:
            assert db.query(ClinicalAsset).count() == 0
        metadata.create_all(engine)
        assert _counts(engine) == [0, 0, 0, 0]
        missing = http.post(commit, json={
            **data, "explicit_confirmation": False,
        }, headers=headers)
        assert missing.status_code == 409
        assert _counts(engine) == [0, 0, 0, 0]
    print("DC06_B06_3_SCHEMA_MISSING_AND_DISABLED_ZERO_WRITES_PASS")


def test_b06_3_durable_signed_ack_recovered_after_worker_restart(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    engine, claim, station, headers, app, active = _setup(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch, 82,
    )
    metadata.create_all(engine)
    with _localhost_server(app) as origin, httpx.Client(
        base_url=origin, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, data = _start(http, claim, active, headers)
        assert http.post(commit, json={**data, "dossier": "WRONG"}, headers=headers).status_code == 409
        assert http.post(commit, json={**data, "capture_digest": "0" * 64},
                         headers=headers).status_code == 409
        assert _counts(engine) == [0, 0, 0, 0]
        saved = http.post(commit, json=data, headers=headers)
        assert saved.status_code == 200, saved.text[:300]
        ack = saved.json()
        assert ack["status"] == "DURABLE_MEDIA_ACK"
        assert ack["patient_id"] == claim.patient
        assert ack["capture_digest"] == active["capture"].digest
        assert ack["patient_assigned"] is True
        assert ack["media_published"] is True
        assert ack["clinical_receipt_authorized"] is False
        assert len(ack["signature"]) == 128
        assert _counts(engine) == [1, 1, 1, 1]
        assert http.post(commit, json=data, headers=headers).status_code == 409

        # Simulate application worker restart; transient review disappears,
        # but a fresh authenticated staff session can retrieve the same ACK.
        app.state.dc06_review_store = ProductReviewStore()
        path = f"/api/imaging/acquisition/receipts/{active['capture'].id}"
        query = {
            "selected_patient_id": claim.patient,
            "capture_digest": active["capture"].digest,
        }
        lookup = http.get(path, headers=headers, params=query)
        assert lookup.status_code == 200, lookup.text[:300]
        assert lookup.json() == ack
        assert http.get(path, params={**query, "selected_patient_id": claim.patient + 99999},
                        headers=headers).status_code in (403, 404, 409)
        assert http.get(path, params={**query, "capture_digest": "0" * 64},
                        headers=headers).status_code == 409
        assert _counts(engine) == [1, 1, 1, 1]

        # A client cannot reuse the original ID with altered native bytes.
        active["media"] += b"tampered"
        assert http.get(path, headers=headers, params=query).json() == ack
        assert http.post("/api/imaging/acquisition/review", json={
            "capture_id": active["capture"].id,
            "capture_digest": active["capture"].digest,
            "selected_patient_id": claim.patient,
        }, headers=headers).status_code in (200, 409)
        assert _counts(engine) == [1, 1, 1, 1]
    print("DC06_B06_3_PRODUCT_SQLCIPHER_ASSET_SIGNED_ACK_RESTART_REPLAY_PASS")


def test_b06_3_sql_failure_rollback_then_single_commit(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    engine, claim, station, headers, app, active = _setup(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch, 83,
    )
    metadata.create_all(engine)
    with _localhost_server(app) as origin, httpx.Client(
        base_url=origin, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, data = _start(http, claim, active, headers)
        for point in ("after_asset", "after_receipt", "after_audit"):
            app.state.dc06_b06_lab_failpoint = point
            response = http.post(commit, json=data, headers=headers)
            assert response.status_code == 503, (point, response.text[:200])
            assert _counts(engine) == [0, 0, 0, 0]
        app.state.dc06_b06_lab_failpoint = None
        succeeded = http.post(commit, json=data, headers=headers)
        assert succeeded.status_code == 200, succeeded.text[:300]
        assert _counts(engine) == [1, 1, 1, 1]
        assert succeeded.json()["asset_id"] > 0
    print("DC06_B06_3_ATOMIC_ROLLBACK_ENCRYPTED_ORPHAN_SAFE_PASS")


def test_b06_3_signed_ledger_tamper_refused_on_ack_recovery(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    engine, claim, station, headers, app, active = _setup(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch, 84,
    )
    metadata.create_all(engine)
    with _localhost_server(app) as origin, httpx.Client(
        base_url=origin, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        commit, data = _start(http, claim, active, headers)
        assert http.post(commit, json=data, headers=headers).status_code == 200
        with engine.begin() as conn:
            conn.execute(receipts.update().values(signature="0" * 128))
        lookup = http.get(
            f"/api/imaging/acquisition/receipts/{active['capture'].id}",
            params={
                "selected_patient_id": claim.patient,
                "capture_digest": active["capture"].digest,
            }, headers=headers,
        )
        assert lookup.status_code == 409
        assert _counts(engine) == [1, 1, 1, 1]
    print("DC06_B06_3_TAMPERED_SIGNED_ACK_DENIED_PASS")
