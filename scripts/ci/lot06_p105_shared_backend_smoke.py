"""Offline real FastAPI smoke for P1-05 shared host startup (NOT a network FUE)."""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile
import threading
import uuid


def main():
    assert os.environ.get("ENVIRONMENT") == "test"
    assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
    assert os.environ.get("C05B03H_NETWORK_POLICY_APPROVED") != "true", "OFFLINE_SMOKE_ONLY"
    from scripts.ci.lot06_p105_private_shared_clinic import (
        TAG, backend_and_room, make_jpeg, enable_backend,
    )
    root = Path(tempfile.mkdtemp(prefix="p105-offline-real-app-smoke-"))
    os.environ["MEDIA_ROOT"] = str(root / "encrypted-media")
    os.environ["DATABASE_URL"] = "sqlite:///" + str(root / "shared-clinic.sqlite")
    os.environ["DC06H_TAIL_IP"] = "100.64.0.1"  # in-process ASGI scope only
    tracker = {
        "lock": threading.Lock(), "token": "p105-offline-smoke-only-" + uuid.uuid4().hex,
        "peers": {}, "start_at": None, "done": {},
    }
    app, engine, room = backend_and_room(root, tracker)
    assert len(room["users"]) == 2 and len(room["slot_refs"]) == 2
    enable_backend()
    from backend.services.patient_companion_remote_crypto import sign_and_encrypt, decrypt_and_verify
    from relay.contract import RelayInnerMessage
    import httpx

    async def request_checks():
        transport_a = httpx.ASGITransport(app=app, client=("100.64.0.2", 7001))
        transport_cam = httpx.ASGITransport(app=app, client=("100.64.0.3", 7002))
        base = "http://p105-in-process-not-a-network"
        headers_a = {"X-Lab-Token": tracker["token"], "X-Lab-Label": "patient-a"}
        headers_cam = {"X-Lab-Token": tracker["token"], "X-Lab-Label": "camera"}
        async with httpx.AsyncClient(transport=transport_a, base_url=base) as a:
            unauth = await a.get("/lab/status", headers={"X-Lab-Label": "patient-a"})
            assert unauth.status_code == 403, (unauth.status_code, unauth.text)
            join = await a.post("/lab/register", headers=headers_a,
                                json={"sha": os.environ["EXPECTED_SHA"],
                                      "run_id": os.environ["GITHUB_RUN_ID"],
                                      "runner": "smoke-client-a"})
            assert join.status_code == 200, join.text
            wrong = await a.get("/media/" + str(room["users"][0]["patient_id"]) + "/assets",
                                headers=headers_a)
            assert wrong.status_code == 403, wrong.text
            user = room["users"][0]
            msg = RelayInnerMessage(
                message_id=uuid.uuid4(), access_id=uuid.UUID(user["public_id"]),
                sent_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                idempotency_key=uuid.uuid4(), operation="message.send",
                payload={"client_message_id": str(uuid.uuid4()), "body": "offline real test app"},
            )
            blob = sign_and_encrypt(
                msg.model_dump(mode="json"),
                sender_signing_private_jwk=user["sign_private"],
                recipient_encryption_public_jwk=user["cabinet_enc_public"],
                sender_signing_kid=user["sign_kid"],
                recipient_encryption_kid=user["cabinet_enc_kid"],
            )
            send = await a.post(
                "/contexts/" + user["public_id"] + "/messages/remote-command",
                headers={**headers_a, "Authorization": user["authorization"]},
                json={"blob": blob},
            )
            assert send.status_code == 200, (send.status_code, send.text[:300])
            ack = decrypt_and_verify(
                send.json()["blob"],
                recipient_encryption_private_jwk=user["enc_private"],
                sender_signing_public_jwk=user["cabinet_sig_public"],
                expected_sender_signing_kid=user["cabinet_sig_kid"],
                expected_recipient_encryption_kid=user["enc_kid"],
            )
            assert ack["payload"]["status"] == "ACCEPTED", ack["payload"]

        async with httpx.AsyncClient(transport=transport_cam, base_url=base) as camera:
            join = await camera.post("/lab/register", headers=headers_cam,
                                     json={"sha": os.environ["EXPECTED_SHA"],
                                           "run_id": os.environ["GITHUB_RUN_ID"],
                                           "runner": "smoke-camera"})
            assert join.status_code == 200, join.text
            jpeg = make_jpeg(0)
            res = await camera.post(
                "/media/" + str(room["users"][0]["patient_id"]) + "/assets/import",
                headers={**headers_cam, "Authorization": room["staff_authorization"]},
                data={"asset_type": "PHOTO", "source_kind": "DEVICE_CAPTURE",
                      "source_ref": "P105-NET-SMOKE"},
                files={"file": ("smoke.jpeg", jpeg, "image/jpeg")},
            )
            assert res.status_code == 201, (res.status_code, res.text[:300])
            asset_id = res.json()["id"]
            read = await camera.get(
                "/media/" + str(room["users"][0]["patient_id"]) +
                "/assets/" + str(asset_id) + "/content",
                headers={**headers_cam, "Authorization": room["staff_authorization"]},
            )
            assert read.status_code == 200 and read.content == jpeg

    try:
        asyncio.run(request_checks())
        print("LOT06_P105_REAL_SHARED_BACKEND_IN_PROCESS_FUE_PASS_NETWORK_NOT_TESTED")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
