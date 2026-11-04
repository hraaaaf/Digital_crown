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
from backend.routers import imaging_acquisition_status_v15
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
