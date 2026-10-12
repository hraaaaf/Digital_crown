"""Independent GitHub Actions Station actor over public TLS to an isolated Cabinet runner.

Uses the real Station FastAPI routes with its own workstation cookie and
distinct OS runner. Synthetic test actors only; not a physical station.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone

import httpx

run_id = os.environ["GITHUB_RUN_ID"]
repo = os.environ["GITHUB_REPOSITORY"]
password = os.environ["FIELD_DEMO_PASSWORD"]
email = f"field-{run_id}@example.com"


def discover_origin() -> str:
    """Read a same-run artifact after upload by the independent Cabinet job.

    Actions-only artifact exchange works while the server job remains alive.
    No issue/PR comments, no write permissions, no shared runner filesystem.
    """
    folder = "/tmp/field-actions-live-link"
    os.makedirs(folder, exist_ok=True)
    for _ in range(135):
        response = subprocess.run(
            ["gh", "run", "download", run_id, "--repo", repo,
             "--name", "v15-04-5-live-link", "--dir", folder],
            capture_output=True, text=True, check=False, timeout=22,
        )
        path = os.path.join(folder, ".field-live.txt")
        if response.returncode == 0 and os.path.exists(path):
            values = open(path, encoding="utf-8").read().splitlines()
            if len(values) >= 2 and values[0] == run_id:
                origin = values[1].strip()
                if re.fullmatch(r"https://[a-z0-9-]+\.trycloudflare\.com", origin):
                    return origin
        time.sleep(5)
    raise RuntimeError("LAB_SERVER_ARTIFACT_UNAVAILABLE: separate Cabinet runner did not publish origin")

origin = discover_origin()
with httpx.Client(base_url=origin, timeout=35, follow_redirects=False) as station:
    healthy = station.get("/field-lab/health")
    assert healthy.status_code == 200, (healthy.status_code, healthy.text[:1000])
    assert str(healthy.json().get("run_id")) == run_id, "Wrong isolated Cabinet run."
    doc_id = int(healthy.json()["document_id"])

    login = station.post(
        "/api/auth/login", data={"username": email, "password": password},
    )
    assert login.status_code == 200, (login.status_code, login.text[:400])
    auth = {"Authorization": f"Bearer {login.json()['access_token']}"}

    enrolled = station.post(
        "/api/workstation/enroll",
        headers=auth, json={"accountPassword": password},
    )
    assert enrolled.status_code == 200, (enrolled.status_code, enrolled.text[:500])
    assert station.cookies.get("dc_workstation"), "Station workstation cookie missing"
    cabinet_mode = station.post(
        "/api/workstation/mode",
        headers=auth, json={"mode": "station", "ownerPin": "2468"},
    )
    assert cabinet_mode.status_code == 200, (cabinet_mode.status_code, cabinet_mode.text[:400])
    station_workstation_id = cabinet_mode.json()["workstationId"]
    assert station_workstation_id != healthy.json()["cabinet_workstation_id"], "CABINET_STATION_NOT_ISOLATED"

    # Bounded 13-minute interactive window. Rotate expired QR only. Do NOT
    # rotate a claimed session during its valid retrieval window.
    for iteration in range(7):
        issued = station.post("/api/workstation/patient-session", headers=auth)
        assert issued.status_code == 201, (issued.status_code, issued.text[:600])
        data = issued.json()
        assert data["handoffUrl"].startswith(origin + "/companion?stationSession=")
        assert data["handoffUrl"] == data["nfcPayload"]
        session_id = data["sessionId"]

        denied = station.get(
            f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{doc_id}",
            headers=auth,
        )
        # Before phone identification, the real fail-closed contract is 409.
        # After a successful Companion claim, the kiosk must still be PDF-denied (423).
        assert denied.status_code == 409, (denied.status_code, denied.text[:400])
        assert denied.json().get("detail") == "STATION_PATIENT_NOT_IDENTIFIED"
        assert not denied.headers.get("content-type", "").startswith("application/pdf")

        published = station.post(
            "/api/workstation/field-lab/station-publish",
            headers=auth, json={"session_id": session_id, "handoff_url": data["handoffUrl"]},
        )
        assert published.status_code == 200, (published.status_code, published.text[:500])
        print(
            f"STATION_READY run={run_id} iteration={iteration+1} session_id={session_id} "
            f"qr_status=published preclaim_kiosk_pdf=409 station_workstation_id={station_workstation_id}",
            flush=True,
        )

        # Retain the current session until it expires. The companion receives
        # the same generated session via the independent real iPhone browser.
        for _ in range(22):
            time.sleep(5)
            status = station.get(
                f"/api/workstation/patient-session/{session_id}", headers=auth,
            )
            if status.status_code in (404, 409, 410):
                break
            assert status.status_code == 200, (status.status_code, status.text[:500])
            state = status.json().get("status", "")
            if state == "expired":
                break
            if state == "identified":
                post_claim_denied = station.get(
                    f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{doc_id}",
                    headers=auth,
                )
                assert post_claim_denied.status_code == 423, (
                    post_claim_denied.status_code, post_claim_denied.text[:400],
                )
                assert not post_claim_denied.headers.get("content-type", "").startswith("application/pdf")
                print("STATION_PHONE_CLAIM_OBSERVED kiosk_pdf=423 on separate runner", flush=True)
                # Let the person inspect/download their fictitious PDF.
                time.sleep(65)
                break

    print("STATION_FIELD_WINDOW_COMPLETE", flush=True)
