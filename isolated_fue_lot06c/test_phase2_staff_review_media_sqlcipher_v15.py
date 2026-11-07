"""Phase2 LAB: real SQLCipher/JWT review -> signed ClinicalAsset receipt, not clinic."""
from dataclasses import replace

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from backend import models
from isolated_fue_lot06c.phase2_staff_review_sqlcipher_lab import mount_lab_review, reviews, audit
from isolated_fue_lot06c import unassigned_device_manifest_lab as unassigned
from isolated_fue_lot06c.c05b03m_security_gate_lab import (
    BridgeRejected, identity as device_identity, review as device_review,
    sign_test_device_claim, verify_pending_device_capture_proof,
)
from isolated_fue_lot06c.test_c05b03m_device_human_authority_v15 import (
    _setup, _post, _counts, synthetic_sqlcipher_bridge, _localhost_server,
)
from tools.imaging_gateway import HotFolder


def _ctx(bridge, tmp_path, monkeypatch):
    monkeypatch.setenv("DC06_PHASE2_REVIEW_LAB", "1")
    values = _setup(
        bridge, tmp_path, media_authority=unassigned.TestOnlyUnassignedMediaAuthority(),
    )
    # Unlike the historical 03M fixture, this B06 upload must NOT send a
    # patient-/staff-bearing device signature as an HTTP authorization.
    values = (
        *values[:11],
        {key: value for key, value in values[11].items()
         if key.lower() != "x-dc-lab-device-proof"},
        *values[12:],
    )
    with values[0].begin() as conn:
        conn.execute(update(models.Patient.__table__).where(models.Patient.id == values[1].patient).values(numero_dossier='LAB-42'))
    # The device signs a capture manifest without patient or staff fields.
    # The human association is then established by separate review SQLCipher.
    # Fixture extracts only scanner fields. The constructor itself cannot
    # accept a clinical patient/user/appointment object.
    capture = values[1]
    device_manifest = unassigned.new_unassigned_manifest(
        tenant=capture.tenant, device=capture.device, station=capture.station,
        generation=capture.generation, capture=capture.capture,
        digest=capture.digest, byte_size=capture.byte_size,
    )
    device_signature = unassigned.sign_unassigned(device_manifest, values[9])
    with Session(values[0]) as db:
        unassigned.register_unassigned(db, device_manifest, device_signature)
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
        preview_endpoint = "/isolated/lot06-phase2/preview/" + claim.capture
        # Authenticated access alone does not unlock a capture preview.
        assert http.get(preview_endpoint, headers=headers).status_code == 409
        response = http.get(endpoint, headers=headers)
        assert response.status_code == 200, response.text[:200]
        view = response.json()
        assert view["lab_only"] is True
        assert view["clinical_receipt_authorized"] is False
        assert view["numero_dossier"] and view["date_naissance"]
        assert view["capture_digest"] == claim.digest
        assert http.get(view["preview_url"], headers=headers).status_code == 409
        assert http.get(view["preview_url"], headers={
            **headers, "X-DC-Review-Challenge": "wrong-review-challenge-000000000",
        }).status_code == 409
        preview = http.get(view["preview_url"], headers={
            **headers, "X-DC-Review-Challenge": view["challenge"],
        })
        assert preview.status_code == 200 and preview.content == raw
        assert preview.headers["cache-control"] == "no-store"

        confirm = endpoint + "/confirm"
        # Existing signed-media fixture sends application/octet-stream. That is
        # correct for binary media, wrong for JSON review (FastAPI 422 before
        # server confirmation logic). Preserve all auth headers, strip ONLY
        # media Content-Type so httpx sets application/json.
        review_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
        valid = _input(view)
        malformed_media_header = http.post(confirm, json=valid, headers=headers)
        assert malformed_media_header.status_code == 422
        with Session(engine) as db:
            assert db.execute(select(device_review.c.approved_at)).scalar_one() is None
            assert db.execute(select(reviews.c.consumed)).scalar_one() == 0
        for bad in (
            {"explicit_confirmation": False},
            {"selected_patient_id": view["patient_id"] + 1},
            {"dossier": "UNKNOWN"},
            {"date_naissance": "1980-01-01"},
            {"capture_digest": "0" * 64},
            {"challenge": "wrong-one-use-challenge-000000000000000"},
        ):
            result = http.post(confirm, json={**valid, **bad}, headers=review_headers)
            assert result.status_code == 409, (bad, result.status_code, result.text[:400])
        with Session(engine) as db:
            assert db.execute(select(device_review.c.approved_at)).scalar_one() is None
            assert db.execute(select(reviews.c.consumed)).scalar_one() == 0
        assert _counts(engine) == (0, 0, 0)

        newer = http.get(endpoint, headers=headers).json()
        assert newer["challenge"] != view["challenge"]
        assert http.post(confirm, json=valid, headers=review_headers).status_code == 409
        accepted = http.post(confirm, json=_input(newer), headers=review_headers)
        assert accepted.status_code == 200, accepted.text[:300]
        assert accepted.json()["clinical_receipt_authorized"] is False
        assert http.post(confirm, json=_input(newer), headers=review_headers).status_code == 409
        # Once the staff consumes the one-use challenge, even a still-valid
        # bearer session and its formerly valid challenge cannot fetch media.
        assert http.get(newer["preview_url"], headers={
            **headers, "X-DC-Review-Challenge": newer["challenge"],
        }).status_code == 409
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
        review_headers = {k: v for k, v in headers.items() if k.lower() != "content-type"}
        with engine.begin() as conn:
            conn.execute(update(reviews).values(expires_at=1))
        assert http.post(endpoint + "/confirm", json=_input(view),
                         headers=review_headers).status_code == 409
        assert http.get(view["preview_url"], headers={
            **headers, "X-DC-Review-Challenge": view["challenge"],
        }).status_code == 409
        assert _counts(engine) == (0, 0, 0)

        monkeypatch.setenv("ENVIRONMENT", "cabinet")
        assert http.get(endpoint, headers=headers).status_code in (401, 403)
        assert _counts(engine) == (0, 0, 0)
    print("LOT06_PHASE2_EXPIRED_REVIEW_AND_CABINET_DISABLE_PASS")


def test_phase2_preview_requires_independent_pinned_device_signature_and_staff_challenge(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    (engine, claim, _token, station, _media, _source, _collector, _item,
     _raw, private, challenge, headers, app, _public) = _ctx(
        synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
    )
    # The historical patient-/staff-bearing proof is generated only for
    # this independent negative oracle, never sent to the B06 upload server.
    proof = sign_test_device_claim(claim, challenge, private)
    assert len(proof) == 128
    assert "X-DC-Lab-Device-Proof" not in headers
    endpoint = "/isolated/lot06-phase2/review/" + claim.capture
    good_key = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    bad_key = Ed25519PrivateKey.generate().public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    ).hex()

    with Session(engine) as db:
        verify_pending_device_capture_proof(db, claim, proof)
        with pytest.raises(BridgeRejected, match="DEVICE_SIGNATURE_DENIED"):
            verify_pending_device_capture_proof(
                db, claim, sign_test_device_claim(
                    claim, challenge, Ed25519PrivateKey.generate(),
                ),
            )
        for wrong in (
            replace(claim, patient=claim.patient + 1),
            replace(claim, staff=claim.staff + 1),
            replace(claim, station=claim.station + "-other"),
            replace(claim, byte_size=claim.byte_size + 1),
            replace(claim, device=claim.device + "-other"),
            replace(claim, capture=claim.capture + "-other"),
            replace(claim, digest="0" * 64),
            replace(claim, generation=claim.generation + 1),
        ):
            with pytest.raises(BridgeRejected):
                verify_pending_device_capture_proof(db, wrong, proof)
    assert _counts(engine) == (0, 0, 0)

    with _localhost_server(app) as url, httpx.Client(
        base_url=url, trust_env=False, timeout=20,
    ) as http:
        http.cookies.set("dc_workstation", station)
        view = http.get(endpoint, headers=headers)
        assert view.status_code == 200
        data = view.json()
        preview_headers = {
            **headers, "X-DC-Review-Challenge": data["challenge"],
        }
        assert http.get(data["preview_url"], headers=preview_headers).status_code == 200

        # Simulate pinned device key replacement while review is still open.
        with engine.begin() as conn:
            conn.execute(update(device_identity).values(public_key_hex=bad_key))
        assert http.get(data["preview_url"], headers=preview_headers).status_code == 409
        assert http.get(endpoint, headers=headers).status_code == 409
        confirm_headers = {k: v for k, v in headers.items()
                           if k.lower() != "content-type"}
        assert http.post(endpoint + "/confirm", json=_input(data),
                         headers=confirm_headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)

        with engine.begin() as conn:
            conn.execute(update(device_identity).values(public_key_hex=good_key))
            conn.execute(update(device_identity).values(generation=claim.generation + 1))
        assert http.get(data["preview_url"], headers=preview_headers).status_code == 409
        with engine.begin() as conn:
            conn.execute(update(device_identity).values(generation=claim.generation))
            conn.execute(update(device_identity).values(active=0))
        assert http.get(data["preview_url"], headers=preview_headers).status_code == 409
        assert _counts(engine) == (0, 0, 0)

    print("DC06_B06_PINNED_ED25519_DEVICE_AND_STAFF_PREVIEW_REVOKE_PASS")
