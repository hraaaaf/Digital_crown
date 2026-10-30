"""LOT06 C05B-03G: FOUR isolated Ubuntu Docker clients -> ONE shared Docker-server.
Only a private Docker bridge, NEVER a public tunnel or cabinet service.
Actual HotFolder SQLite/AES-GCM spool, synthetic PNG, no real clinical ACK.
Different container IPs/network namespaces on ONE GitHub host; NOT four VMs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time

from isolated_fue_lot06c.qa_multi_ubuntu_hotfolder_stress_v15 import (
    Receiver, payload, new_collector,
)
from tools.imaging_gateway import HotFolder

CLIENTS = {"u22a": 24, "u22b": 48, "u24a": 24, "u24b": 48}
TOTAL_HEALTHY = 8 + sum(CLIENTS.values())
TOTAL_RECEIVED = TOTAL_HEALTHY + 4 * 16
CAPACITY = 160

# The reusable deterministic barriers and SHA/AES-GCM/SQLite oracles from
# the prior C05B-03G lab file are intentionally reproduced here. No network
# exposure or remote GitHub token is required for this Docker-only harness.
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.error
import urllib.request

def guard():
    if not (os.getenv("ENVIRONMENT") == "test"
            and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
            and os.getenv("DC06C05B03G_TEST_ONLY") == "1"
            and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("EXPECTED_SHA")
            and os.getenv("EXPECTED_SHA") == os.getenv("GITHUB_SHA_EXACT")):
        raise RuntimeError("C05B03G_PRIVATE_DOCKER_TEST_ONLY")
    token = os.getenv("DC06G_TEST_TOKEN", "")
    if len(token) < 36:
        raise RuntimeError("C05B03G_EPHEMERAL_TEST_TOKEN_REQUIRED")
    return token

def ensure(value, code):
    if not value:
        raise AssertionError(code)

def names(label, phase):
    count = CLIENTS[label] if phase == "bulk" else (2 if phase == "two" else 16)
    return [f"stress_{label}_{phase}_{i:05d}" for i in range(count)]

class PrivateReceiver(Receiver):
    # 4 independent clients x up to 6 concurrent HTTP sends each. The
    # default TCPServer backlog=5 causes SYN resets under the flood FUE.
    request_queue_size = 128

    def __init__(self, watch, token):
        # Explicit TEST-only Docker bridge ingress. No -p/published ports.
        ThreadingHTTPServer.__init__(self, ("0.0.0.0", 7077), PrivateHandler)
        self.watch, self.token = watch, token
        self.write_lock = threading.Lock()
        self.accepted, self.denied = 0, 0
        self.lock = threading.Lock()
        self.ready = set()
        self.progress = {p: set() for p in ("two", "bulk", "flood")}
        self.phase = "ready"
        self.start_at = None
        self.accepted_by_phase = Counter()

class PrivateHandler(__import__(
    "isolated_fue_lot06c.qa_multi_ubuntu_hotfolder_stress_v15",
    fromlist=["ReceiverHandler"]).ReceiverHandler):
    def _json(self, status, obj):
        data = json.dumps(obj, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _auth(self):
        return secrets.compare_digest(self.headers.get("X-Lab-Token", ""),
                                      self.server.token)

    def do_GET(self):
        if not self._auth() or self.path != "/test-only/status":
            self._json(403, {"error": "LAB_AUTH_REQUIRED"})
            return
        with self.server.lock:
            reply = {"phase": self.server.phase,
                     "start_at": self.server.start_at,
                     "ready_count": len(self.server.ready)}
        self._json(200, reply)

    def do_POST(self):
        server = self.server
        if self.path == "/test-only/incoming":
            if not self._auth():
                self._json(403, {"error": "LAB_AUTH_REQUIRED"})
                return
            capture = self.headers.get("X-Capture", "")
            match = re.fullmatch(
                r"stress_(u22a|u22b|u24a|u24b)_(two|bulk|flood)_[0-9]{5}",
                capture,
            )
            if not match or capture not in names(match.group(1), match.group(2)):
                self._json(422, {"error": "UNKNOWN_SYNTHETIC_CAPTURE"})
                return
            with server.lock:
                phase = server.phase
            if phase != match.group(2):
                self._json(409, {"error": "PHASE_BLOCKED"})
                return
            return super().do_POST()
        if not self._auth():
            self._json(403, {"error": "LAB_AUTH_REQUIRED"})
            return
        match = re.fullmatch(
            r"/test-only/(ready|two-done|bulk-done|flood-done)", self.path)
        size = self.headers.get("Content-Length", "")
        if not match or not size.isdecimal() or not 0 < int(size) <= 120:
            self._json(422, {"error": "INVALID_CONTROL"})
            return
        try:
            record = json.loads(self.rfile.read(int(size)))
        except (UnicodeError, ValueError):
            self._json(422, {"error": "INVALID_CONTROL_JSON"})
            return
        label = record.get("label") if isinstance(record, dict) else None
        if label not in CLIENTS:
            self._json(422, {"error": "UNKNOWN_TEST_CLIENT"})
            return
        command = match.group(1)
        with server.lock:
            if command == "ready":
                if server.phase != "ready":
                    self._json(409, {"error": "LATE_CLIENT"})
                    return
                server.ready.add(label)
            else:
                phase = command.replace("-done", "")
                if server.phase != phase or label not in server.ready:
                    self._json(409, {"error": "WRONG_PHASE"})
                    return
                server.progress[phase].add(label)
        self._json(200, {"ok": True})

def wait_for(check, code, seconds=120):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if check():
            return
        time.sleep(.15)
    raise AssertionError(code)

def phase_progress(server, name):
    with server.lock:
        return len(server.progress[name])

def verify(agent, expected, *, count):
    rows = agent.items()
    ensure(len(rows) == count, "SQLITE_QUEUE_COUNT_MISMATCH")
    ensure(all(r["state"] == "PENDING_CONFIRMATION" for r in rows),
           "FALSE_CLINICAL_CONFIRMATION")
    originals = Counter(hashlib.sha256(payload(n)).hexdigest() for n in expected)
    actual = Counter(r["digest"] for r in rows)
    ensure(not (actual - originals), "WRONG_CLIENT_DATA")
    for row in rows:
        body = agent.read_verified(row["id"])
        ensure(hashlib.sha256(body).hexdigest() == row["digest"],
               "AES_GCM_READBACK_OR_SHA_FAILED")
        ensure(agent.audit(row["id"]) == ["PENDING_CONFIRMATION"],
               "AUDIT_INCONSISTENT")
    return agent.storage_health()

def run_server():
    token = guard()
    root = Path(tempfile.mkdtemp(prefix="lot06c05b03g-private-"))
    agent, config = new_collector(root, CAPACITY)
    server = PrivateReceiver(config.watch, token)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        wait_for(lambda: len(server.ready) == 4,
                 "FOUR_ISOLATED_CONTAINERS_NOT_READY", seconds=120)
        with server.lock:
            server.phase, server.start_at = "two", time.time() + 2.5
        wait_for(lambda: phase_progress(server, "two") == 4,
                 "TWO_SIMULTANEOUS_PER_CLIENT_INCOMPLETE")
        ensure(server.accepted == 8, "FIRST_EIGHT_FILES_MISSING")
        print("LOT06C05B03G_PRIVATE_FOUR_CLIENTS_SIMULTANEOUS_TWO_PASS", flush=True)
        with server.lock:
            server.phase, server.start_at = "bulk", time.time() + 2
        wait_for(lambda: phase_progress(server, "bulk") == 4,
                 "MULTI_CONTAINER_BULK_INCOMPLETE", seconds=150)
        ensure(server.accepted == TOTAL_HEALTHY, "BULK_HTTP_COUNT")
        seen = [n for label in CLIENTS for phase in ("two", "bulk")
                for n in names(label, phase)]
        first, second = agent.scan_once(), agent.scan_once()
        ensure(first["unstable"] == TOTAL_HEALTHY,
               "FIRST_SCAN_STABILITY_GATE_MISSING")
        ensure(second["staged"] == TOTAL_HEALTHY and second["deferred"] == 0,
               "REAL_QUEUE_NOT_STAGING_152")
        verify(agent, seen, count=TOTAL_HEALTHY)
        print("LOT06C05B03G_ONE_SHARED_HOTFOLDER_152_AES_SQLITE_PASS", flush=True)
        with server.lock:
            server.phase, server.start_at = "flood", time.time() + 2
        wait_for(lambda: phase_progress(server, "flood") == 4,
                 "FOUR_CONCURRENT_FLOOD_CLIENTS_INCOMPLETE")
        ensure(server.accepted == TOTAL_RECEIVED, "216_HTTP_FILES_NOT_RECEIVED")
        extra = [n for label in CLIENTS for n in names(label, "flood")]
        a, b = agent.scan_once(), agent.scan_once()
        ensure(a["unstable"] == 64, "FLOOD_FILE_STABILITY_MISSING")
        ensure(b["staged"] == 8 and b["deferred"] == 56,
               "QUEUE_BACKPRESSURE_WRONG")
        state = verify(agent, seen + extra, count=CAPACITY)
        ensure(state["state"] == "BACKPRESSURE", "BACKPRESSURE_STATE_MISSING")
        directory = config.watch
        expected_names = set(seen + extra)
        actual_names = {p.stem for p in directory.glob("*.png")}
        ensure(actual_names == expected_names, "SOURCE_FILE_LOSS")
        ensure(len(list(directory.glob("*.png.ready"))) == TOTAL_RECEIVED,
               "SOURCE_MANIFEST_LOSS")
        for n in expected_names:
            ensure((directory / (n + ".png")).read_bytes() == payload(n),
                   "SOURCE_HASH_MISMATCH")
        print("LOT06C05B03G_SHARED_QUEUE_160_AND_56_SOURCES_DEFERRED_PASS",
              flush=True)
        restarted = HotFolder(config)
        restarted.scan_once()
        last = restarted.scan_once()
        ensure(last["staged"] == 0 and len(restarted.items()) == CAPACITY,
               "RESTART_REPLAY_CREATED_DUPLICATES")
        report = {
            "kind": "LOT06_C05B03G_PRIVATE_DOCKER_MULTI_UBUNTU",
            "head_sha": os.environ["EXPECTED_SHA"],
            "client_count": 4,
            "container_os": {"u22a": "ubuntu22", "u22b": "ubuntu22",
                             "u24a": "ubuntu24", "u24b": "ubuntu24"},
            "received_http": TOTAL_RECEIVED,
            "encrypted_sqlite_queued": CAPACITY,
            "deferred_sources_intact": TOTAL_RECEIVED - CAPACITY,
            "two_concurrent_files_per_client": True,
            "aes_gcm_and_sha_verified": True,
            "cold_restart_without_duplication": True,
            "network_boundary": "private_docker_bridge_only",
            "four_distinct_github_vms_tested": False,
            "public_endpoint_created": False,
            "clinical_upload_ack": False,
            "product_ready": False,
        }
        Path("server-proof.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("LOT06C05B03G_FOUR_UBUNTU_PRIVATE_NETWORK_SHARED_SERVER_PASS",
              flush=True)
    finally:
        with server.lock:
            server.phase = "finished"
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)

def request_json(url, token, path, data=None):
    headers = {"X-Lab-Token": token}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    req = urllib.request.Request(url + path, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=12) as reply:
        return json.loads(reply.read())

def wait_phase(url, token, phase):
    until = time.monotonic() + 145
    while time.monotonic() < until:
        try:
            info = request_json(url, token, "/test-only/status")
        except (urllib.error.URLError, TimeoutError):
            time.sleep(.25)
            continue
        if info["phase"] == phase and info["start_at"] is not None:
            return float(info["start_at"])
        if info["phase"] == "finished":
            raise AssertionError("SERVER_FINISHED_BEFORE_CLIENT")
        time.sleep(.1)
    raise AssertionError("CLIENT_BARRIER_TIMEOUT_" + phase)

def send_one(url, token, capture):
    """Bounded transport retry: acknowledge 409 only after a lost-ACK attempt.

    All remote source counts, AES payload hashes and source .ready manifests
    are independently checked by the server at the end, so retry cannot
    manufacture a green file result.
    """
    blob = payload(capture)
    req = urllib.request.Request(url + "/test-only/incoming", data=blob,
                                 method="POST",
                                 headers={"X-Lab-Token": token,
                                          "X-Capture": capture,
                                          "Content-Type": "image/png"})
    had_transient = False
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=18) as r:
                ensure(r.status == 201, "FILE_SEND_NOT_201")
            return capture
        except urllib.error.HTTPError as exc:
            # A first 409 is an error; after an ACK loss, server may already
            # have written exact deterministic bytes and refuse a duplicate.
            # Final server-side SHA+ready+216-count checks are mandatory.
            if exc.code == 409 and had_transient:
                return capture
            raise
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError,
                TimeoutError, urllib.error.URLError):
            had_transient = True
            if attempt == 3:
                raise
            time.sleep(.18 * (attempt + 1))
    raise AssertionError("FILE_SEND_RETRY_EXHAUSTED")

def run_client(label):
    token = guard()
    ensure(label in CLIENTS, "UNKNOWN_UBUNTU_CONTAINER")
    url = "http://dc06g-server:7077"
    until = time.monotonic() + 80
    while True:
        try:
            request_json(url, token, "/test-only/ready", {"label": label})
            break
        except (urllib.error.URLError, TimeoutError):
            ensure(time.monotonic() < until, "PRIVATE_SERVER_UNREACHABLE")
            time.sleep(.3)
    metrics = {}
    for phase in ("two", "bulk", "flood"):
        target = wait_phase(url, token, phase)
        while time.time() < target:
            time.sleep(.01)
        began = time.monotonic()
        caps = names(label, phase)
        with ThreadPoolExecutor(max_workers=2 if phase == "two" else 6) as pool:
            futures = [pool.submit(send_one, url, token, capture) for capture in caps]
            delivered = [f.result(timeout=60) for f in as_completed(futures)]
        ensure(set(delivered) == set(caps), "CLIENT_SENT_FILES_MISSING")
        elapsed = time.monotonic() - began
        metrics[phase] = {"files": len(caps),
                          "elapsed_s": round(elapsed, 3),
                          "files_per_s": round(len(caps) / elapsed, 2)}
        request_json(url, token, "/test-only/" + phase + "-done",
                     {"label": label})
    report = {"label": label, "head_sha": os.environ["EXPECTED_SHA"],
              "files_sent": sum(v["files"] for v in metrics.values()),
              "metrics": metrics,
              "same_server_dns": "dc06g-server",
              "isolated_private_docker_client": True,
              "real_remote_github_vm_client": False,
              "clinical_receipt": False}
    Path("client-proof.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("LOT06C05B03G_PRIVATE_UBUNTU_CLIENT_PASS", label, flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("role", choices=("server", "client"))
    ap.add_argument("--label", choices=tuple(CLIENTS))
    a = ap.parse_args()
    if a.role == "server":
        run_server()
    else:
        ensure(a.label is not None, "CLIENT_LABEL_REQUIRED")
        run_client(a.label)

if __name__ == "__main__":
    main()
