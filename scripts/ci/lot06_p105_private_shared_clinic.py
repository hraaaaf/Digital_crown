"""LOT06 P1-05 private 5-VM FUE: 1 real FastAPI/SQLite/Media receiver + 4 remote peers.

Test only. Does not activate Tailnet, change repository network policy, use
patient data, deploy a clinical backend, or issue a production certification.
Five distinct github-hosted VMs and Tailscale IPs are required. Test-only JWK,
JWT and shared lab token exist only in a one-day GitHub artifact for this run.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import hashlib
from io import BytesIO
import ipaddress
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
import zipfile

NETWORK = ipaddress.ip_network("100.64.0.0/10")
LABELS = ("patient-a", "patient-b", "staff", "camera")
PORT = 7079
ROUNDS = 8
TAG = "DC06_P105_5_VM_ONE_REAL_BACKEND_SYNTHETIC_V1"


def check(value, message):
    if not value:
        raise AssertionError(message)


def valid_ip(raw):
    try:
        return ipaddress.ip_address(str(raw)) in NETWORK
    except ValueError:
        return False


def guard(*, require_network=True):
    check(os.getenv("ENVIRONMENT") == "test", "TEST_ENVIRONMENT_REQUIRED")
    check(os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true", "ISOLATED_RUNTIME_REQUIRED")
    check(os.getenv("GITHUB_ACTIONS") == "true", "GITHUB_RUNNER_REQUIRED")
    check(os.getenv("RUNNER_ENVIRONMENT") == "github-hosted", "GITHUB_HOSTED_VM_REQUIRED")
    check(os.getenv("EXPECTED_SHA") and os.environ["EXPECTED_SHA"] == os.getenv("GITHUB_SHA_EXACT"),
          "COMMIT_SHA_NOT_PINNED")
    if require_network:
        check(os.getenv("C05B03H_NETWORK_POLICY_APPROVED") == "true", "NETWORK_APPROVAL_NOT_GRANTED")
        check(valid_ip(os.getenv("DC06H_TAIL_IP", "")), "PRIVATE_TAILNET_IP_REQUIRED")
    return os.getenv("DC06H_TAIL_IP", "")


def enable_backend():
    # Reuse exact real backend models/routes on five real VMs, without the
    # incidental eager-import side effects in backend.routers/__init__.py.
    import sys, types
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    p = types.ModuleType("backend.routers")
    p.__path__ = [str(root / "backend" / "routers")]
    sys.modules["backend.routers"] = p


def make_jpeg(index):
    from PIL import Image
    img = Image.new("RGB", (40, 30), ((40 + 9*index) % 255, 90, 150))
    out = BytesIO()
    img.save(out, "JPEG")
    return out.getvalue()


def backend_and_room(root, tracker):
    enable_backend()
    from functools import partial
    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.responses import JSONResponse
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import NullPool
    from backend import models, database
    from backend.models_patient_companion import PatientCompanionIdentity, PatientCompanionAccess
    from backend.routers import patient_companion_agenda, patient_companion_messages, media_core
    from backend.services.patient_companion_remote_crypto import generate_p256_keypair
    from backend.services.patient_companion_remote_keys import enroll_remote_keyset
    from backend.services.patient_companion_remote_worker import process_remote_envelope
    from backend.routers.patient_companion_common import create_patient_device_token
    from backend.security import create_access_token
    engine = create_engine("sqlite:///" + str(root / "shared-clinic.sqlite"),
                           poolclass=NullPool, connect_args={"timeout": 20, "check_same_thread": False})
    @event.listens_for(engine, "connect")
    def _connect(connection, _record):
        connection.execute("PRAGMA busy_timeout=20000")
        connection.execute("PRAGMA foreign_keys=ON")
    with engine.connect() as db:
        check(db.exec_driver_sql("PRAGMA journal_mode=WAL").scalar().lower() == "wal",
              "SHARED_BACKEND_WAL_REQUIRED")
    models.Base.metadata.create_all(bind=engine)
    users = []
    with Session(engine) as db:
        owner = models.User(email="dc06p105-owner@example.invalid",
                            hashed_password="synthetic-no-login", role="DENTISTE",
                            nom_complet="P105 Synthetic Doctor", is_active=True, is_licensed=True)
        db.add(owner)
        db.flush()
        for index in range(2):
            patient = models.Patient(
                numero_dossier="P105-NET-" + str(index), nom="Synthetic",
                prenom="A" if index == 0 else "B",
                date_naissance=datetime(2010, 1, 1), sexe="F", employer_id=owner.id)
            identity = PatientCompanionIdentity(
                provider="local_bridge", subject="p105:" + str(uuid.uuid4()))
            db.add_all([patient, identity])
            db.flush()
            access = PatientCompanionAccess(
                identity_id=identity.id, employer_id=owner.id,
                patient_id=patient.id, relationship_type="SELF")
            db.add(access)
            db.flush()
            sign_private, sign_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
            enc_private, enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
            keyset, cabinet_sig, cabinet_enc = enroll_remote_keyset(
                db, access=access,
                patient_signing_kid=sign_public["kid"],
                patient_signing_public_jwk=sign_public,
                patient_encryption_kid=enc_public["kid"],
                patient_encryption_public_jwk=enc_public,
                protect=lambda raw: b"DC06_P105_SYNTHETIC_ONLY:" + raw)
            db.flush()
            users.append({
                "patient_id": patient.id, "access_pk": access.id,
                "public_id": access.public_id,
                "authorization": "Bearer " + create_patient_device_token(identity, access),
                "sign_private": sign_private, "sign_kid": keyset.patient_signing_kid,
                "enc_private": enc_private, "enc_kid": keyset.patient_encryption_kid,
                "cabinet_enc_public": json.loads(cabinet_enc.public_jwk_json),
                "cabinet_enc_kid": keyset.cabinet_encryption_kid,
                "cabinet_sig_public": json.loads(cabinet_sig.public_jwk_json),
                "cabinet_sig_kid": keyset.cabinet_signing_kid,
            })
        from backend.services.patient_companion_agenda import issue_slots
        refs = []
        for user in users:
            access = db.get(PatientCompanionAccess, user["access_pk"])
            rows = issue_slots(db, access=access, starts=[datetime(2033, 1, 15, 10)],
                               duration_minutes=30, practitioner_id=owner.id)
            check(len(rows) == 1, "SYNTHETIC_SLOT_MISSING")
            refs.append(rows[0]["slot_ref"])
        staff_token = "Bearer " + create_access_token({"sub": owner.email})
        owner_id = owner.id
        db.commit()

    app = FastAPI(title="P105-ONLY-PRIVATE-SHARED-BACKEND")
    app.include_router(patient_companion_agenda.router)
    app.include_router(patient_companion_messages.router)
    app.include_router(media_core.router, prefix="/media")

    def get_test_db():
        with Session(engine) as db:
            yield db
    # Replace only the disposable database dependency; not real JWT, JWE,
    # access control, booking, messaging, Media Core or SQL write locks.
    app.dependency_overrides[database.get_db] = get_test_db
    for routes in (patient_companion_agenda, patient_companion_messages):
        routes.process_remote_envelope = partial(
            process_remote_envelope,
            unprotect=lambda raw: (
                raw[len(b"DC06_P105_SYNTHETIC_ONLY:"):]
                if raw.startswith(b"DC06_P105_SYNTHETIC_ONLY:")
                else (_ for _ in ()).throw(ValueError("test OS-bound key mismatch"))
            ),
        )

    @app.middleware("http")
    async def lab_scope(request: Request, call_next):
        # Middleware rejections must be 403, never an uncaught exception/500.
        if not valid_ip(request.client.host if request.client else ""):
            return JSONResponse({"detail": "Private Tailnet peer required"}, status_code=403)
        token = request.headers.get("X-Lab-Token", "")
        if not secrets.compare_digest(token, tracker["token"]):
            return JSONResponse({"detail": "Invalid lab credential"}, status_code=403)
        label = request.headers.get("X-Lab-Label", "")
        if label not in LABELS:
            return JSONResponse({"detail": "Unknown remote lab role"}, status_code=403)
        path = request.url.path
        if (path.startswith("/media/") and label != "camera"
            or path.startswith("/admin/") and label != "staff"
            or path.startswith("/contexts/") and label not in ("patient-a", "patient-b")):
            return JSONResponse({"detail": "Wrong lab role for real product API"}, status_code=403)
        ip = request.client.host
        with tracker["lock"]:
            known = tracker["peers"].get(label)
            if path != "/lab/register" and (known is None or known["ip"] != ip):
                return JSONResponse({"detail": "Unregistered network client"}, status_code=403)
        return await call_next(request)

    @app.post("/lab/register")
    def register(data: dict, request: Request, x_lab_label: str = Header(...)):
        check(data.get("sha") == os.environ["EXPECTED_SHA"], "REPLAYED_SHA")
        check(data.get("run_id") == os.environ["GITHUB_RUN_ID"], "REPLAYED_RUN")
        runner = str(data.get("runner", ""))
        check(runner and len(runner) < 160, "MISSING_DISTINCT_RUNNER")
        peer_ip = request.client.host
        check(valid_ip(peer_ip) and peer_ip != os.environ["DC06H_TAIL_IP"], "NO_PRIVATE_REMOTE_VM")
        with tracker["lock"]:
            existing = tracker["peers"].get(x_lab_label)
            if existing:
                check(existing == {"ip": peer_ip, "runner": runner}, "REASSIGNED_REMOTE_ROLE")
            else:
                check(peer_ip not in [v["ip"] for v in tracker["peers"].values()], "SHARED_REMOTE_IP")
                check(runner not in [v["runner"] for v in tracker["peers"].values()], "SHARED_RUNNER_ID")
                tracker["peers"][x_lab_label] = {"ip": peer_ip, "runner": runner}
            if len(tracker["peers"]) == 4 and not tracker["start_at"]:
                tracker["start_at"] = time.time() + 6
        return {"registered": True}

    @app.get("/lab/status")
    def status():
        with tracker["lock"]:
            return {"joined": len(tracker["peers"]), "start_at": tracker["start_at"],
                    "done": sorted(tracker["done"])}

    @app.post("/lab/done")
    def done(data: dict, x_lab_label: str = Header(...)):
        check(data.get("sha") == os.environ["EXPECTED_SHA"], "WRONG_SHA_IN_PROOF")
        check(data.get("run_id") == os.environ["GITHUB_RUN_ID"], "WRONG_RUN_IN_PROOF")
        check(data.get("label") == x_lab_label, "WRONG_ROLE_IN_PROOF")
        with tracker["lock"]:
            check(x_lab_label not in tracker["done"], "DUPLICATED_PROOF")
            tracker["done"][x_lab_label] = {
                "kind": str(data.get("kind")), "count": int(data.get("count", -1)),
                "p95_ms": float(data.get("p95_ms", 0)),
            }
        return {"ok": True}

    room = {
        "kind": TAG, "run_id": os.environ["GITHUB_RUN_ID"], "sha": os.environ["EXPECTED_SHA"],
        "ip": os.environ["DC06H_TAIL_IP"], "port": PORT,
        "token": tracker["token"], "staff_authorization": staff_token,
        "owner_id": owner_id, "users": users, "slot_refs": refs,
    }
    return app, engine, room


def assert_server_proof(engine, room, tracker):
    enable_backend()
    from sqlalchemy.orm import Session
    from backend import models
    from backend.models_media_core import ClinicalAsset
    from backend.models_patient_companion import PatientCompanionMessage, PatientCompanionRemoteReceipt
    from backend.services.clinical_asset_storage import read_clinical_asset_bytes
    engine.dispose()
    with tracker["lock"]:
        peers = dict(tracker["peers"])
        done = dict(tracker["done"])
    check(set(peers) == set(LABELS) and set(done) == set(LABELS), "INCOMPLETE_FIVE_VM_TOPOLOGY")
    check(len({x["ip"] for x in peers.values()}) == 4, "REMOTE_PEER_IP_DUPLICATED")
    check(len({x["runner"] for x in peers.values()}) == 4, "REMOTE_RUNNER_ID_DUPLICATED")
    check(os.environ["RUNNER_NAME"] not in {x["runner"] for x in peers.values()}, "SERVER_RUNNER_NOT_DISTINCT")
    check(done["patient-a"]["kind"] == "patient" and done["patient-a"]["count"] == ROUNDS + 1,
          "PATIENT_A_MESSAGES_OR_BOOKING_NOT_DONE")
    check(done["patient-b"]["kind"] == "patient" and done["patient-b"]["count"] == ROUNDS + 1,
          "PATIENT_B_MESSAGES_OR_BOOKING_NOT_DONE")
    check(done["staff"]["kind"] == "staff" and done["staff"]["count"] == ROUNDS * 2, "STAFF_READ_INCOMPLETE")
    check(done["camera"]["kind"] == "camera" and done["camera"]["count"] == ROUNDS, "MEDIA_CAPTURE_INCOMPLETE")
    users = room["users"]
    with Session(engine) as db:
        from datetime import datetime
        appointments = db.query(models.Appointment).filter(
            models.Appointment.employer_id == room["owner_id"],
            models.Appointment.datetime_start == datetime(2033, 1, 15, 10)).all()
        check(len(appointments) == 1, "RACE_DOUBLE_BOOKING")
        check(appointments[0].patient_id in [u["patient_id"] for u in users], "RACE_WRONG_PATIENT")
        counts = []
        for u in users:
            count = db.query(PatientCompanionMessage).filter(
                PatientCompanionMessage.access_id == u["access_pk"],
                PatientCompanionMessage.patient_id == u["patient_id"]).count()
            counts.append(count)
            check(count == ROUNDS, "MESSAGE_MISSING_OR_DUPLICATED")
        receipts = db.query(PatientCompanionRemoteReceipt).count()
        check(receipts == 2 * (ROUNDS + 1), "GHOST_OR_MISSING_RECEIPT")
        media = db.query(ClinicalAsset).filter(
            ClinicalAsset.source_ref.like("P105-NET-%"),
            ClinicalAsset.employer_id == room["owner_id"],
            ClinicalAsset.source_kind == "DEVICE_CAPTURE").all()
        check(len(media) == ROUNDS, "MEDIA_MISSING_OR_DUPLICATED")
        check(all(a.patient_id == users[0]["patient_id"] for a in media), "MEDIA_CROSS_PATIENT")
        for asset in media:
            image = read_clinical_asset_bytes(
                db, employer_id=room["owner_id"], patient_id=users[0]["patient_id"],
                asset_id=asset.id)
            check(image.startswith(b"\xff\xd8") and len(image) > 300, "MEDIA_CRYPTO_INVALID")
        proof = {
            "kind": TAG, "sha": room["sha"], "run_id": room["run_id"],
            "server_runner": os.environ["RUNNER_NAME"],
            "server_ip": room["ip"], "peers": peers, "clients": done,
            "shared_backend_real": True, "distinct_github_vms": 5,
            "tailnet_only": True, "patient_data_real": False,
            "appointments": len(appointments), "messages": sum(counts),
            "receipts": receipts, "encrypted_media": len(media),
            "fail_closed": True, "product_ready": False,
        }
    Path("p105-server-proof.json").write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n")
    print("LOT06_P1_05_TRUE_FIVE_VM_SHARED_REAL_BACKEND_PASS", {
        "appointments": proof["appointments"], "messages": proof["messages"],
        "receipts": proof["receipts"], "encrypted_media": proof["encrypted_media"],
        "distinct_vm": proof["distinct_github_vms"]}, flush=True)


def run_server():
    guard()
    root = Path(tempfile.mkdtemp(prefix="dc06-p105-private-shared-"))
    os.environ["MEDIA_ROOT"] = str(root / "media")
    os.environ["DATABASE_URL"] = "sqlite:///" + str(root / "shared-clinic.sqlite")
    tracker = {"lock": threading.Lock(), "token": secrets.token_urlsafe(40),
               "peers": {}, "start_at": None, "done": {}}
    try:
        app, engine, room = backend_and_room(root, tracker)
        import uvicorn
        server = uvicorn.Server(uvicorn.Config(
            app, host=room["ip"], port=PORT, log_level="warning",
            proxy_headers=False, access_log=False))
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        limit = time.monotonic() + 30
        while not server.started and time.monotonic() < limit:
            check(thread.is_alive(), "PRIVATE_BACKEND_BOOT_FAILED")
            time.sleep(0.1)
        check(server.started, "PRIVATE_BACKEND_TIMEOUT")
        room_path = Path("p105-private-room.json")
        room_path.write_text(json.dumps(room))
        os.chmod(room_path, 0o600)
        print("LOT06_P1_05_PRIVATE_REAL_BACKEND_READY", flush=True)
        end = time.monotonic() + 1020
        while time.monotonic() < end:
            with tracker["lock"]:
                finished = len(tracker["done"]) == 4
            if finished:
                break
            check(thread.is_alive(), "SHARED_BACKEND_DIED")
            time.sleep(0.4)
        else:
            raise AssertionError("FIVE_VM_NETWORK_CLIENTS_TIMED_OUT")
        assert_server_proof(engine, room, tracker)
    finally:
        if "server" in locals():
            server.should_exit = True
        if "thread" in locals():
            thread.join(timeout=10)
        if "engine" in locals():
            engine.dispose()
        Path("p105-private-room.json").unlink(missing_ok=True)
        shutil.rmtree(root, ignore_errors=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_room():
    token = os.environ.get("GH_API_TOKEN", "")
    check(len(token) > 10, "GITHUB_READ_TOKEN_REQUIRED")
    base = ("https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"])
    expected = "lot06-p105-private-room-" + os.environ["GITHUB_RUN_ID"]
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    no_redirects = urllib.request.build_opener(NoRedirect())
    until = time.monotonic() + 820
    while time.monotonic() < until:
        try:
            req = urllib.request.Request(
                base + "/actions/runs/" + os.environ["GITHUB_RUN_ID"] + "/artifacts?per_page=100",
                headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                items = json.load(response)["artifacts"]
            artifact = next((x for x in items if x["name"] == expected and not x["expired"]), None)
            if artifact is None:
                time.sleep(4)
                continue
            req = urllib.request.Request(base + "/actions/artifacts/" + str(artifact["id"]) + "/zip",
                                         headers=headers)
            try:
                with no_redirects.open(req, timeout=15) as response:
                    archive = response.read()
            except urllib.error.HTTPError as error:
                check(error.code in (301, 302, 303, 307, 308), "UNEXPECTED_ARTIFACT_HTTP")
                signed = error.headers.get("Location", "")
                check(signed.startswith("https://") and "api.github.com" not in signed,
                      "BAD_SIGNED_ARTIFACT_REDIRECT")
                # Signed storage URL: never forward GitHub Authorization headers.
                with urllib.request.urlopen(signed, timeout=30) as response:
                    archive = response.read()
            with zipfile.ZipFile(BytesIO(archive)) as z:
                room = json.loads(z.read("p105-private-room.json"))
            check(room["kind"] == TAG and room["run_id"] == os.environ["GITHUB_RUN_ID"],
                  "FOREIGN_RUN_RENDEZVOUS")
            check(room["sha"] == os.environ["EXPECTED_SHA"] and valid_ip(room["ip"]),
                  "UNTRUSTED_PRIVATE_ROOM")
            check(len(room["token"]) > 45, "WEAK_LAB_AUTH_TOKEN")
            return room
        except (urllib.error.URLError, TimeoutError, KeyError, zipfile.BadZipFile) as error:
            time.sleep(4)
    raise AssertionError("SHARED_BACKEND_RENDEZVOUS_UNAVAILABLE")


def request(room, label, method, path, *, data=None, form=None, headers=None):
    import requests
    url = "http://" + room["ip"] + ":" + str(room["port"]) + path
    h = {"X-Lab-Token": room["token"], "X-Lab-Label": label,
         "Cache-Control": "no-store"}
    h.update(headers or {})
    options = {"headers": h, "timeout": 25, "allow_redirects": False}
    if form is not None:
        options["data"] = form[0]
        options["files"] = form[1]
    elif data is not None:
        options["json"] = data
    return requests.request(method, url, **options)


def command(room, label, user, op, payload, *, key=None):
    enable_backend()
    from relay.contract import RelayInnerMessage
    from backend.services.patient_companion_remote_crypto import sign_and_encrypt, decrypt_and_verify
    message = RelayInnerMessage(
        message_id=uuid.uuid4(), access_id=uuid.UUID(user["public_id"]),
        sent_at=datetime.now().astimezone(), expires_at=datetime.now().astimezone() + timedelta(minutes=10),
        idempotency_key=key or uuid.uuid4(), operation=op, payload=payload,
    )
    blob = sign_and_encrypt(
        message.model_dump(mode="json"),
        sender_signing_private_jwk=user["sign_private"],
        recipient_encryption_public_jwk=user["cabinet_enc_public"],
        sender_signing_kid=user["sign_kid"],
        recipient_encryption_kid=user["cabinet_enc_kid"])
    endpoint = "messages" if op.startswith("message.") else "agenda"
    resp = request(
        room, label, "POST", "/contexts/" + user["public_id"] +
        "/" + endpoint + "/remote-command", data={"blob": blob},
        headers={"Authorization": user["authorization"]})
    check(resp.status_code == 200, "REAL_REMOTE_HTTP_" + str(resp.status_code) + "_" + resp.text[:180])
    ack = decrypt_and_verify(
        resp.json()["blob"],
        recipient_encryption_private_jwk=user["enc_private"],
        sender_signing_public_jwk=user["cabinet_sig_public"],
        expected_sender_signing_kid=user["cabinet_sig_kid"],
        expected_recipient_encryption_kid=user["enc_kid"])
    check(ack["operation"] == "command.result", "UNSIGNED_ACK_REJECTED")
    return ack["payload"]


def wait_start(room, label):
    until = time.monotonic() + 360
    while time.monotonic() < until:
        resp = request(room, label, "GET", "/lab/status")
        if resp.status_code == 200 and resp.json()["start_at"]:
            start = float(resp.json()["start_at"])
            while time.time() < start:
                time.sleep(0.07)
            return
        time.sleep(0.2)
    raise AssertionError("FIVE_VM_START_BARRIER_TIMEOUT")


def wait_peers(room, label, required):
    until = time.monotonic() + 420
    while time.monotonic() < until:
        resp = request(room, label, "GET", "/lab/status")
        if resp.status_code == 200 and set(required).issubset(resp.json()["done"]):
            return
        time.sleep(0.35)
    raise AssertionError("REMOTE_STAFF_WAIT_FOR_MESSAGES_OR_MEDIA_TIMEOUT")


def percentile(samples, p):
    rows = sorted(samples)
    return round(rows[max(0, (len(rows)*p + 99)//100 - 1)], 2)


def run_client(label):
    guard()
    check(label in LABELS, "UNSUPPORTED_FIVE_VM_ROLE")
    room = get_room()
    start = time.monotonic()
    join = request(room, label, "POST", "/lab/register",
                   data={"sha": room["sha"], "run_id": room["run_id"],
                         "runner": os.environ["RUNNER_NAME"]})
    check(join.status_code == 200 and join.json()["registered"], "PRIVATE_VM_REGISTER_FAILED")
    wait_start(room, label)
    samples = []
    if label in ("patient-a", "patient-b"):
        index = 0 if label == "patient-a" else 1
        user = room["users"][index]
        wrong = room["users"][1-index]
        denial = request(room, label, "GET", "/contexts/" + wrong["public_id"] + "/agenda",
                         headers={"Authorization": user["authorization"]})
        check(denial.status_code == 404, "PATIENT_CROSS_TENANT_READ_ALLOWED")
        for step in range(ROUNDS):
            t0 = time.monotonic()
            payload = {"client_message_id": str(uuid.uuid4()),
                       "body": f"p105-{label}-round-{step}"}
            intent = uuid.uuid4()
            ack = command(room, label, user, "message.send", payload, key=intent)
            check(ack["status"] == "ACCEPTED", "MESSAGE_NOT_DURABLE")
            if step == 0:
                replay = command(room, label, user, "message.send", payload, key=intent)
                check(replay["status"] == "ACCEPTED"
                      and replay["result"] == ack["result"], "LOST_ACK_RETRY_DUPLICATED_MESSAGE")
            samples.append((time.monotonic()-t0)*1000)
        t0 = time.monotonic()
        book = command(room, label, user, "agenda.create",
                       {"slot_ref": room["slot_refs"][index]})
        check(book["status"] in ("ACCEPTED", "REJECTED"), "INVALID_BOOKING_ACK")
        samples.append((time.monotonic()-t0)*1000)
        kind, count = "patient", ROUNDS + 1
    elif label == "camera":
        for step in range(ROUNDS):
            jpeg = make_jpeg(step)
            t0 = time.monotonic()
            resp = request(room, label, "POST",
                           "/media/" + str(room["users"][0]["patient_id"]) + "/assets/import",
                           form=({"asset_type": "PHOTO", "source_kind": "DEVICE_CAPTURE",
                                  "source_ref": f"P105-NET-{step}"},
                                 {"file": ("p105-synthetic.jpeg", jpeg, "image/jpeg")}),
                           headers={"Authorization": room["staff_authorization"]})
            check(resp.status_code == 201, "CLINICAL_MEDIA_STORE_FAILED_" + str(resp.status_code) +
                  "_" + resp.text[:150])
            asset_id = resp.json()["id"]
            verify = request(room, label, "GET",
                             "/media/" + str(room["users"][0]["patient_id"]) +
                             "/assets/" + str(asset_id) + "/content",
                             headers={"Authorization": room["staff_authorization"]})
            check(verify.status_code == 200 and hashlib.sha256(verify.content).digest() ==
                  hashlib.sha256(jpeg).digest(), "REMOTE_ENCRYPTED_MEDIA_READ_MISMATCH")
            samples.append((time.monotonic()-t0)*1000)
        kind, count = "camera", ROUNDS
    else:
        wait_peers(room, label, ("patient-a", "patient-b", "camera"))
        count = 0
        for user in room["users"]:
            t0 = time.monotonic()
            result = request(room, label, "GET",
                             "/admin/patients/" + str(user["patient_id"]) +
                             "/messages?access_id=" + user["public_id"],
                             headers={"Authorization": room["staff_authorization"]})
            check(result.status_code == 200, "STAFF_MESSAGES_DENIED")
            items = result.json()["items"]
            check(len(items) == ROUNDS and all("p105-patient-" in m["body"] for m in items),
                  "STAFF_SHARED_DB_MESSAGES_CROSS_PATIENT")
            count += len(items)
            samples.append((time.monotonic()-t0)*1000)
        kind = "staff"
    proof = {"label": label, "kind": kind, "count": count,
             "sha": room["sha"], "run_id": room["run_id"],
             "runner_name": os.environ["RUNNER_NAME"],
             "tailnet_ip": os.environ["DC06H_TAIL_IP"],
             "samples": len(samples), "p95_ms": percentile(samples, 95),
             "real_network_http": True, "synthetic_only": True}
    sent = request(room, label, "POST", "/lab/done", data=proof)
    check(sent.status_code == 200 and sent.json()["ok"], "REMOTE_SHARED_SERVER_PROOF_DENIED")
    Path("p105-client-proof.json").write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n")
    print("LOT06_P1_05_REAL_PRIVATE_VM_PRODUCT_CLIENT_PASS", {
        "role": label, "operations": count, "p95_ms": proof["p95_ms"],
        "elapsed_ms": round((time.monotonic()-start)*1000, 2)}, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("role", choices=("server", "client", "preflight"))
    ap.add_argument("--label", choices=LABELS)
    args = ap.parse_args()
    if args.role == "preflight":
        guard(require_network=False)
        check(len(LABELS) == 4 and PORT > 1024, "INVALID_TEST_TOPOLOGY")
        check(valid_ip("100.64.0.1") and not valid_ip("127.0.0.1")
              and not valid_ip("8.8.8.8"), "PRIVATE_ONLY_GUARD_BROKEN")
        print("LOT06_P1_05_NETWORK_STATIC_FAIL_CLOSED_PREFLIGHT_PASS")
    elif args.role == "server":
        run_server()
    else:
        check(args.label is not None, "MISSING_CLIENT_ROLE")
        run_client(args.label)


if __name__ == "__main__":
    main()
