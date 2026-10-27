"""LOT06-B: real Chromium → Axios → localhost HTTP → actual FastAPI ASGI.

Only synthetic data in SQLite :memory:. No mock server responses, no real
patients/devices, no product UI registration, and no Vercel/clinical deployment.
The loopback HTTP bridge executes the actual FastAPI TestClient and forwards the
browser's Bearer AND workstation cookies; it never fabricates API results.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import subprocess
import threading
import time
from urllib.request import urlopen
from contextlib import contextmanager

from fastapi.testclient import TestClient
from PIL import Image
import pytest
from playwright.sync_api import sync_playwright
from sqlalchemy import select

from backend.main import app
from backend.models_media_core import ClinicalAsset
from backend.services import imaging_acquisition_transfer_lab_v15 as lab
from backend.tests.test_imaging_acquisition_preflight_v15 import _lab, _patient, _rdv


@contextmanager
def real_loopback_asgi():
    # TestClient without a cookie jar: browser must supply real login/session
    # and workstation authority, not borrow any fixture client's cookies.
    isolated_asgi = TestClient(app, raise_server_exceptions=True)
    lock = threading.Lock()
    requests_seen: list[tuple[str, str, int]] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):  # no JWT, image or PHI in logs
            return

        def _headers(self, status, length, content_type="application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:5187")
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Access-Control-Allow-Headers",
                             "Authorization,Content-Type,X-DC06B-Lab-Device-Token")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def do_OPTIONS(self):
            self._headers(204, 0)

        def do_GET(self):
            self._forward()

        def do_POST(self):
            self._forward()

        def _forward(self):
            if not self.path.startswith("/api/imaging-acquisitions/lab/"):
                self._headers(404, 0)
                return
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 <= size <= 50 * 1024 * 1024 + 8192:
                self._headers(413, 0)
                return
            body = self.rfile.read(size)
            headers = {
                key: value for key, value in self.headers.items()
                if key.lower() in {
                    "authorization", "cookie", "content-type",
                    "x-dc06b-lab-device-token",
                }
            }
            with lock:
                # Real FastAPI route + auth + workstation + SQL business logic.
                response = isolated_asgi.request(self.command, self.path,
                                                 headers=headers, content=body)
                requests_seen.append((self.command, self.path.split("?")[0],
                                      response.status_code))
            payload = response.content
            self._headers(response.status_code, len(payload),
                          response.headers.get("content-type", "application/json"))
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests_seen
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        isolated_asgi.close()


def _vite_ready(port: int, process: subprocess.Popen, timeout: int = 75):
    for _ in range(timeout * 4):
        if process.poll() is not None:
            raise AssertionError("VITE_DEV_STOPPED")
        try:
            with urlopen(f"http://127.0.0.1:{port}/staff-review-http-fixture.html",
                         timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(.25)
    raise AssertionError("VITE_DEV_TIMEOUT")


@pytest.mark.parametrize("patient_only", [False, True],
                         ids=["matched-rdv", "patient-only-audited"])
def test_real_browser_patient_rdv_approve_upload_receipt(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path, patient_only
):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root",
        lambda: tmp_path,
    )
    station = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, "LIVE" + str(dentiste.id))
    rdv = None if patient_only else _rdv(db, dentiste.id, patient.id)
    reason_code = "LAB_UNSCHEDULED" if patient_only else None
    device = "real-http-synthetic-bridge"
    capture = "capture-live-http-20261027"
    device_token = lab.enroll_fixture(db, tenant=dentiste.id, device=device)
    png = BytesIO()
    Image.new("RGB", (4, 4), color=(120, 80, 40)).save(png, format="PNG")
    image = png.getvalue()
    digest = hashlib.sha256(image).hexdigest()

    frontend = Path(__file__).resolve().parents[2] / "frontend"
    standalone = frontend / "staff-review-http-fixture.html"
    if standalone.exists():
        raise AssertionError("DEV_HARNESS_HTML_ALREADY_PRESENT")
    standalone.write_text(
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex,nofollow"></head><body>'
        '<div id="root"></div><script type="module" '
        'src="/src/features/imaging/__tests__/StaffReviewHttpHarness.tsx">'
        '</script></body></html>',
        encoding="utf-8",
    )
    log = tmp_path / "vite-lab.log"
    with real_loopback_asgi() as (backend_origin, recorded), log.open("wb") as stream:
        env = os.environ.copy()
        env["VITE_API_URL"] = backend_origin
        env["BROWSER"] = "none"
        process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1",
             "--port", "5187", "--strictPort"],
            cwd=frontend, env=env, stdout=stream, stderr=subprocess.STDOUT,
        )
        try:
            _vite_ready(5187, process)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    context = browser.new_context(viewport={"width": 1280, "height": 900})
                    # Access-cookie pairing and workstation identity use actual
                    # credentials created by /api/auth/login & _lab fixture.
                    jwt = auth_headers["Authorization"].removeprefix("Bearer ")
                    context.add_cookies([
                        {"name": "access_token", "value": jwt,
                         "url": backend_origin},
                        {"name": "dc_workstation",
                         "value": client.cookies["dc_workstation"],
                         "url": backend_origin},
                    ])
                    fixture = {
                        "workstationId": station,
                        "capture": {
                            "device": device, "capture": capture,
                            "modality": "PNG synthetique HTTP",
                            "claimedSha256": digest,
                            "receivedAtLabel": "Fixture TEST uniquement",
                        },
                        "targets": [{
                            "patientId": patient.id,
                            "label": f"Patient synthétique {patient.id}",
                            "appointments": [] if patient_only else [{
                                "id": rdv.id, "label": "RDV synthétique",
                            }],
                        }],
                    }
                    context.add_init_script(
                        "localStorage.setItem('token', " + json.dumps(jwt) +
                        ");window.__DC06B_HTTP_TEST__=" +
                        json.dumps(fixture, ensure_ascii=False) + ";"
                    )
                    page = context.new_page()
                    page.goto("http://127.0.0.1:5187/staff-review-http-fixture.html",
                              wait_until="networkidle")
                    page.get_by_role(
                        "heading", name="Associer une capture au bon patient"
                    ).wait_for()
                    assert page.locator("#lab-patient").input_value() == ""
                    assert page.get_by_role(
                        "button", name="Vérifier le lien patient"
                    ).is_disabled()
                    # Real device proposal over network, not fixtures calling
                    # lab.propose directly and not a client-generated response.
                    proposed = page.evaluate(
                        """async ([origin, tenant, device, capture, digest, size, token]) => {
                          const resp = await fetch(origin+'/api/imaging-acquisitions/lab/propose',{
                            method:'POST',
                            headers:{'Content-Type':'application/json',
                              'X-DC06B-Lab-Device-Token':token},
                            body:JSON.stringify({tenant,device,capture,
                              sha256:digest,byte_size:size})
                          });
                          return {status:resp.status,body:await resp.json()};
                        }""",
                        [backend_origin, dentiste.id, device, capture,
                         digest, len(image), device_token],
                    )
                    assert proposed["status"] == 200, proposed
                    assert proposed["body"]["status"] == "AWAITING_STAFF"
                    # Upload cannot work before actual staff approval.
                    pre = page.evaluate(
                        """async ([origin,tenant,device,capture,token,encoded]) => {
                          const data=new FormData();
                          data.append('tenant',String(tenant));
                          data.append('device',device);data.append('capture',capture);
                          const bytes=Uint8Array.from(atob(encoded),x=>x.charCodeAt(0));
                          data.append('file',new Blob([bytes],{type:'image/png'}),'synthetic.png');
                          const r=await fetch(origin+'/api/imaging-acquisitions/lab/transfer',{
                            method:'POST',headers:{'X-DC06B-Lab-Device-Token':token},body:data
                          });
                          return r.status;
                        }""",
                        [backend_origin,dentiste.id,device,capture,device_token,
                         base64.b64encode(image).decode()],
                    )
                    assert pre == 403  # valid bytes cannot bypass approval
                    page.locator("#lab-patient").select_option(str(patient.id))
                    if patient_only:
                        # Same actual FastAPI endpoint must deny missing/free-text
                        # reason even when staff JWT/station is otherwise valid.
                        invalid = page.evaluate(
                            """async ([origin,station,device,capture,patient]) => {
                              const base={workstation_id:station,device,capture,
                                patient_id:patient,appointment_id:null};
                              const bearer=localStorage.getItem('token');
                              const req=async(payload)=> {
                                const r=await fetch(origin+'/api/imaging-acquisitions/lab/review',{
                                  method:'POST',credentials:'include',
                                  headers:{'Content-Type':'application/json',
                                    'Authorization':'Bearer '+bearer},
                                  body:JSON.stringify(payload)
                                });
                                return {status:r.status,body:await r.json()};
                              };
                              return {
                                missing:await req(base),
                                free_text:await req({...base,
                                  patient_only_reason:'Informations médicales libres'})
                              };
                            }""",
                            [backend_origin, station, device, capture, patient.id],
                        )
                        assert invalid["missing"]["status"] == 422, invalid
                        assert invalid["free_text"]["status"] == 422, invalid
                        page.locator("#lab-reason").fill("LAB_UNSCHEDULED")
                    else:
                        page.locator("#lab-appointment").select_option(str(rdv.id))
                    page.get_by_role("button", name="Vérifier le lien patient").click()
                    page.get_by_text("Vérifier avant confirmation").wait_for()
                    assert ("POST", "/api/imaging-acquisitions/lab/review", 200) in recorded
                    assert not any(path.endswith("/approve") for _,path,_ in recorded)
                    page.get_by_role("button", name="Confirmer ce patient").click()
                    page.get_by_text("Association approuvée dans le LAB.", exact=False).wait_for()
                    assert ("POST", "/api/imaging-acquisitions/lab/approve", 200) in recorded
                    # After the actual UI approval, upload real bytes and
                    # recover their receipt from FastAPI via genuine HTTP.
                    results = page.evaluate(
                        """async ([origin,tenant,device,capture,token,encoded,digest]) => {
                          const bytes=Uint8Array.from(atob(encoded),x=>x.charCodeAt(0));
                          const upload=async(content) => {
                            const data=new FormData();
                            data.append('tenant',String(tenant));
                            data.append('device',device);
                            data.append('capture',capture);
                            data.append('file',new Blob([content],{type:'image/png'}),
                              'synthetic.png');
                            const r=await fetch(origin+'/api/imaging-acquisitions/lab/transfer',{
                              method:'POST',
                              headers:{'X-DC06B-Lab-Device-Token':token},
                              body:data
                            });
                            return {status:r.status,body:await r.json()};
                          };
                          const first=await upload(bytes);
                          // Deliberately disregard the original ACK as if it
                          // never reached the connector. Query independently
                          // before any replay. This is NOT a crash/restart test.
                          const beforeReplay=await fetch(
                            origin+'/api/imaging-acquisitions/lab/receipt?'+
                            new URLSearchParams({tenant:String(tenant),device,capture}),{
                              headers:{'X-DC06B-Lab-Device-Token':token}
                            });
                          const recovered={status:beforeReplay.status,
                            body:await beforeReplay.json()};
                          const replay=await upload(bytes);
                          const tamper=await upload(new Uint8Array([0,1,2]));
                          const r=await fetch(origin+'/api/imaging-acquisitions/lab/receipt?'+
                             new URLSearchParams({tenant:String(tenant),device,capture}),{
                             headers:{'X-DC06B-Lab-Device-Token':token}
                          });
                          const denied=await fetch(origin+'/api/imaging-acquisitions/lab/receipt?'+
                             new URLSearchParams({tenant:String(tenant),device,capture}),{
                             headers:{'X-DC06B-Lab-Device-Token':'invalid'}
                          });
                          return {first,recovered,replay,tamper,lookup:{status:r.status,
                             body:await r.json()},denied:denied.status,expected:digest};
                        }""",
                        [backend_origin,dentiste.id,device,capture,device_token,
                         base64.b64encode(image).decode(),digest],
                    )
                    assert results["first"]["status"] == 200, results
                    first = results["first"]["body"]
                    assert first["status"] == "LAB_SERVER_RECEIPT"
                    assert first["server_confirmed"] is False
                    assert first["patient_id"] == patient.id
                    assert first["sha256"] == digest
                    assert results["recovered"] == {"status": 200, "body": first}
                    assert results["replay"]["body"] == first
                    assert results["lookup"] == {"status": 200, "body": first}
                    assert results["tamper"]["status"] == 409
                    assert results["denied"] == 401
                    assert len([r for r in recorded if r[1].endswith("/approve")
                                and r[2] == 200]) == 1
                    row = db.execute(select(lab.audit).where(
                        lab.audit.c.receipt_id == first["receipt_id"]
                    )).mappings().one()
                    assert row["patient_only_reason"] == reason_code
                    assets = db.query(ClinicalAsset).filter(
                        ClinicalAsset.id == first["asset_id"],
                        ClinicalAsset.employer_id == dentiste.id,
                        ClinicalAsset.patient_id == patient.id,
                    ).all()
                    assert len(assets) == 1 and assets[0].sha256 == digest
                    assert len(db.execute(select(lab.receipts).where(
                        lab.receipts.c.receipt_id == first["receipt_id"]
                    )).all()) == 1
                    report = {
                        "kind": "LOT06B_REAL_HTTP_ASGI_BROWSER_FIXTURE",
                        "real_fastapi_asgi": True,
                        "real_browser_network": True,
                        "session_and_workstation_checked": True,
                        "synthetic_data_only": True,
                        "server_receipt": first["status"],
                        "server_confirmed": False,
                        "no_clinical_release": True,
                        "negative_preapproval": pre,
                        "negative_tamper": results["tamper"]["status"],
                        "negative_device_token": results["denied"],
                        "patient_only": patient_only,
                        "audit_reason_code": reason_code,
                        "lost_ack_receipt_lookup": True,
                        "backend_restart_or_disk_durability_tested": False,
                        "server_confirmed": False,
                        "route_codes": [
                            {"method": method, "route": route, "status": status}
                            for method,route,status in recorded
                        ],
                    }
                    evidence_root = Path(os.environ.get(
                        "DC06B_HTTP_EVIDENCE_DIR", str(tmp_path)
                    ))
                    evidence_root.mkdir(parents=True, exist_ok=True)
                    scenario = "patient-only" if patient_only else "matched-rdv"
                    evidence = evidence_root / f"lot06b-real-http-proof-{scenario}.json"
                    evidence.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
                    print("LOT06B_REAL_HTTP_REACT_FASTAPI_RECEIPT_PASS", scenario)
                    context.close()
                finally:
                    browser.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=8)
            standalone.unlink(missing_ok=True)
