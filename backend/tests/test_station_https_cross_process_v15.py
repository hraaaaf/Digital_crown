"""V1.5-04.5 RPG-X: real TLS socket, real FastAPI, isolated OS actor processes.

This is an isolated single-runner network rehearsal, NOT two physical machines,
a real QR/NFC scanner, or a browser visual approval. No mocked API routes.
"""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime

import fitz
import uvicorn

from backend import models
from backend.main import app
from backend.config import settings as app_settings
from backend.routers.workstation_mode import WORKSTATION_COOKIE
from backend.services.archive_service import ArchiveService
from backend.services.station_care_sheet import record_trusted_finalization
from backend.tests.test_station_patient_session_v15 import _patient_context, _station


# Invoked as a fresh OS process each time: TLS is verified by httpx against
# a test-only CA certificate, never verify=False or FastAPI TestClient.
ACTOR = r"""
import hashlib
import json
import os
import socket
import ssl
import sys
from urllib.parse import urlsplit

import fitz
import httpx

action = sys.argv[1]
p = json.loads(sys.stdin.read())
cert = p["cert"]
origin = p["origin"]
with socket.create_connection(("localhost", p["port"]), timeout=8) as sock:
    with ssl.create_default_context(cafile=cert).wrap_socket(sock, server_hostname="localhost") as secure:
        tls_version = secure.version()
        assert tls_version in ("TLSv1.2", "TLSv1.3"), tls_version

headers = {"Authorization": p["authorization"]} if p.get("authorization") else {}
cookies = {"dc_workstation": p["workstation_cookie"]} if p.get("workstation_cookie") else {}
with httpx.Client(base_url=origin, verify=cert, trust_env=False, timeout=15, headers=headers, cookies=cookies) as c:
    base = f"/api/workstation/patient-session/{p['session_id']}" if p.get("session_id") else ""
    if action == "sender":
        mode = c.post("/api/workstation/mode", json={"mode": "cabinet", "ownerPin": "2468"})
        assert mode.status_code == 200, (mode.status_code, mode.text)
        response = c.post(f"/api/workstation/documents/care-sheet/{p['document_id']}/authorize-withdrawal")
        assert response.status_code == 200, (response.status_code, response.text)
        assert response.json()["status"] == "AUTHORIZED"
        result = {"authorized": True}
    elif action == "create":
        mode = c.post("/api/workstation/mode", json={"mode": "station", "ownerPin": "2468"})
        assert mode.status_code == 200, (mode.status_code, mode.text)
        response = c.post("/api/workstation/patient-session")
        assert response.status_code == 201, (response.status_code, response.text)
        created = response.json()
        assert created["nfcPayload"] == created["handoffUrl"]
        assert created["handoffUrl"].startswith(origin + "/companion?stationSession=")
        result = {"session_id": created["sessionId"], "handoff": created["handoffUrl"]}
    elif action == "before":
        response = c.get(base + "/documents")
        assert response.status_code == 409 and response.json()["detail"] == "STATION_PATIENT_NOT_IDENTIFIED"
        result = {"denied_before_identity": True}
    elif action in ("claim", "replay"):
        raw = p["handoff"].split("stationSession=", 1)[1]
        response = c.post("/api/workstation/patient-session/claim", json={"token": raw, "accessId": p["access_id"]})
        assert response.status_code == (200 if action == "claim" else 409), (response.status_code, response.text)
        result = {"claim_once": action == "claim", "replay_denied": action == "replay"}
    elif action == "receive":
        # The receiver is a separate patient-phone OS process, not the kiosk.
        phone = f"/api/patient-companion/station-session/{p['session_id']}/documents"
        phone += f"?accessId={p['access_id']}"
        listing = c.get(phone)
        assert listing.status_code == 200, (listing.status_code, listing.text)
        assert listing.headers["cache-control"] == "no-store"
        assert listing.json() == {"documents": [{"documentId": p["document_id"], "kind": "care_sheet"}]}
        alien = c.get(phone.replace("/documents?", f"/documents/care-sheet/{p['other_document_id']}?"))
        assert alien.status_code == 404, (alien.status_code, alien.text)
        response = c.get(phone.replace("/documents?", f"/documents/care-sheet/{p['document_id']}?"))
        assert response.status_code == 200, (response.status_code, response.text)
        assert response.headers["content-type"].startswith("application/pdf")
        assert response.headers["cache-control"].startswith("no-store")
        assert response.headers["x-content-type-options"] == "nosniff"
        digest = hashlib.sha256(response.content).hexdigest()
        assert digest == p["expected_sha256"], (digest, p["expected_sha256"])
        pdf = fitz.open(stream=response.content, filetype="pdf")
        assert pdf.page_count == 1
        pixels = pdf[0].get_pixmap()
        assert pixels.width > 100 and pixels.height > 100
        pdf.close()
        result = {"sha256": digest, "bytes": len(response.content), "pdf_pages_rendered": 1, "alien_patient_denied": True}
    elif action == "purge":
        purge = c.post(base + "/purge")
        assert purge.status_code == 204, (purge.status_code, purge.text)
        phone = f"/api/patient-companion/station-session/{p['session_id']}/documents"
        phone += f"?accessId={p['access_id']}"
        patient_headers = {"Authorization": p["patient_authorization"]}
        listing = c.get(phone, headers=patient_headers)
        download = c.get(
            phone.replace("/documents?", f"/documents/care-sheet/{p['document_id']}?"),
            headers=patient_headers,
        )
        assert listing.status_code in (404, 409)
        assert download.status_code in (404, 409)
        assert not download.headers.get("content-type", "").startswith("application/pdf")
        result = {"purged": True, "listing_denied": True, "pdf_denied": True}
    elif action == "kiosk_pdf_denied":
        response = c.get(base + f"/documents/care-sheet/{p['document_id']}")
        assert response.status_code == 423, (response.status_code, response.text)
        assert not response.headers.get("content-type", "").startswith("application/pdf")
        result = {"kiosk_pdf_denied": True}
    elif action == "wrong_station":
        listing = c.get(base + "/documents")
        download = c.get(base + f"/documents/care-sheet/{p['document_id']}")
        assert listing.status_code in (404, 423), (listing.status_code, listing.text)
        assert download.status_code in (404, 423), (download.status_code, download.text)
        result = {"wrong_station_denied": True}
    elif action == "token_only":
        response = c.get(base + f"/documents/care-sheet/{p['document_id']}", headers={"Authorization": "Bearer " + p["handoff"].split("stationSession=", 1)[1]})
        assert response.status_code in (401, 403), (response.status_code, response.text)
        result = {"handoff_not_pdf_credential": True}
    else:
        raise AssertionError(f"Unknown actor: {action}")
print(json.dumps({"pid": os.getpid(), "tls": tls_version, **result}))
"""


def _valid_finalized_pdf(db, patient):
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((80, 80), "Feuille de soins - fictive - test HTTPS", fontsize=14)
    content = pdf.tobytes()
    pdf.close()
    digest = hashlib.sha256(content).hexdigest()
    document, _ = ArchiveService(db).archive_document(
        patient_id=patient.id,
        uploaded_by_id=patient.employer_id,
        file_content=content,
        filename=f"CareSheet_HTTPS_{patient.id}.pdf",
        doc_type=models.DocumentType.AUTRE,
        title="Feuille de soins - test isolation",
        tags=["insurance_submission", "cnss"],
        clinical_data={
            "kind": "INSURANCE_SUBMISSION",
            "schema_version": "1",
            "validated_by_practitioner_id": patient.employer_id,
            "validated_at": "2026-10-12T10:00:00",
            "draft": {"status": "VALIDATED"},
            "render_evidence": {"renderer": "PDF_OVERLAY_V1", "rendered_pdf_sha256": digest},
        },
        is_accounted=False,
        is_collected=False,
        payment_status=models.PaiementStatut.EN_ATTENTE,
    )
    record_trusted_finalization(
        db, document, employer_id=patient.employer_id,
        practitioner_id=patient.employer_id, expected_patient_id=patient.id,
    )
    return document, digest


def _actor(action, data):
    proc = subprocess.run(
        [sys.executable, "-c", ACTOR, action],
        input=json.dumps(data), text=True, capture_output=True, timeout=35,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        check=False,
    )
    assert proc.returncode == 0, f"{action}: exit={proc.returncode}; stderr={proc.stderr[-1500:]}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_045_tls_sender_companion_receiver_are_independent_os_processes(
    client, db, dentiste, monkeypatch, tmp_path,
):
    """HTTP+TLS only. Document bytes travel via FastAPI, not a copied fixture file."""
    staff, station_workstation_id = _station(client, dentiste)
    station_cookie = client.cookies.get(WORKSTATION_COOKIE)
    assert station_cookie, "Station must have its own authenticated workstation cookie."
    # Independently enroll another real workstation for the Cabinet sender.
    # It must not share the station credential, even when owned by one tenant.
    client.cookies.delete(WORKSTATION_COOKIE)
    cabinet_enroll = client.post(
        "/api/workstation/enroll", headers=staff, json={"accountPassword": "TestPass123!"},
    )
    assert cabinet_enroll.status_code == 200, cabinet_enroll.text
    cabinet_workstation_id = cabinet_enroll.json()["workstationId"]
    cabinet_cookie = client.cookies.get(WORKSTATION_COOKIE)
    assert cabinet_cookie and cabinet_cookie != station_cookie
    assert cabinet_workstation_id != station_workstation_id
    patient_a, access_a, patient_auth = _patient_context(db, dentiste, dossier="ST045-HTTPS-A")
    patient_b, _access_b, _patient_b_auth = _patient_context(db, dentiste, dossier="ST045-HTTPS-B")
    document_a, digest = _valid_finalized_pdf(db, patient_a)
    document_b, _ = _valid_finalized_pdf(db, patient_b)

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    origin = f"https://localhost:{port}"
    monkeypatch.setattr(app_settings, "STATION_HANDOFF_PUBLIC_ORIGIN", origin)
    cert, key = tmp_path / "localhost-cert.pem", tmp_path / "localhost-key.pem"
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-days", "1", "-subj", "/CN=localhost",
        "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
        "-keyout", str(key), "-out", str(cert),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    config = uvicorn.Config(
        app, host="127.0.0.1", port=port,
        ssl_certfile=str(cert), ssl_keyfile=str(key),
        lifespan="off", access_log=False, log_level="error",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="station-tls-api", daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.1)
        assert server.started, "Real HTTPS FastAPI did not start."
        common = {
            "origin": origin, "port": port, "cert": str(cert),
            "authorization": staff["Authorization"],
            "workstation_cookie": station_cookie, "document_id": document_a.id,
            "other_document_id": document_b.id, "expected_sha256": digest,
        }
        sender = _actor("sender", {**common, "workstation_cookie": cabinet_cookie})
        created = _actor("create", common)
        bound = {**common, "session_id": created["session_id"], "handoff": created["handoff"]}
        before = _actor("before", bound)
        patient = _actor("claim", {
            **bound, "authorization": patient_auth["Authorization"],
            "workstation_cookie": "", "access_id": access_a.public_id,
        })
        replay = _actor("replay", {
            **bound, "authorization": patient_auth["Authorization"],
            "workstation_cookie": "", "access_id": access_a.public_id,
        })
        kiosk_blocked = _actor("kiosk_pdf_denied", bound)
        assert kiosk_blocked["kiosk_pdf_denied"]
        received = _actor("receive", {
            **bound, "authorization": patient_auth["Authorization"],
            "workstation_cookie": "", "access_id": access_a.public_id,
        })
        wrong_station = _actor("wrong_station", {**bound, "workstation_cookie": cabinet_cookie})
        token_only = _actor("token_only", {
            **bound, "authorization": "", "workstation_cookie": "",
        })
        purged = _actor("purge", {
            **bound, "access_id": access_a.public_id,
            "patient_authorization": patient_auth["Authorization"],
        })
        db.expire_all()
        session = db.get(models.WorkstationPatientSession, created["session_id"])
        assert session is not None
        assert session.purged_at is not None and session.patient_id is None
        assert session.patient_access_id is None
        pids = [sender["pid"], created["pid"], patient["pid"], received["pid"]]
        assert len(set(pids)) == 4, "The sender, station and patient must be different OS processes."
        assert all(item["tls"].startswith("TLSv1.") for item in (sender, created, patient, received))
        assert before["denied_before_identity"] and replay["replay_denied"]
        assert received["sha256"] == digest and received["pdf_pages_rendered"] == 1
        assert received["alien_patient_denied"] and token_only["handoff_not_pdf_credential"]
        assert wrong_station["wrong_station_denied"]
        assert purged["purged"] and purged["listing_denied"] and purged["pdf_denied"]
        evidence = {
            "lot": "V1.5-04.5", "gate": "RPG-X",
            "github_sha": os.getenv("GITHUB_SHA"),
            "observed_utc": datetime.utcnow().isoformat() + "Z",
            "transport": "verified HTTPS localhost TCP socket with test-only ephemeral TLS certificate",
            "actors": {"sender_pid": sender["pid"], "station_create_pid": created["pid"],
                       "companion_pid": patient["pid"], "receiver_pid": received["pid"],
                       "cabinet_workstation_id": cabinet_workstation_id,
                       "station_workstation_id": station_workstation_id,
                       "distinct_workstation_credentials": cabinet_cookie != station_cookie},
            "tls": received["tls"], "sha256": digest, "received_bytes": received["bytes"],
            "pdf_pages_rendered": received["pdf_pages_rendered"],
            "denials": ["not_identified", "replay", "other_patient", "wrong_workstation", "kiosk_pdf", "token_only", "post_purge"],
            "scope": "isolated GitHub runner; separate Cabinet+Station workstation identities and personal-phone OS process; no physical PCs, NFC or real printer",
        }
        artifact = Path("backend/artifacts/v15-04-5-https/evidence.json")
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print("04.5 RPG-X HTTPS separate-process sender/companion/receiver PASS; sha256=" + digest)
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive(), "HTTPS test server must stop cleanly."
