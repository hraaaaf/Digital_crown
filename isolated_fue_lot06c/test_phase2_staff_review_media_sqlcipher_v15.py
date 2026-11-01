"""Phase2 LAB: real SQLCipher/JWT review -> signed ClinicalAsset receipt, not clinic."""
import httpx
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from backend import models
from isolated_fue_lot06c.phase2_staff_review_sqlcipher_lab import mount_lab_review, reviews, audit
from isolated_fue_lot06c.c05b03m_security_gate_lab import review as device_review
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import (
    _setup, _post, _counts, synthetic_sqlcipher_bridge, _localhost_server,
)
from tools.imaging_gateway import HotFolder


def _ctx(bridge, tmp_path, monkeypatch):
    monkeypatch.setenv("DC06_PHASE2_REVIEW_LAB", "1")
    values = _setup(bridge, tmp_path)
    with values[0].begin() as conn:
        conn.execute(update(models.Patient.__table__).where(models.Patient.id == values[1].patient).values(numero_dossier='LAB-42'))
    mount_lab_review(values[12], claim=values[1], validated_media=values[8])
    return values


def _input(view):
    return {
        "challenge": view["challenge"],
        "selected_patient_id": view["patient_id"],
        "dossier": view["numero_dossier"],
        "date_naissance": view["date_naissance"],
        "capture_digest": view["capture_digest"],
        "explicit_confirmation": True,
    }


def test_phase2_authentic_review_and_encrypted_signed_ack_replay(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, token, station, media, source, collector, item,
     raw, private, challenge, headers, app, public_key) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    endpoint = "/isolated/lot06-phase2/review/" + claim.capture
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, timeout=20, trust_env=False,
    ) as http:
        http.cookies.set("dc_workstation", station)
        assert _post(http, claim, raw, headers).status_code == 409
        assert http.get(endpoint).status_code in (401, 403)
        response = http.get(endpoint, headers=headers)
        assert response.status_code == 200, response.text[:200]
        view = response.json()
        assert view["lab_only"] is True
        assert view["clinical_receipt_authorized"] is False
        assert view["numero_dossier"] and view["date_naissance"]
        assert view["capture_digest"] == claim.digest
        preview = http.get(view["preview_url"], headers=headers)
        assert preview.status_code == 200 and preview.content == raw
        assert preview.headers["cache-control"] == "no-store"

        confirm = endpoint + "/confirm"
        valid = _input(view)
        for bad in (
            {"explicit_confirmation": False},
            {"selected_patient_id": view["patient_id"] + 1},
            {"dossier": "UNKNOWN"},
            {"date_naissance": "1980-01-01"},
            {"capture_digest": "0" * 64},
            {"challenge": "wrong-one-use-challenge-000000000000000"},
        ):
            result = http.post(confirm, json={**valid, **bad}, headers=headers)
            assert result.status_code == 409, (bad, result.status_code)
        with Session(engine) as db:
            assert db.execute(select(device_review.c.approved_at)).scalar_one() is None
            assert db.execute(select(reviews.c.consumed)).scalar_one() == 0
        assert _counts(engine) == (0, 0, 0)

        newer = http.get(endpoint, headers=headers).json()
        assert newer["challenge"] != view["challenge"]
        assert http.post(confirm, json=valid, headers=headers).status_code == 409
        accepted = http.post(confirm, json=_input(newer), headers=headers)
        assert accepted.status_code == 200, accepted.text[:300]
        assert accepted.json()["clinical_receipt_authorized"] is False
        assert http.post(confirm, json=_input(newer), headers=headers).status_code == 409
        with Session(engine) as db:
            assert db.execute(select(reviews.c.consumed)).scalar_one() == 1
            assert db.execute(select(audit.c.event)).scalar_one() == "LAB_HTTP_EXPLICIT_STAFF_CONFIRM"
        assert _counts(engine) == (0, 0, 0)

        first = _post(http, claim, raw, headers)
        assert first.status_code == 200, first.text[:300]
        receipt = first.json()
        assert receipt["clinical_receipt_authorized"] is False
        assert _counts(engine) == (1, 1, 1)
        restarted = HotFolder(collector.config)
        assert restarted.items()[0]["state"] == "PENDING_CONFIRMATION"
        again = _post(http, claim, restarted.read_verified(item["id"]), headers)
        assert again.status_code == 200 and again.json() == receipt
        assert _counts(engine) == (1, 1, 1)
    assert source.read_bytes() == raw
    print("LOT06_PHASE2_REAL_SQLCIPHER_REVIEW_DUAL_ID_SIGNED_MEDIA_IDEMPOTENT_PASS")


def test_phase2_expiry_revocation_and_cabinet_kill_switch(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, token, station, media, source, collector, item,
     raw, private, challenge, headers, app, public_key) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    endpoint = "/isolated/lot06-phase2/review/" + claim.capture
    with _localhost_server(app) as url, httpx.Client(
        base_url=url, timeout=20, trust_env=False,
    ) as http:
        http.cookies.set("dc_workstation", station)
        view = http.get(endpoint, headers=headers).json()
        with engine.begin() as conn:
            conn.execute(update(reviews).values(expires_at=1))
        assert http.post(endpoint + "/confirm", json=_input(view),
                         headers=headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)

        monkeypatch.setenv("ENVIRONMENT", "cabinet")
        assert http.get(endpoint, headers=headers).status_code in (401, 403)
        assert _counts(engine) == (0, 0, 0)
    print("LOT06_PHASE2_EXPIRED_REVIEW_AND_CABINET_DISABLE_PASS")
