"""LOT06 B01: real localhost HTTP/JWT/workstation and SQLCipher product GET FUE-I.

The native service, TPM, real scanner and product capture ingress are NOT tested.
"""
import httpx
from sqlalchemy.orm import Session
from backend import database
from backend.routers import imaging_acquisition_status_v15
from isolated_fue_lot06c.test_phase2_staff_review_media_sqlcipher_v15 import _ctx
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import (
    _counts, _localhost_server, synthetic_sqlcipher_bridge,
)


def test_product_status_auth_scoped_read_only_and_no_ingress(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, _token, station, _media, _source, _collector, _item,
     _raw, _private, _challenge, headers, app, _pub) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    async def product_db():
        with Session(app.state.lab_sqlcipher_engine) as db:
            yield db

    app.dependency_overrides[database.get_db] = product_db
    app.include_router(imaging_acquisition_status_v15.router, prefix="/api/patients")
    endpoint = f"/api/patients/{claim.patient}/acquisition/status"
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        assert http.get(endpoint).status_code in (401, 403)
        before = _counts(engine)
        result = http.get(endpoint, headers=headers)
        assert result.status_code == 200, result.text[:350]
        assert result.json() == {
            "schema_version": "dc06-product-status-v1",
            "state": "NATIVE_IPC_NOT_CONNECTED",
            "read_only": True, "acquisition_enabled": False,
            "clinical_receipt_authorized": False, "pending_captures": None,
            "reason": "WINDOWS_IPC_AND_TPM_PRODUCT_GATE_NOT_VERIFIED",
        }
        assert result.headers["cache-control"] == "no-store"
        assert http.get(f"/api/patients/{claim.patient + 500000}/acquisition/status",
                        headers=headers).status_code in (403, 404)
        json_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
        assert http.post(endpoint, json={"explicit_confirmation": True},
                         headers=json_headers).status_code == 405
        assert http.post(f"/api/patients/{claim.patient}/acquisition/confirm",
                         json={}, headers=json_headers).status_code == 404
        assert _counts(engine) == before == (0, 0, 0)
    print("LOT06_PRODUCT_STATUS_REAL_JWT_SQLCIPHER_READ_ONLY_NO_INGEST_PASS")
