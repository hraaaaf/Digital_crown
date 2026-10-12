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
    # Bounded discovery of a link written only after the synthetic server
    # successfully boots on a different runner. Never trust stale run IDs.
    for _ in range(140):
        request = subprocess.run(
            ["gh", "api", f"repos/{repo}/issues/844/comments?per_page=100"],
            capture_output=True, text=True, check=False, timeout=20,
        )
        if request.returncode == 0:
            try:
                comments = json.loads(request.stdout)
                for item in reversed(comments):
                    body = item.get("body", "")
                    if f"FIELD_LAB_RUN_ID={run_id}" not in body:
                        continue
                    match = re.search(r"FIELD_LAB_HOST=(https://[a-z0-9-]+\.trycloudflare\.com)", body)
                    if match:
                        return match.group(1)
            except (ValueError, TypeError):
                pass
        time.sleep(5)
    raise RuntimeError("LAB_SERVER_NOT_DISCOVERABLE: separate Cabinet runner unavailable")


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
    for iteration in range(26):
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
        assert denied.status_code == 423, (denied.status_code, denied.text[:400])
        assert not denied.headers.get("content-type", "").startswith("application/pdf")

        published = station.post(
            "/field-lab/station-publish",
            headers=auth, json={"session_id": session_id, "handoff_url": data["handoffUrl"]},
        )
        assert published.status_code == 200, (published.status_code, published.text[:500])
        print(
            f"STATION_READY run={run_id} iteration={iteration+1} session_id={session_id} "
            f"qr_status=published kiosk_pdf=423 station_workstation_id={station_workstation_id}",
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
                print("STATION_PHONE_CLAIM_OBSERVED on separate runner", flush=True)
                # Let the person inspect/download their fictitious PDF.
                time.sleep(65)
                break

    print("STATION_FIELD_WINDOW_COMPLETE", flush=True)
