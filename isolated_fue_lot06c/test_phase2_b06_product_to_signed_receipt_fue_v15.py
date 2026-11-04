"""B06 one-HEAD FUE-I: mounted product status stays closed while isolated
staff-authenticated review and encrypted signed receipt complete together.
Never a real scanner, production IPC adapter, human click or cabinet activation.
"""
import httpx
import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from isolated_fue_lot06c import unassigned_device_manifest_lab as unassigned
from isolated_fue_lot06c.c05b03m_security_gate_lab import (
    identity, review as device_review, sign_test_device_claim, BridgeRejected,
)
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import _issue
from backend.services.clinical_asset_storage import store_clinical_asset_bytes

from backend import database
from backend.routers import imaging_acquisition_status_v15, imaging_acquisition_unassigned_v15
from backend.services.imaging_acquisition_product_review_v15 import ProductReviewStore
from backend import models
from backend.security import create_access_token
from backend.services.imaging_acquisition_native_bridge_v15 import LocalNativeCaptureBridge
from tools.imaging_gateway.native_inventory_protocol_v15 import (
    NativeInventoryDenied, UnassignedCapture,
)
import hashlib
from isolated_fue_lot06c.test_phase2_staff_review_media_sqlcipher_v15 import _ctx, _input
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import (
    _counts, _localhost_server, _post, synthetic_sqlcipher_bridge,
)
from tools.imaging_gateway import HotFolder


def test_b06_product_boundary_and_lab_review_media_receipt_same_server_and_db(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, token, station, media, source, collector, item,
     raw, private, challenge, headers, app, _pub) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )

    async def product_db():
        with Session(app.state.lab_sqlcipher_engine) as session:
            yield session

    app.dependency_overrides[database.get_db] = product_db
    app.include_router(imaging_acquisition_status_v15.router, prefix="/api/patients")
    status = f"/api/patients/{claim.patient}/acquisition/status"
    review = f"/isolated/lot06-phase2/review/{claim.capture}"
    json_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}

    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        assert http.get(status).status_code in (401, 403)
        assert http.get(review).status_code in (401, 403)
        assert _counts(engine) == (0, 0, 0)

        product = http.get(status, headers=headers)
        assert product.status_code == 200
        assert product.headers["cache-control"] == "no-store"
        assert product.json()["state"] == "NATIVE_IPC_NOT_CONNECTED"
        assert product.json()["pending_captures"] is None
        assert product.json()["acquisition_enabled"] is False
        assert product.json()["clinical_receipt_authorized"] is False
        assert http.post(status, json={}, headers=json_headers).status_code == 405

        # A capture is not associated with a patient by visiting its dossier.
        assert _post(http, claim, raw, headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)

        view = http.get(review, headers=headers)
        assert view.status_code == 200
        candidate = view.json()
        assert candidate["lab_only"] is True
        assert candidate["clinical_receipt_authorized"] is False
        assert candidate["patient_id"] == claim.patient
        assert candidate["capture_digest"] == claim.digest
        assert http.get(candidate["preview_url"], headers=headers).status_code == 409
        preview = http.get(candidate["preview_url"], headers={
            **headers, "X-DC-Review-Challenge": candidate["challenge"],
        })
        assert preview.status_code == 200 and preview.content == raw
        assert preview.headers["cache-control"] == "no-store"

        confirm = review + "/confirm"
        bad = {**_input(candidate), "date_naissance": "1970-01-01"}
        assert http.post(confirm, json=bad, headers=json_headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)
        ok = http.post(confirm, json=_input(candidate), headers=json_headers)
        assert ok.status_code == 200 and ok.json()["clinical_receipt_authorized"] is False
        assert http.post(confirm, json=_input(candidate), headers=json_headers).status_code == 409
        assert http.get(candidate["preview_url"], headers={
            **headers, "X-DC-Review-Challenge": candidate["challenge"],
        }).status_code == 409

        # A legacy device signature containing patient/staff never authorizes
        # this newly separated upload contract.
        assert "X-DC-Lab-Device-Proof" not in headers
        legacy = sign_test_device_claim(claim, challenge, private)
        assert _post(http, claim, raw, {
            **headers, "X-DC-Lab-Device-Proof": legacy,
        }).status_code == 409
        with engine.begin() as conn:
            conn.execute(update(identity).values(active=0))
        assert _post(http, claim, raw, headers).status_code == 409
        with engine.begin() as conn:
            conn.execute(update(identity).values(active=1))
        assert _counts(engine) == (0, 0, 0)
        with Session(engine) as db:
            signed = db.execute(select(unassigned.unassigned.c.signature)).scalar_one()
        with engine.begin() as conn:
            conn.execute(update(unassigned.unassigned).values(signature="0" * 128))
        assert _post(http, claim, raw, headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)
        with engine.begin() as conn:
            conn.execute(update(unassigned.unassigned).values(signature=signed))

        saved = _post(http, claim, raw, headers)
        assert saved.status_code == 200
        receipt = saved.json()
        assert receipt["clinical_receipt_authorized"] is False
        assert _counts(engine) == (1, 1, 1)

        restarted = HotFolder(collector.config)
        assert restarted.items()[0]["state"] == "PENDING_CONFIRMATION"
        retry = _post(http, claim, restarted.read_verified(item["id"]), headers)
        assert retry.status_code == 200 and retry.json() == receipt
        assert _counts(engine) == (1, 1, 1)

        # Even AFTER a LAB receipt, product device ingress remains blocked.
        after = http.get(status, headers=headers)
        assert after.status_code == 200 and after.json() == product.json()
        assert http.post(
            f"/api/patients/{claim.patient}/acquisition/confirm",
            json=_input(candidate), headers=json_headers,
        ).status_code == 404
    assert source.read_bytes() == raw
    print("DC06_B06_SAME_SERVER_PRODUCT_CLOSED_LAB_DUAL_ID_MEDIA_ACK_REPLAY_PASS")


def test_b06_unassigned_receipt_failpoint_rolls_back_and_replays(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, token, station, media, _source, collector, item,
     raw, _private, _challenge, headers, app, _pub) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    authority = unassigned.TestOnlyUnassignedMediaAuthority()
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        review = "/isolated/lot06-phase2/review/" + claim.capture
        view = http.get(review, headers=headers).json()
        json_headers = {k: v for k, v in headers.items()
                        if k.lower() != "content-type"}
        confirmed = http.post(
            review + "/confirm", json=_input(view), headers=json_headers,
        )
        assert confirmed.status_code == 200
        with Session(engine) as db:
            store_clinical_asset_bytes(
                db, employer_id=claim.tenant, patient_id=claim.patient,
                asset_id=claim.asset_id, content=raw, media_root=media,
            )
            db.commit()
        with pytest.raises(BridgeRejected, match="INJECTED_TRANSACTION_ROLLBACK"):
            _issue(
                engine, claim, token, station, media, fail_at="after_audit",
                locked_authorize=lambda db, c: authority.consume(db, c, ""),
            )
        assert _counts(engine) == (0, 0, 0)
        with Session(engine) as db:
            assert db.execute(select(device_review.c.consumed)).scalar_one() == 0
            assert db.execute(select(unassigned.unassigned.c.consumed)).scalar_one() == 1
        good = _post(http, claim, collector.read_verified(item["id"]), headers)
        assert good.status_code == 200
        assert _counts(engine) == (1, 1, 1)
        again = _post(http, claim, raw, headers)
        assert again.status_code == 200 and again.json() == good.json()
        assert _counts(engine) == (1, 1, 1)
    print("DC06_B06_UNASSIGNED_PROVENANCE_RECEIPT_ROLLBACK_REPLAY_PASS")


def test_b06_product_unassigned_inventory_jwt_workstation_bridge_and_verified_bytes(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, _token, station_token, _media, _source, _collector, _item,
     raw, _private, _challenge, headers, app, _pub) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    capture = UnassignedCapture(
        id=73, size=len(raw), digest=hashlib.sha256(raw).hexdigest(),
        mime="image/png", category="RADIOGRAPH",
    )
    active = {"capture": capture, "bytes": raw}

    async def product_db():
        with Session(app.state.lab_sqlcipher_engine) as db:
            yield db
    app.dependency_overrides[database.get_db] = product_db
    app.include_router(
        imaging_acquisition_unassigned_v15.router,
        prefix="/api/imaging/acquisition",
    )
    url = "/api/imaging/acquisition/unassigned"
    expected_closed = {
        "schema_version": "dc06-product-unassigned-v1",
        "state": "NATIVE_IPC_NOT_CONNECTED",
        "read_only": True, "clinical_receipt_authorized": False,
        "patient_assigned": False, "captures": [],
    }
    bridge = LocalNativeCaptureBridge(
        tenant_id=claim.tenant, workstation_id=claim.station,
        inventory_reader=lambda: active["capture"],
        media_reader=lambda c: active["bytes"],
    )

    with _localhost_server(app) as origin, httpx.Client(
        base_url=origin, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station_token)
        assert http.get(url).status_code in (401, 403)
        assert http.get(url, headers=headers).json() == expected_closed
        app.state.dc06_unassigned_bridge = bridge
        http.cookies.set("dc_workstation", "unknown-workstation")
        assert http.get(url, headers=headers).status_code == 423
        http.cookies.set("dc_workstation", station_token)
        response = http.get(url, headers=headers)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        payload = response.json()
        assert payload == {
            **expected_closed, "state": "UNASSIGNED_INVENTORY_READ_ONLY",
            "captures": [{
                "id": capture.id, "digest": capture.digest,
                "size": capture.size, "mime": capture.mime,
                "category": capture.category,
            }],
        }
        assert not set(payload["captures"][0]).intersection({
            "patient", "staff", "filename", "appointment", "dossier",
        })
        assert bridge.read_verified_media(
            capture, tenant_id=claim.tenant,
            workstation_id=claim.station,
        ) == raw
        with pytest.raises(NativeInventoryDenied, match="TENANT_STATION"):
            bridge.inventory(tenant_id=claim.tenant + 1,
                             workstation_id=claim.station)
        with pytest.raises(NativeInventoryDenied, match="TENANT_STATION"):
            bridge.read_verified_media(
                capture, tenant_id=claim.tenant,
                workstation_id="not-this-station",
            )

        # An unassigned capture is not made into a patient ClinicalAsset,
        # and no raw media route is exposed by the product in B06-1.
        assert http.post(url, json={}, headers={
            k: v for k, v in headers.items() if k.lower() != "content-type"
        }).status_code == 405
        assert http.get(url + "/" + str(capture.id) + "/media",
                        headers=headers).status_code == 404
        assert _counts(engine) == (0, 0, 0)

        active["bytes"] = raw + b"modified"
        with pytest.raises(NativeInventoryDenied, match="INTEGRITY"):
            bridge.read_verified_media(
                capture, tenant_id=claim.tenant,
                workstation_id=claim.station,
            )
        active["bytes"] = raw
        active["capture"] = None
        with pytest.raises(NativeInventoryDenied, match="CAPTURE_CHANGED"):
            bridge.read_verified_media(
                capture, tenant_id=claim.tenant,
                workstation_id=claim.station,
            )
        assert http.get(url, headers=headers).json()["captures"] == []
        def refuse():
            raise NativeInventoryDenied("SERVICE_ACCESS_DENIED")
        app.state.dc06_unassigned_bridge = LocalNativeCaptureBridge(
            tenant_id=claim.tenant, workstation_id=claim.station,
            inventory_reader=refuse, media_reader=lambda c: raw,
        )
        assert http.get(url, headers=headers).status_code == 503
        assert _counts(engine) == (0, 0, 0)
    print("DC06_B06_PRODUCT_UNASSIGNED_JWT_STATION_NATIVE_BRIDGE_NO_PATIENT_PASS")


def test_b06_product_real_staff_preview_and_two_marker_transient_review_no_media_commit(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, _token, station, _media, _source, _collector, _item,
     raw, _private, _challenge, headers, app, _public) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    capture = UnassignedCapture(
        id=17, digest=hashlib.sha256(raw).hexdigest(),
        size=len(raw), mime="image/png", category="PHOTO",
    )
    actual = {"capture": capture, "media": raw}
    app.state.dc06_unassigned_bridge = LocalNativeCaptureBridge(
        tenant_id=claim.tenant, workstation_id=claim.station,
        inventory_reader=lambda: actual["capture"],
        media_reader=lambda _capture: actual["media"],
    )
    app.state.dc06_review_store = ProductReviewStore()

    async def product_db():
        with Session(app.state.lab_sqlcipher_engine) as db:
            yield db
    app.dependency_overrides[database.get_db] = product_db
    app.include_router(
        imaging_acquisition_unassigned_v15.router,
        prefix="/api/imaging/acquisition",
    )
    base = "/api/imaging/acquisition/review"
    start_data = {
        "capture_id": capture.id, "capture_digest": capture.digest,
        "selected_patient_id": claim.patient,
    }
    json_headers = {k: v for k, v in headers.items()
                    if k.lower() != "content-type"}

    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        assert http.post(base, json=start_data).status_code in (401, 403)
        assert _counts(engine) == (0, 0, 0)
        assert http.post(base, json={
            **start_data, "selected_patient_id": claim.patient + 500000,
        }, headers=json_headers).status_code in (403, 404, 409)
        assert http.post(base, json={
            **start_data, "capture_digest": "0" * 64,
        }, headers=json_headers).status_code == 409
        assert http.post(base, json={
            **start_data, "capture_id": 99999,
        }, headers=json_headers).status_code == 409
        # The real authentication dependency rejects missing Bearer with
        # 401 before this route's own stricter session guard can return 403.
        assert http.post(base, json=start_data, headers={
            k: v for k, v in json_headers.items()
            if k.lower() != "authorization"
        }).status_code in (401, 403)

        http.cookies.set("dc_workstation", "wrong-station-cookie")
        assert http.post(base, json=start_data, headers=json_headers).status_code == 423
        http.cookies.set("dc_workstation", station)

        begin = http.post(base, json=start_data, headers=json_headers)
        assert begin.status_code == 200, begin.text[:200]
        review = begin.json()
        assert review["clinical_receipt_authorized"] is False
        assert review["patient_id"] == claim.patient
        assert review["numero_dossier"] == "LAB-42"
        preview = "/api" + review["preview_url"]
        confirm = base + "/" + review["review_id"] + "/confirm"
        assert http.post(base, json=start_data, headers=json_headers).status_code == 409
        assert http.get(preview, headers=json_headers).status_code == 409
        assert http.get(preview, headers={
            **json_headers, "X-DC-Review-Challenge": "wrong-challenge",
        }).status_code == 409

        with Session(engine) as db:
            staff_email = db.get(models.User, claim.staff).email
        different_jwt = create_access_token({"sub": staff_email})
        assert http.get(preview, headers={
            **json_headers, "Authorization": "Bearer " + different_jwt,
            "X-DC-Review-Challenge": review["challenge"],
        }).status_code == 409

        good_preview = http.get(preview, headers={
            **json_headers, "X-DC-Review-Challenge": review["challenge"],
        })
        assert good_preview.status_code == 200
        assert good_preview.headers["cache-control"] == "no-store"
        assert good_preview.headers["content-type"].startswith("image/png")
        assert good_preview.content == raw

        valid = {
            "challenge": review["challenge"],
            "selected_patient_id": claim.patient,
            "dossier": review["numero_dossier"],
            "date_naissance": review["date_naissance"],
            "capture_digest": capture.digest,
            "explicit_confirmation": True,
        }
        for changed in (
            {"selected_patient_id": claim.patient + 1},
            {"dossier": "WRONG"},
            {"date_naissance": "1970-01-01"},
            {"capture_digest": "0" * 64},
            {"explicit_confirmation": False},
            {"challenge": "not-the-current-challenge"},
        ):
            bad = http.post(confirm, json={**valid, **changed},
                            headers=json_headers)
            assert bad.status_code in (409, 422), (changed, bad.status_code)
        assert _counts(engine) == (0, 0, 0)

        actual["media"] = raw + b"tampered"
        assert http.get(preview, headers={
            **json_headers, "X-DC-Review-Challenge": review["challenge"],
        }).status_code == 409
        assert http.post(confirm, json=valid, headers=json_headers).status_code == 409
        actual["media"] = raw
        accepted = http.post(confirm, json=valid, headers=json_headers)
        assert accepted.status_code == 200, accepted.text[:200]
        assert accepted.json() == {
            "status": "STAFF_REVIEW_VERIFIED_TRANSIENT_ONLY",
            "clinical_receipt_authorized": False,
            "patient_assigned": False, "media_published": False,
        }
        assert http.post(confirm, json=valid, headers=json_headers).status_code == 409
        assert http.get(preview, headers={
            **json_headers, "X-DC-Review-Challenge": review["challenge"],
        }).status_code == 409
        assert http.post(base, json=start_data, headers=json_headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)
    print("DC06_B06_PRODUCT_REAL_REVIEW_STAFF_SESSION_TWO_MARKERS_ONE_SHOT_NO_MEDIA_PASS")


def test_b06_product_review_cancel_releases_only_own_session(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, _token, station, _media, _source, _collector, _item,
     raw, _private, _challenge, headers, app, _pub) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    capture = UnassignedCapture(
        id=18, digest=hashlib.sha256(raw).hexdigest(),
        size=len(raw), mime="image/png", category="PHOTO",
    )
    app.state.dc06_unassigned_bridge = LocalNativeCaptureBridge(
        tenant_id=claim.tenant, workstation_id=claim.station,
        inventory_reader=lambda: capture, media_reader=lambda _capture: raw,
    )
    app.state.dc06_review_store = ProductReviewStore()
    async def product_db():
        with Session(app.state.lab_sqlcipher_engine) as db:
            yield db
    app.dependency_overrides[database.get_db] = product_db
    app.include_router(
        imaging_acquisition_unassigned_v15.router,
        prefix="/api/imaging/acquisition",
    )
    base = "/api/imaging/acquisition/review"
    payload = {
        "capture_id": capture.id, "capture_digest": capture.digest,
        "selected_patient_id": claim.patient,
    }
    json_headers = {k: v for k, v in headers.items()
                    if k.lower() != "content-type"}
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        first = http.post(base, json=payload, headers=json_headers)
        assert first.status_code == 200
        view = first.json()
        target = base + "/" + view["review_id"]
        assert http.delete(target, headers={
            **json_headers, "X-DC-Review-Challenge": "wrong",
        }).status_code == 409
        assert http.delete(target, headers={
            **json_headers, "X-DC-Review-Challenge": view["challenge"],
        }).status_code == 204
        assert http.delete(target, headers={
            **json_headers, "X-DC-Review-Challenge": view["challenge"],
        }).status_code == 409
        second = http.post(base, json=payload, headers=json_headers)
        assert second.status_code == 200
        assert second.json()["challenge"] != view["challenge"]
        assert _counts(engine) == (0, 0, 0)
    print("DC06_B06_PRODUCT_REVIEW_CANCEL_REPLAY_FAIL_CLOSED_PASS")
