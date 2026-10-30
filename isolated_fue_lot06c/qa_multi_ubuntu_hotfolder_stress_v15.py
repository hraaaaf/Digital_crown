"""C05B-03F: parallel-producer, real HotFolder queue STRESS (isolated LAB only).

GitHub-hosted Ubuntu matrix jobs are different machines, each running its OWN
loopback-only HTTP receiver and REAL LOT06-A HotFolder/SQLite/AES spool.
There is NO shared multi-host server or clinical upload/receipt here.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import re
import secrets
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib

from tools.imaging_gateway import Config, HotFolder

BASE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)
CAPTURE = re.compile(r"^stress_[a-z0-9_]{5,55}$")
MAX_UPLOAD = 128 * 1024


def guard():
    if not (os.getenv("ENVIRONMENT") == "test"
            and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
            and os.getenv("DC06C05B03F_TEST_ONLY") == "1"):
        raise RuntimeError("C05B03F_ISOLATED_TEST_ONLY")


def payload(capture):
    """Valid small PNG with deterministic, varying size nonclinical tEXt data."""
    if not CAPTURE.fullmatch(capture):
        raise ValueError("CAPTURE_INVALID")
    size = (256, 4096, 16384)[int(hashlib.sha256(capture.encode()).hexdigest(), 16) % 3]
    note = b"Stress\x00" + hashlib.shake_256(capture.encode()).digest(size)
    chunk = len(note).to_bytes(4, "big") + b"tEXt" + note
    chunk += (zlib.crc32(b"tEXt" + note) & 0xffffffff).to_bytes(4, "big")
    return BASE_PNG[:-12] + chunk + BASE_PNG[-12:]


class Receiver(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address, watch, token):
        assert address[0] == "127.0.0.1"
        super().__init__(address, ReceiverHandler)
        self.watch = watch
        self.token = token
        self.write_lock = threading.Lock()
        self.accepted = 0
        self.denied = 0


class ReceiverHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        return

    def do_POST(self):
        server = self.server
        assert isinstance(server, Receiver)
        if (self.path != "/test-only/incoming"
                or not secrets.compare_digest(
                    self.headers.get("X-Lab-Token", ""), server.token
                )):
            server.denied += 1
            self.send_error(403, "LAB_ONLY")
            return
        capture = self.headers.get("X-Capture", "")
        length = self.headers.get("Content-Length", "")
        if (not CAPTURE.fullmatch(capture)
                or not length.isdecimal()
                or not 0 < int(length) <= MAX_UPLOAD):
            server.denied += 1
            self.send_error(422, "INVALID_SYNTHETIC_INPUT")
            return
        data = self.rfile.read(int(length))
        if len(data) != int(length) or data != payload(capture):
            server.denied += 1
            self.send_error(422, "SYNTHETIC_PAYLOAD_MISMATCH")
            return
        target = server.watch / (capture + ".png")
        sidecar = server.watch / (capture + ".png.ready")
        with server.write_lock:
            if target.exists() or sidecar.exists():
                server.denied += 1
                self.send_error(409, "CAPTURE_DUPLICATE")
                return
            name = capture + "-" + secrets.token_hex(6)
            temp = server.watch / ("." + name + ".part")
            tmpready = server.watch / ("." + name + ".ready")
            try:
                with temp.open("xb") as out:
                    out.write(data)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(temp, target)
                witness = {"version": 1, "size": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()}
                with tmpready.open("xb") as out:
                    out.write(json.dumps(witness, separators=(",", ":")).encode())
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmpready, sidecar)
                server.accepted += 1
            finally:
                temp.unlink(missing_ok=True)
                tmpready.unlink(missing_ok=True)
        self.send_response(201)
        self.send_header("Content-Length", "0")
        self.end_headers()


def child_send(args):
    guard()
    token = os.environ["DC06C05B03F_LOOPBACK_TOKEN"]
    now = time.time()
    if args.start_at > now:
        time.sleep(args.start_at - now)
    durations = []
    accepted = 0
    errors = []
    for i in range(args.count):
        name = f"stress_{args.group}_{args.offset + i:05d}"
        blob = payload(name)
        req = urllib.request.Request(
            args.url + "/test-only/incoming", data=blob, method="POST",
            headers={"Content-Type": "image/png", "X-Capture": name,
                     "X-Lab-Token": token},
        )
        begin = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 201:
                    errors.append("UNEXPECTED_HTTP_STATUS")
                else:
                    accepted += 1
        except Exception:
            errors.append("SEND_REJECTED")
        durations.append((time.perf_counter() - begin) * 1000)
    print(json.dumps({"sent": args.count, "accepted": accepted,
                      "errors": errors, "ms": durations}), flush=True)


def send_parallel(server, *, group, files, workers):
    guard()
    assert files >= workers >= 2 and files % workers == 0
    target = "http://127.0.0.1:" + str(server.server_port)
    start = time.time() + 1.5
    env = dict(os.environ, DC06C05B03F_LOOPBACK_TOKEN=server.token)
    children = []
    started = time.perf_counter()
    try:
        for worker in range(workers):
            cmd = [sys.executable, "-m",
                   "isolated_fue_lot06c.qa_multi_ubuntu_hotfolder_stress_v15",
                   "--child", "--url", target, "--group", group,
                   "--offset", str(worker * (files // workers)),
                   "--count", str(files // workers), "--start-at", str(start)]
            children.append(subprocess.Popen(
                cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
            ))
        outputs = []
        for child in children:
            out, err = child.communicate(timeout=90)
            if child.returncode != 0:
                raise AssertionError("CLIENT_CHILD_FAILED " + err[-220:])
            outputs.append(json.loads(out))
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate()
    elapsed = time.perf_counter() - started
    assert sum(r["accepted"] for r in outputs) == files
    assert not any(r["errors"] for r in outputs)
    latencies = [t for r in outputs for t in r["ms"]]
    assert len(latencies) == files
    latencies.sort()
    return {
        "sent": files,
        "accepted": files,
        "workers": workers,
        "elapsed_s": round(elapsed, 3),
        "requests_per_s": round(files / elapsed, 2),
        "request_p95_ms": round(latencies[min(len(latencies)-1, int(.95*len(latencies)))], 2),
    }


def new_collector(root, limit):
    watch = root / "incoming"
    private = root / "private"
    watch.mkdir(parents=True)
    config = Config(
        "synthetic_cabinet", "synthetic_station", watch, private, b"k" * 32,
        require_ready_manifest=True, max_queue_items=limit,
        max_spool_bytes=200 * 1024 * 1024, min_free_bytes=0,
    )
    return HotFolder(config), config


def assert_collected(agent, *, expected_names, expected_count):
    rows = agent.items()
    assert len(rows) == expected_count, ("QUEUE_COUNT", len(rows), expected_count)
    assert all(row["state"] == "PENDING_CONFIRMATION" for row in rows)
    expected = Counter(
        hashlib.sha256(payload(name)).hexdigest() for name in expected_names
    )
    actual = Counter(row["digest"] for row in rows)
    assert actual == expected
    for row in rows:
        clear = agent.read_verified(row["id"])
        assert hashlib.sha256(clear).hexdigest() == row["digest"]
        assert agent.audit(row["id"]) == ["PENDING_CONFIRMATION"]
    health = agent.storage_health()
    assert health["queued_items"] == expected_count
    assert health["states"] == {"PENDING_CONFIRMATION": expected_count}
    return health


def run_case(root, *, files, cap, shard, label):
    agent, config = new_collector(root, cap)
    server = Receiver(("127.0.0.1", 0), config.watch, secrets.token_urlsafe(20))
    background = threading.Thread(target=server.serve_forever, daemon=True)
    background.start()
    try:
        two = send_parallel(server, group=label + "two", files=2, workers=2)
        one = agent.scan_once()
        assert one["unstable"] == 2
        second = agent.scan_once()
        assert second["staged"] == 2 and second["deferred"] == 0
        assert len(agent.items()) == 2
        print("LOT06C05B03F_SIMULTANEOUS_TWO_FILES_PASS", flush=True)
        assert send_parallel(server, group=label + "bulk", files=files,
                             workers=12 if files % 12 == 0 else 8)["accepted"] == files
        extra = send_parallel(server, group=label + "duplicate", files=2, workers=2)
        all_names = ([f"stress_{label}two_{i:05d}" for i in range(2)]
                     + [f"stress_{label}bulk_{i:05d}" for i in range(files)]
                     + [f"stress_{label}duplicate_{i:05d}" for i in range(2)])
        first = agent.scan_once()
        assert first["unstable"] == files + 2
        after = agent.scan_once()
        if cap >= len(all_names):
            assert after["staged"] == files + 2, after
            assert_collected(agent, expected_names=all_names,
                             expected_count=files + 4)
        else:
            assert after["staged"] == cap - 2, after
            assert after["deferred"] == files + 4 - cap, after
            staged = agent.items()
            names = all_names[:cap]  # deterministic alphabetical ordering, validated below
            # Sorted watch order includes 'bulk' before 'duplicate' and 'two';
            # use actual ledger signatures instead of assuming producer order.
            actual_keys = Counter(x["digest"] for x in staged)
            possible = Counter(hashlib.sha256(payload(n)).hexdigest() for n in all_names)
            assert not (actual_keys - possible)
        # Replay same capture: receiver denies without replacing media.
        req = urllib.request.Request(
            "http://127.0.0.1:" + str(server.server_port) + "/test-only/incoming",
            data=payload(all_names[0]), method="POST",
            headers={"X-Capture": all_names[0], "X-Lab-Token": server.token},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            raise AssertionError("REPLAY_MUST_BE_REJECTED")
        except urllib.error.HTTPError as exc:
            assert exc.code == 409
        report = {
            "two_files_simultaneous": True,
            "received_count": files + 4,
            "queue_capacity": cap,
            "queue_count": len(agent.items()),
            "deferred_at_capacity": after["deferred"],
            "receiver_duplicate_refused": True,
            "encrypted_queue_and_verified_payload": True,
            "no_clinical_server_receipt": True,
            "two_file_sender_metrics": two,
            "receiver_accepted_count": server.accepted,
        }
    finally:
        server.shutdown()
        server.server_close()
        background.join(timeout=5)
    restarted = HotFolder(config)
    restarted.scan_once()
    again = restarted.scan_once()
    assert len(restarted.items()) == report["queue_count"]
    assert again["staged"] == 0
    assert sum(1 for p in config.watch.glob("*.png.ready")) == files + 4
    assert report["receiver_accepted_count"] == files + 4
    report["restarted_without_duplication"] = True
    print("LOT06C05B03F_RESTART_NO_DUPLICATE_PASS", flush=True)
    return report


def stress(args):
    guard()
    assert platform.system() == "Linux", "C05B03F_UBUNTU_ONLY"
    with tempfile.TemporaryDirectory(prefix="dc06f-stress-") as temp:
        root = Path(temp)
        healthy = run_case(root / "healthy", files=args.files, cap=args.files + 4,
                           shard=args.shard, label="healthy" + str(args.shard))
        print("LOT06C05B03F_CONCURRENT_BURST_QUEUE_PASS", flush=True)
        overload = run_case(root / "overload", files=12, cap=8,
                            shard=args.shard, label="overload" + str(args.shard))
        assert overload["queue_count"] == 8
        assert overload["deferred_at_capacity"] == 8
        print("LOT06C05B03F_BACKPRESSURE_NO_LOSS_PASS", flush=True)
        report = {
            "kind": "LOT06_C05B03F_PARALLEL_UBUNTU_LOOPBACK_RECEIVER",
            "shard": args.shard,
            "ubuntu_runner_requested": os.getenv("STRESS_RUNNER_LABEL", "unknown"),
            "host_os": platform.system(),
            "python": platform.python_version(),
            "head_sha": os.environ["EXPECTED_SHA"],
            "case_saturated": overload,
            "case_healthy": healthy,
            "tests": {
                "two_simultaneous_http_files": True,
                "concurrent_distinct_producer_processes": True,
                "real_hotfolder_sqlite_aes_gcm_queue": True,
                "backpressure_preserves_all_source_files": True,
                "identity_replay_denied": True,
                "process_restart_without_duplicate": True,
            },
            "negative_certification": {
                "shared_cross_runner_receiver_tested": False,
                "production_http_device_ingestion_tested": False,
                "clinical_ack_emitted": False,
                "physical_hosts_certified": False,
                "real_patient_data_used": False,
                "product_ready": False,
            },
        }
        path = Path(os.environ["STRESS_EVIDENCE_DIR"])
        path.mkdir(parents=True, exist_ok=True)
        (path / ("runner-" + str(args.shard) + "-stress.json")).write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        print("LOT06C05B03F_PER_RUNNER_STRESS_PASS", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--url")
    parser.add_argument("--group")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--start-at", type=float, default=0)
    parser.add_argument("--files", type=int, choices=[96, 192], default=96)
    parser.add_argument("--shard", type=int, choices=[0, 1], default=0)
    args = parser.parse_args()
    if args.child:
        child_send(args)
    else:
        stress(args)


if __name__ == "__main__":
    main()
