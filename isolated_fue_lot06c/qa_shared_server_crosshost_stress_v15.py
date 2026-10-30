"""LOT06 C05B-03G four REAL remote Ubuntu GitHub runners -> one isolated TEST receiver.

One runner hosts a loopback-only synthetic HTTP receiver through a TEMPORARY
Cloudflare Quick Tunnel; four other GitHub runner VMs send deterministic PNGs
over HTTPS to that ONE origin. Actual LOT06-A HotFolder / SQLite / AES-GCM is
used after the phase barrier. Never expose Digital Crown backend or cabinet.
NO clinical transfer, authorization, physical device or release certification.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile

from isolated_fue_lot06c.qa_multi_ubuntu_hotfolder_stress_v15 import (
    Receiver, ReceiverHandler, new_collector, payload,
)
from tools.imaging_gateway import HotFolder

CLIENTS = {"u22a": 24, "u22b": 48, "u24a": 24, "u24b": 48}
PHASE_NAMES = {"two": 2, "bulk": None, "flood": 16}
TOTAL_HEALTHY = sum(2 + n for n in CLIENTS.values())  # 152
TOTAL_RECEIVED = TOTAL_HEALTHY + len(CLIENTS) * 16  # 216
CAPACITY = 160
TIME_LIMIT_S = 510
PHASE_TIMEOUT_S = 170


def guard():
    assert (os.environ.get("ENVIRONMENT") == "test"
            and os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
            and os.environ.get("DC06C05B03G_TEST_ONLY") == "1"), "ISOLATED_G_ONLY"
    assert os.environ.get("GITHUB_ACTIONS") == "true", "GITHUB_ACTIONS_ONLY"
    assert os.environ.get("EXPECTED_SHA") == os.environ.get("GITHUB_SHA_EXACT"), "SHA_UNPINNED"


def ensure(cond, code):
    if not cond:
        raise AssertionError(code)


def names(label, phase):
    n = CLIENTS[label] if phase == "bulk" else PHASE_NAMES[phase]
    return [f"stress_{label}_{phase}_{i:05d}" for i in range(n)]


class SharedReceiver(Receiver):
    def __init__(self, watch, token):
        super().__init__(("127.0.0.1", 0), watch, token)
        self.RequestHandlerClass = SharedHandler
        self.lock = threading.Lock()
        self.ready = set()
        self.progress = {p: set() for p in ("two", "bulk", "flood")}
        self.phase = "ready"
        self.start_at = None
        self.received_by_stage = Counter()


class SharedHandler(ReceiverHandler):
    def _auth(self):
        return secrets.compare_digest(
            self.headers.get("X-Lab-Token", ""), self.server.token
        )

    def _json(self, status, obj):
        data = json.dumps(obj, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._auth() or self.path != "/test-only/status":
            self._json(403, {"error": "LAB_AUTH_REQUIRED"})
            return
        with self.server.lock:
            self._json(200, {"phase": self.server.phase,
                             "start_at": self.server.start_at,
                             "ready_count": len(self.server.ready)})

    def do_POST(self):
        server = self.server
        if self.path == "/test-only/incoming":
            if not self._auth():
                self._json(403, {"error": "LAB_AUTH_REQUIRED"})
                return
            cap = self.headers.get("X-Capture", "")
            match = re.fullmatch(r"stress_(u22a|u22b|u24a|u24b)_(two|bulk|flood)_[0-9]{5}", cap)
            if not match or cap not in names(match.group(1), match.group(2)):
                self._json(422, {"error": "UNKNOWN_SYNTHETIC_CAPTURE"})
                return
            with server.lock:
                active = server.phase
            if active != match.group(2):
                self._json(409, {"error": "PHASE_BLOCKED"})
                return
            # ReceiverHandler checks exact payload, identity, token, bounds
            # and atomically writes only .png and .ready under a single lock.
            super().do_POST()
            return
        if not self._auth():
            self._json(403, {"error": "LAB_AUTH_REQUIRED"})
            return
        match = re.fullmatch(r"/test-only/(ready|two-done|bulk-done|flood-done)", self.path)
        raw = self.headers.get("Content-Length", "")
        if not match or not raw.isdecimal() or int(raw) > 120:
            self._json(422, {"error": "INVALID_CONTROL"})
            return
        try:
            d = json.loads(self.rfile.read(int(raw)))
        except (ValueError, UnicodeError):
            self._json(422, {"error": "BAD_JSON"})
            return
        label = d.get("label") if isinstance(d, dict) else None
        if label not in CLIENTS:
            self._json(422, {"error": "UNKNOWN_LAB_CLIENT"})
            return
        command = match.group(1)
        with server.lock:
            if command == "ready":
                if server.phase != "ready":
                    self._json(409, {"error": "LATE_READY"})
                    return
                server.ready.add(label)
            else:
                phase = command.replace("-done", "")
                if server.phase != phase or label not in server.ready:
                    self._json(409, {"error": "WRONG_PHASE"})
                    return
                server.progress[phase].add(label)
        self._json(200, {"ok": True})


def wait_for(predicate, code, *, timeout=PHASE_TIMEOUT_S):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.2)
    raise AssertionError(code)


def snapshot(receiver, phase):
    with receiver.lock:
        return (receiver.phase == phase,
                len(receiver.ready),
                len(receiver.progress.get(phase, ())))


def verified_ledger(agent, count, expected):
    rows = agent.items()
    ensure(len(rows) == count, "QUEUE_COUNT_INCORRECT")
    ensure(all(row["state"] == "PENDING_CONFIRMATION" for row in rows),
           "FALSE_CLINICAL_STATE")
    actual = Counter(row["digest"] for row in rows)
    possible = Counter(hashlib.sha256(payload(name)).hexdigest() for name in expected)
    ensure(not (actual - possible), "UNEXPECTED_CAPTURE_IN_LEDGER")
    for row in rows:
        data = agent.read_verified(row["id"])
        ensure(hashlib.sha256(data).hexdigest() == row["digest"],
               "CIPHERTEXT_READBACK_FAILED")
        ensure(agent.audit(row["id"]) == ["PENDING_CONFIRMATION"],
               "AUDIT_MISSING")
    return agent.storage_health()


def verify_files(root, all_names):
    watch = root / "incoming"
    actual = {p.stem for p in watch.glob("*.png")}
    ensure(actual == set(all_names), "ORIGINAL_SOURCE_LOST_OR_WRONG")
    ensure(len(list(watch.glob("*.png.ready"))) == len(all_names),
           "PRODUCER_MARKER_MISSING")
    for cap in all_names:
        ensure((watch / (cap + ".png")).read_bytes() == payload(cap),
               "SOURCE_BYTES_CORRUPTED")


def orchestrate(receiver, agent, root, config):
    try:
        wait_for(lambda: snapshot(receiver, "ready")[1] == 4, "MISSING_REMOTE_RUNNER", timeout=330)
        with receiver.lock:
            receiver.phase, receiver.start_at = "two", time.time() + 5
        wait_for(lambda: snapshot(receiver, "two")[2] == 4, "TWO_REMOTE_SENDERS_INCOMPLETE")
        ensure(receiver.accepted == 8, "SIMULTANEOUS_TWO_PER_HOST_MISSING")
        print("LOT06C05B03G_EIGHT_REAL_REMOTE_TWO_FILE_SENDERS_PASS", flush=True)

        with receiver.lock:
            receiver.phase, receiver.start_at = "bulk", time.time() + 3
        wait_for(lambda: snapshot(receiver, "bulk")[2] == 4, "REMOTE_BULK_INCOMPLETE")
        ensure(receiver.accepted == TOTAL_HEALTHY, "REMOTE_BULK_RECEIVE_COUNT")
        first = agent.scan_once()
        second = agent.scan_once()
        ensure(first["unstable"] == TOTAL_HEALTHY, "BULK_READY_STABILITY_GATE_MISSING")
        ensure(second["staged"] == TOTAL_HEALTHY and second["deferred"] == 0,
               "BULK_QUEUE_STAGING_FAILED")
        healthy = [n for label in CLIENTS for phase in ("two", "bulk")
                   for n in names(label, phase)]
        health = verified_ledger(agent, TOTAL_HEALTHY, healthy)
        ensure(health["queued_items"] == TOTAL_HEALTHY, "BULK_LEDGER_COUNT")
        print("LOT06C05B03G_REAL_SHARED_SERVER_SQLITE_AES_QUEUE_PASS", flush=True)

        with receiver.lock:
            receiver.phase, receiver.start_at = "flood", time.time() + 3
        wait_for(lambda: snapshot(receiver, "flood")[2] == 4, "REMOTE_FLOOD_INCOMPLETE")
        ensure(receiver.accepted == TOTAL_RECEIVED, "FLOOD_RECEIVE_COUNT")
        extra = [n for label in CLIENTS for n in names(label, "flood")]
        first = agent.scan_once()
        second = agent.scan_once()
        ensure(first["unstable"] == len(extra), "FLOOD_STABILITY_GATE_MISSING")
        ensure(second["staged"] == CAPACITY - TOTAL_HEALTHY,
               "CAPACITY_NOT_ENFORCED")
        ensure(second["deferred"] == TOTAL_RECEIVED - CAPACITY,
               "BACKPRESSURE_MISSING")
        state = verified_ledger(agent, CAPACITY, healthy + extra)
        ensure(state["state"] == "BACKPRESSURE", "BACKPRESSURE_HEALTH_MISSING")
        verify_files(root, healthy + extra)
        print("LOT06C05B03G_REMOTE_BACKPRESSURE_SOURCES_PRESERVED_PASS", flush=True)

        restarted = HotFolder(config)
        restarted.scan_once()
        final = restarted.scan_once()
        ensure(final["staged"] == 0 and len(restarted.items()) == CAPACITY,
               "COLD_RESTART_DUPLICATED")
        ensure(receiver.accepted == TOTAL_RECEIVED,
               "REMOTE_FILES_LOST")
        print("LOT06C05B03G_REMOTE_RESTART_IDEMPOTENCY_PASS", flush=True)
        report = {
            "kind": "LOT06_C05B03G_REAL_REMOTE_SHARED_SERVER_LAB",
            "head_sha": os.environ["EXPECTED_SHA"],
            "expected_clients": sorted(CLIENTS),
            "remote_http_received": receiver.accepted,
            "pre_saturation_queue": TOTAL_HEALTHY,
            "final_sqlite_encrypted_queue": CAPACITY,
            "deferred_sources_preserved": TOTAL_RECEIVED - CAPACITY,
            "external_clients_all_joined": len(receiver.ready) == 4,
            "two_per_host_simultaneous_barrier": True,
            "all_source_sha256_and_aesgcm_verified": True,
            "cold_restart_no_duplicate": True,
            "tests_are_synthetic": True,
            "production_endpoint_touched": False,
            "clinical_receipt_issued": False,
            "physical_powercut_tested": False,
            "product_ready": False,
        }
        Path("server-proof.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return report
    finally:
        with receiver.lock:
            receiver.phase = "finished"


def start_tunnel(local_port):
    env = dict(os.environ)
    env["NO_AUTOUPDATE"] = "true"
    tunnel = subprocess.Popen(
        ["./cloudflared", "tunnel", "--no-autoupdate", "--url",
         "http://127.0.0.1:" + str(local_port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        bufsize=1, env=env,
    )
    endpoint = []
    ready = threading.Event()

    def consume():
        try:
            for line in tunnel.stdout:
                match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
                if match and not endpoint:
                    endpoint.append(match.group())
                    ready.set()
        finally:
            ready.set()

    threading.Thread(target=consume, daemon=True).start()
    if not ready.wait(85) or not endpoint:
        tunnel.terminate()
        raise AssertionError("QUICK_TUNNEL_NO_ENDPOINT")
    return tunnel, endpoint[0]


def request_json(url, token, path, data=None, timeout=20):
    headers = {"X-Lab-Token": token, "Cache-Control": "no-store"}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data, separators=(",", ":")).encode()
    req = urllib.request.Request(url + path, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 502, 503, 504, 520, 522, 530) or attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(1 + attempt)
    raise AssertionError("UNREACHABLE_REMOTE")


def run_host():
    guard()
    root = Path(tempfile.mkdtemp(prefix="lot06-c05b03g-shared-"))
    agent, config = new_collector(root, CAPACITY)
    receiver = SharedReceiver(config.watch, secrets.token_urlsafe(35))
    thread = threading.Thread(target=receiver.serve_forever, daemon=True)
    thread.start()
    tunnel = None
    try:
        tunnel, url = start_tunnel(receiver.server_port)
        # Verify that HTTPS actually traverses Cloudflare to this ONE origin.
        wait_for(lambda: _probe(url, receiver.token), "TUNNEL_HTTPS_NOT_ACCESSIBLE",
                 timeout=75)
        private = {
            "schema": "LOT06_C05B03G_EPHEMERAL_RUN_ONLY",
            "head_sha": os.environ["EXPECTED_SHA"],
            "run_id": os.environ["GITHUB_RUN_ID"],
            "url": url,
            "token": receiver.token,
        }
        out = Path("rendezvous-private.json")
        out.write_text(json.dumps(private, sort_keys=True), encoding="utf-8")
        os.chmod(out, 0o600)
        print("LOT06C05B03G_REAL_SHARED_TUNNEL_READY (endpoint redacted)", flush=True)
        orchestrate(receiver, agent, root, config)
    finally:
        if tunnel is not None and tunnel.poll() is None:
            tunnel.terminate()
            try:
                tunnel.wait(timeout=8)
            except subprocess.TimeoutExpired:
                tunnel.kill()
        receiver.shutdown()
        receiver.server_close()
        thread.join(timeout=5)
        shutil.rmtree(root, ignore_errors=True)


def _probe(url, token):
    try:
        d = request_json(url, token, "/test-only/status", timeout=5)
        return d.get("phase") == "ready"
    except Exception:
        return False


def github_rendezvous():
    guard()
    repo = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]
    token = os.environ["GH_API_TOKEN"]
    api = "https://api.github.com/repos/" + repo
    label = "lot06-c05b03g-private-rendezvous-" + run_id
    deadline = time.monotonic() + 330
    while time.monotonic() < deadline:
        req = urllib.request.Request(
            api + "/actions/runs/" + run_id + "/artifacts?per_page=100",
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                artifacts = json.loads(res.read()).get("artifacts", [])
        except (urllib.error.HTTPError, urllib.error.URLError):
            time.sleep(4)
            continue
        found = next((a for a in artifacts if a["name"] == label and not a["expired"]), None)
        if found:
            req = urllib.request.Request(
                api + "/actions/artifacts/" + str(found["id"]) + "/zip",
                headers={"Authorization": "Bearer " + token,
                         "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(req, timeout=25) as res:
                archive = res.read()
            with zipfile.ZipFile(io.BytesIO(archive)) as z:
                data = json.loads(z.read("rendezvous-private.json"))
            ensure(data["head_sha"] == os.environ["EXPECTED_SHA"], "RENDEZVOUS_SHA_MISMATCH")
            ensure(data["run_id"] == run_id, "RENDEZVOUS_RUN_MISMATCH")
            ensure(re.fullmatch(r"https://[a-z0-9-]+\.trycloudflare\.com",
                                data["url"]) is not None, "RENDEZVOUS_HOST_INVALID")
            ensure(len(data["token"]) > 35, "RENDEZVOUS_TOKEN_INVALID")
            return data
        time.sleep(4)
    raise AssertionError("SERVER_RENDEZVOUS_NOT_PUBLISHED")


def wait_phase(url, token, phase):
    deadline = time.monotonic() + PHASE_TIMEOUT_S
    while time.monotonic() < deadline:
        d = request_json(url, token, "/test-only/status")
        if d["phase"] == phase and d["start_at"] is not None:
            return float(d["start_at"])
        if d["phase"] == "finished":
            raise AssertionError("SHARED_RECEIVER_FINISHED_EARLY")
        time.sleep(.25)
    raise AssertionError("REMOTE_PHASE_BARRIER_NOT_RELEASED_" + phase)


def post_bytes(url, token, cap):
    data = payload(cap)
    req = urllib.request.Request(
        url + "/test-only/incoming", data=data,
        method="POST", headers={"X-Lab-Token": token,
                                "X-Capture": cap, "Content-Type": "image/png"},
    )
    began = time.perf_counter()
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                ensure(response.status == 201, "REMOTE_NOT_CREATED")
                return (time.perf_counter() - began) * 1000
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                # If an HTTP ACK was lost, re-sending is a duplicate;
                # server validates deterministic synthetic bytes and source.
                if attempt > 0:
                    return (time.perf_counter() - began) * 1000
                raise
            if exc.code not in (429, 502, 503, 504, 520, 522, 530) or attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(.5 * (attempt + 1))
    raise AssertionError("REMOTE_UPLOAD_FAILED")


def send_phase(url, token, label, phase, start_at):
    while time.time() < start_at:
        time.sleep(.01)
    begin = time.perf_counter()
    ns = names(label, phase)
    with ThreadPoolExecutor(max_workers=(2 if phase == "two" else 6)) as pool:
        futures = [pool.submit(post_bytes, url, token, cap) for cap in ns]
        ms = [f.result(timeout=115) for f in as_completed(futures)]
    elapsed = time.perf_counter() - begin
    ordered = sorted(ms)
    return {"files": len(ns), "elapsed_s": round(elapsed, 3),
            "requests_per_s": round(len(ns) / elapsed, 2),
            "p95_ms": round(ordered[min(len(ordered)-1, int(.95*len(ordered)))], 2)}


def run_client(label):
    guard()
    ensure(label in CLIENTS, "WRONG_RUNNER_LABEL")
    room = github_rendezvous()
    url, token = room["url"], room["token"]
    request_json(url, token, "/test-only/ready", {"label": label})
    metrics = {}
    for phase in ("two", "bulk", "flood"):
        start = wait_phase(url, token, phase)
        metrics[phase] = send_phase(url, token, label, phase, start)
        request_json(url, token, "/test-only/" + phase + "-done", {"label": label})
        print("LOT06C05B03G_REMOTE_" + phase.upper() + "_CLIENT_PASS", flush=True)
    report = {
        "kind": "LOT06_C05B03G_REAL_REMOTE_CLIENT_PROOF",
        "head_sha": os.environ["EXPECTED_SHA"],
        "run_id": os.environ["GITHUB_RUN_ID"],
        "label": label,
        "uploads": sum(x["files"] for x in metrics.values()),
        "metrics": metrics,
        "real_https_to_single_shared_test_server": True,
        "source_files_synthetic": True,
        "clinical_receipt_issued": False,
        "physical_powercut_tested": False,
        "product_ready": False,
    }
    Path("client-proof.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("LOT06C05B03G_REMOTE_CLIENT_COMPLETE_PASS", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("server", "client"))
    parser.add_argument("--label", choices=tuple(CLIENTS))
    a = parser.parse_args()
    if a.role == "server":
        run_host()
    else:
        ensure(a.label is not None, "CLIENT_LABEL_REQUIRED")
        run_client(a.label)


if __name__ == "__main__":
    main()
