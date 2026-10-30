"""LOT06-C05B-03H — five *real* GitHub-hosted Ubuntu VMs, one TEST HotFolder.

One server job + four remote client jobs, over a private ephemeral Tailscale
network. Not Docker; all hosts must have a distinct Tailscale source IPv4.
Requires external Tailnet configuration and GitHub OIDC secrets (see workflow).
Synthetic PNG ONLY. No clinical upload, patient material, production or ACK.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from http.server import ThreadingHTTPServer
import io
import ipaddress
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import socket
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from isolated_fue_lot06c.qa_multi_ubuntu_hotfolder_stress_v15 import (
    Receiver, payload, new_collector,
)
from isolated_fue_lot06c.qa_shared_server_crosshost_stress_v15 import (
    CAPACITY, CLIENTS, PrivateHandler, names, verify,
)
from tools.imaging_gateway import HotFolder

PORT = 7077
TOTAL_HEALTHY = 152
TOTAL_RECEIVED = 216
TAILNET = ipaddress.IPv4Network("100.64.0.0/10")
STRESS_TAG = "C05B03H_FIVE_REAL_GITHUB_VMS_TEST_ONLY"


def ensure(ok, reason):
    if not ok:
        raise AssertionError(reason)


def valid_ip(ip):
    try:
        return ipaddress.IPv4Address(ip) in TAILNET
    except ipaddress.AddressValueError:
        return False


def guard():
    ensure(os.getenv("ENVIRONMENT") == "test", "TEST_ENVIRONMENT_REQUIRED")
    ensure(os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true",
           "ISOLATED_RUNTIME_REQUIRED")
    ensure(os.getenv("DC06C05B03H_TEST_ONLY") == "1", "LAB_FLAG_REQUIRED")
    ensure(os.getenv("GITHUB_ACTIONS") == "true", "GITHUB_ACTIONS_REQUIRED")
    ensure(os.getenv("RUNNER_ENVIRONMENT") == "github-hosted",
           "FIVE_GITHUB_HOSTED_VMS_REQUIRED")
    ensure(os.getenv("EXPECTED_SHA")
           and os.environ["EXPECTED_SHA"] == os.getenv("GITHUB_SHA_EXACT"),
           "SOURCE_SHA_MISMATCH")
    own_ip = os.getenv("DC06H_TAIL_IP", "")
    ensure(valid_ip(own_ip), "PRIVATE_TAILNET_IPV4_REQUIRED")
    return own_ip


class TailnetReceiver(Receiver):
    request_queue_size = 128

    def __init__(self, watch, token, bind_ip):
        # Bind ONLY to assigned Tailscale interface (100.64.0.0/10);
        # no public interfaces or loopback-proxy endpoints.
        ensure(valid_ip(bind_ip), "NO_PUBLIC_BIND")
        ThreadingHTTPServer.__init__(self, (bind_ip, PORT), TailnetHandler)
        self.watch, self.token = watch, token
        self.write_lock = threading.Lock()
        self.accepted, self.denied = 0, 0
        self.lock = threading.Lock()
        self.ready = set()
        self.progress = {phase: set() for phase in ("two", "bulk", "flood")}
        self.phase, self.start_at = "ready", None
        self.remote_clients = {}
        self.arrivals_two = []


class TailnetHandler(PrivateHandler):
    def do_POST(self):
        server = self.server
        ensure(isinstance(server, TailnetReceiver), "NON_LAB_SERVER")
        source = self.client_address[0]
        if not valid_ip(source):
            self._json(403, {"error": "REMOTE_TAILNET_ONLY"})
            return
        if self.path == "/test-only/ready":
            label = self.headers.get("X-Lab-Label", "")
            if label not in CLIENTS or not self._auth():
                self._json(403, {"error": "INVALID_LAB_IDENTITY"})
                return
            with server.lock:
                prior = server.remote_clients.get(label)
                if prior is not None and prior != source:
                    self._json(409, {"error": "CLIENT_SOURCE_IP_CHANGED"})
                    return
                if source in {ip for k, ip in server.remote_clients.items() if k != label}:
                    self._json(409, {"error": "REUSED_REMOTE_VM_IP"})
                    return
                server.remote_clients[label] = source
        elif self.path == "/test-only/incoming" and self._auth():
            capture = self.headers.get("X-Capture", "")
            parts = capture.split("_")
            if len(parts) >= 4:
                label = parts[1]
                with server.lock:
                    expected = server.remote_clients.get(label)
                    if expected is None or expected != source:
                        self._json(403, {"error": "UNREGISTERED_REMOTE_CLIENT"})
                        return
                    if parts[2] == "two" and server.phase == "two":
                        server.arrivals_two.append(time.time())
        return super().do_POST()


def wait_for(fn, error, timeout=240):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return
        time.sleep(.15)
    raise AssertionError(error)


def phase_done(server, stage):
    with server.lock:
        return len(server.progress[stage]) == 4


def stage(server, phase, delay=5):
    with server.lock:
        server.phase, server.start_at = phase, time.time() + delay


def run_host():
    ip = guard()
    root = Path(tempfile.mkdtemp(prefix="dc06h-private-vm-"))
    token = secrets.token_urlsafe(48)
    agent, config = new_collector(root, CAPACITY)
    server = TailnetReceiver(config.watch, token, ip)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        rendezvous = {
            "schema": STRESS_TAG, "run_id": os.environ["GITHUB_RUN_ID"],
            "expected_sha": os.environ["EXPECTED_SHA"],
            "server_ip": ip, "token": token,
        }
        room = Path("rendezvous-private.json")
        room.write_text(json.dumps(rendezvous, sort_keys=True))
        os.chmod(room, 0o600)
        print("C05B03H_PRIVATE_TAILNET_SERVER_READY", flush=True)
        wait_for(lambda: len(server.ready) == 4, "FOUR_REAL_VM_CLIENTS_NOT_READY",
                 timeout=960)
        with server.lock:
            remote = dict(server.remote_clients)
        ensure(set(remote) == set(CLIENTS), "FOUR_LABELED_VM_MISSING")
        ensure(len(set(remote.values())) == 4, "CLIENT_VMS_SHARE_TAILNET_IP")
        ensure(all(valid_ip(p) and p != ip for p in remote.values()),
               "REMOTE_VM_NOT_SEPARATE_FROM_SERVER")
        stage(server, "two")
        wait_for(lambda: phase_done(server, "two"),
                 "REMOTE_TWO_FILE_BARRIER_FAILED", timeout=200)
        ensure(server.accepted == 8, "SIMULTANEOUS_REMOTE_EIGHT_MISSING")
        with server.lock:
            arrivals = list(server.arrivals_two)
        ensure(len(arrivals) == 8, "REMOTE_TWO_FILE_ARRIVALS_NOT_EIGHT")
        arrival_span = max(arrivals) - min(arrivals)
        ensure(arrival_span <= 12, "SIMULTANEOUS_REMOTE_ARRIVALS_OVER_12_SECONDS")
        print("C05B03H_4_DISTINCT_REAL_REMOTE_VMS_TWO_FILES_PASS", flush=True)

        stage(server, "bulk")
        wait_for(lambda: phase_done(server, "bulk"), "REAL_VM_BULK_FAILED",
                 timeout=260)
        ensure(server.accepted == TOTAL_HEALTHY, "REAL_VM_BULK_RECEIVE_COUNT")
        healthy = [n for label in CLIENTS for phase in ("two", "bulk")
                   for n in names(label, phase)]
        first, second = agent.scan_once(), agent.scan_once()
        ensure(first["unstable"] == TOTAL_HEALTHY, "REAL_READY_STABILITY_LOST")
        ensure(second["staged"] == TOTAL_HEALTHY and second["deferred"] == 0,
               "REAL_SQLITE_152_NOT_STAGED")
        verify(agent, healthy, count=TOTAL_HEALTHY)
        ensure(server.denied == 4, "FOUR_EXPLICIT_REMOTE_DUPLICATE_409_MISSING")
        print("C05B03H_152_REMOTE_FILES_ENCRYPTED_4_DUPLICATES_REJECTED",
              flush=True)

        stage(server, "flood")
        wait_for(lambda: phase_done(server, "flood"),
                 "REMOTE_FOUR_VM_FLOOD_INCOMPLETE", timeout=260)
        ensure(server.accepted == TOTAL_RECEIVED, "REMOTE_216_NOT_RECEIVED")
        extra = [n for label in CLIENTS for n in names(label, "flood")]
        a, b = agent.scan_once(), agent.scan_once()
        ensure(a["unstable"] == 64, "REMOTE_FLOOD_STABILITY_MISSING")
        ensure(b["staged"] == 8 and b["deferred"] == 56,
               "REMOTE_BACKPRESSURE_NOT_ENFORCED")
        state = verify(agent, healthy + extra, count=CAPACITY)
        ensure(state["state"] == "BACKPRESSURE", "BACKPRESSURE_STATE_LOST")
        assert all((config.watch / (n + ".png")).read_bytes() == payload(n)
                   and (config.watch / (n + ".png.ready")).exists()
                   for n in healthy + extra), "REMOTE_ORIGINAL_SOURCE_LOSS"
        restart = HotFolder(config)
        restart.scan_once()
        again = restart.scan_once()
        ensure(again["staged"] == 0 and len(restart.items()) == CAPACITY,
               "DUPLICATE_AFTER_COLD_RESTART")
        proof = {
            "kind": STRESS_TAG, "expected_sha": os.environ["EXPECTED_SHA"],
            "run_id": os.environ["GITHUB_RUN_ID"],
            "server_runner_hostname": socket.gethostname(),
            "server_runner_name": os.getenv("RUNNER_NAME", ""),
            "server_tailscale_ipv4": ip, "client_src_ipv4": remote,
            "number_of_distinct_remote_client_tailnet_ips": len(set(remote.values())),
            "simultaneous_two_file_arrival_span_ms": round(arrival_span * 1000, 1),
            "all_remote_ubuntu_jobs_joined": True,
            "http_received": TOTAL_RECEIVED,
            "sqlite_aesgcm_queued": CAPACITY,
            "deferred_sources_unchanged": TOTAL_RECEIVED - CAPACITY,
            "duplicate_http_409_rejected": 4,
            "sha_aead_audit_validated": True, "cold_restart_no_duplicates": True,
            "network": "TAILSCALE_PRIVATE_WIREGUARD_FIVE_GITHUB_HOSTED_VMS",
            "containers_substituted_for_remote_vms": False,
            "clinical_ack_issued": False, "product_ready": False,
        }
        Path("server-proof.json").write_text(
            json.dumps(proof, sort_keys=True, indent=2) + "\n")
        print("C05B03H_TRUE_FIVE_VM_ONE_SERVER_216_160_56_PASS", flush=True)
    finally:
        with server.lock:
            server.phase = "finished"
        server.shutdown()
        server.server_close()
        t.join(timeout=5)
        shutil.rmtree(root, ignore_errors=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_artifact_rendezvous():
    token = os.getenv("GH_API_TOKEN", "")
    ensure(len(token) >= 12, "GITHUB_ACTIONS_READ_TOKEN_REQUIRED")
    repo, run_id = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_RUN_ID"]
    api = "https://api.github.com/repos/" + repo
    name = "lot06-c05b03h-private-room-" + run_id
    headers = {"Authorization": "Bearer " + token,
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    stop_redirects = urllib.request.build_opener(NoRedirect())
    until = time.monotonic() + 870
    while time.monotonic() < until:
        req = urllib.request.Request(
            api + "/actions/runs/" + run_id + "/artifacts?per_page=100",
            headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=18) as result:
                records = json.loads(result.read())["artifacts"]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            time.sleep(5)
            continue
        match = next((x for x in records
                      if x["name"] == name and not x["expired"]), None)
        if match is None:
            time.sleep(5)
            continue
        req = urllib.request.Request(
            api + "/actions/artifacts/" + str(match["id"]) + "/zip",
            headers=headers)
        try:
            with stop_redirects.open(req, timeout=20) as result:
                data = result.read()
        except urllib.error.HTTPError as e:
            ensure(e.code in (301, 302, 303, 307, 308),
                   "GITHUB_ARTIFACT_DOWNLOAD_HTTP_" + str(e.code))
            # GitHub signs a separate, short-lived blob URL. Never forward the
            # GitHub Bearer header to storage, fixing prior HTTP 401/302.
            signed = e.headers.get("Location", "")
            parsed = urllib.parse.urlsplit(signed)
            ensure(parsed.scheme == "https" and parsed.hostname
                   and parsed.hostname != "api.github.com",
                   "INVALID_SIGNED_ARTIFACT_REDIRECT")
            with urllib.request.urlopen(signed, timeout=30) as result:
                data = result.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            room = json.loads(z.read("rendezvous-private.json"))
        ensure(room["schema"] == STRESS_TAG, "WRONG_RENDEZVOUS_KIND")
        ensure(room["run_id"] == run_id, "REPLAYED_GITHUB_RUN_ID")
        ensure(room["expected_sha"] == os.environ["EXPECTED_SHA"],
               "REPLAYED_COMMIT_SHA")
        ensure(valid_ip(room["server_ip"]), "RECEIVER_NOT_PRIVATE")
        ensure(len(room["token"]) >= 60, "WEAK_TEST_ONLY_TOKEN")
        return room
    raise AssertionError("PRIVATE_SERVER_RENDEZVOUS_TIMEOUT")


def req_json(url, token, path, data=None, label=None):
    headers = {"X-Lab-Token": token, "Cache-Control": "no-store"}
    if label:
        headers["X-Lab-Label"] = label
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data, separators=(",", ":")).encode()
    req = urllib.request.Request(url + path, headers=headers, data=data,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=18) as reply:
        return json.loads(reply.read())


def wait_for_phase(url, token, phase):
    until = time.monotonic() + 260
    while time.monotonic() < until:
        state = req_json(url, token, "/test-only/status")
        if state["phase"] == phase and state["start_at"] is not None:
            return float(state["start_at"])
        if state["phase"] == "finished":
            raise AssertionError("SERVER_FINISHED_EARLY")
        time.sleep(.17)
    raise AssertionError("MISSING_REMOTE_PHASE_" + phase)


def send_one(url, token, name, expected_duplicate=False):
    data = payload(name)
    req = urllib.request.Request(
        url + "/test-only/incoming", data=data, method="POST",
        headers={"X-Lab-Token": token, "X-Capture": name,
                 "Content-Type": "image/png"})
    had_transient = False
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                ensure(not expected_duplicate and r.status == 201,
                       "DUPLICATE_ACCEPTED_OR_RESPONSE_WRONG")
            return name
        except urllib.error.HTTPError as e:
            if e.code == 409 and (expected_duplicate or had_transient):
                return name
            raise
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError,
                TimeoutError, urllib.error.URLError):
            had_transient = True
            if attempt == 3:
                raise
            time.sleep(.4 * (attempt + 1))
    raise AssertionError("REMOTE_TRANSPORT_RETRY_EXHAUSTED")


def run_client(label):
    ip = guard()
    ensure(label in CLIENTS, "INVALID_REMOTE_VM_LABEL")
    room = github_artifact_rendezvous()
    url = "http://" + room["server_ip"] + ":" + str(PORT)
    token = room["token"]
    until = time.monotonic() + 180
    while True:
        try:
            req_json(url, token, "/test-only/ready", {"label": label}, label)
            break
        except (urllib.error.URLError, TimeoutError):
            ensure(time.monotonic() < until, "WIREGUARD_PEER_NOT_REACHABLE")
            time.sleep(.5)
    metrics = {}
    for phase in ("two", "bulk", "flood"):
        start = wait_for_phase(url, token, phase)
        while time.time() < start:
            time.sleep(.015)
        batch = names(label, phase)
        begun = time.monotonic()
        with ThreadPoolExecutor(max_workers=2 if phase == "two" else 6) as pool:
            futures = [pool.submit(send_one, url, token, n) for n in batch]
            delivered = [f.result(timeout=90) for f in as_completed(futures)]
        ensure(set(delivered) == set(batch), "REMOTE_SEND_INCOMPLETE")
        elapsed = time.monotonic() - begun
        if phase == "bulk":
            send_one(url, token, batch[0], expected_duplicate=True)
        metrics[phase] = {"files": len(batch),
                          "elapsed_s": round(elapsed, 4),
                          "files_per_s": round(len(batch) / elapsed, 2)}
        req_json(url, token, "/test-only/" + phase + "-done", {"label": label})
        print("C05B03H_REAL_VM_" + label + "_" + phase + "_PASS", flush=True)
    proof = {
        "kind": STRESS_TAG, "run_id": os.environ["GITHUB_RUN_ID"],
        "expected_sha": os.environ["EXPECTED_SHA"], "label": label,
        "sender_vm_hostname": socket.gethostname(),
        "sender_vm_runner_name": os.getenv("RUNNER_NAME", ""),
        "sender_vm_tailnet_ipv4": ip,
        "server_tailnet_ipv4": room["server_ip"],
        "source_container_mode": False, "github_hosted_runner_vm": True,
        "files_sent": sum(m["files"] for m in metrics.values()),
        "one_explicit_duplicate_http_409": True, "metrics": metrics,
        "clinical_ack_issued": False, "product_ready": False,
    }
    Path("client-proof.json").write_text(
        json.dumps(proof, sort_keys=True, indent=2) + "\n")
    print("C05B03H_REAL_GITHUB_VM_SENDER_COMPLETE_" + label, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("server", "client"))
    parser.add_argument("--label", choices=list(CLIENTS))
    args = parser.parse_args()
    if args.role == "server":
        run_host()
    else:
        ensure(args.label, "MISSING_REMOTE_CLIENT_LABEL")
        run_client(args.label)


if __name__ == "__main__":
    main()
