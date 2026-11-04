"""B06 one-HEAD FUE-I: mounted product status stays closed while isolated
staff-authenticated review and encrypted signed receipt complete together.
Never a real scanner, production IPC adapter, human click or cabinet activation.
"""
import httpx
from sqlalchemy.orm import Session

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
    (engine, claim, _token, station, _media, source, collector, item,
     raw, _private, _challenge, headers, app, _pub) = _ctx(
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
        preview = http.get(candidate["preview_url"], headers=headers)
        assert preview.status_code == 200 and preview.content == raw
        assert preview.headers["cache-control"] == "no-store"

        confirm = review + "/confirm"
        bad = {**_input(candidate), "date_naissance": "1970-01-01"}
        assert http.post(confirm, json=bad, headers=json_headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)
        ok = http.post(confirm, json=_input(candidate), headers=json_headers)
        assert ok.status_code == 200 and ok.json()["clinical_receipt_authorized"] is False
        assert http.post(confirm, json=_input(candidate), headers=json_headers).status_code == 409

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
