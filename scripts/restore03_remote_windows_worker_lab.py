#!/usr/bin/env python3
"""RESTORE-03: actual DB/media GuidedRestore worker on a separate CI Windows host.

LAB ONLY. A generated .dcbundle crosses from source A. Target B converts the
bundle with its own generated keys, preflights and prepares an independent
synthetic cabinet, then exercises the production worker with real filesystem
DB/media changes and real HTTP /health probes. The *stand-in health service*
is NOT the Digital Crown packaged executable. Portable license rebind, frozen
runtime, UI and clinical endpoints are NOT tested.

For the positive worker test we deliberately remove the portable metadata
from a test-only converted archive so the real worker can be tested without
faking P4 license rebind. Never present this as portable clinical recovery.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import types
import zipfile
from pathlib import Path

from restore03_cross_host_lab import (
    BUNDLE_NAME,
    MARKER,
    ROOT,
    SECRET_ENV,
    SOURCE_RECORD,
    create_db,
    load_slice,
    machine_pseudonym,
    new_dir,
    read_db_marker,
    setup_synthetic_environment,
    sha256_file,
    test_secret,
)

EVIDENCE_NAME = "restore03-b-real-worker-synthetic-evidence.json"
TEST_HEALTH_SERVER = r"""
import json
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

port = int(sys.argv[1])
db_path = Path(sys.argv[2])
media_path = Path(sys.argv[3])
expected_value = sys.argv[4]
media_name = sys.argv[5]
expected_media = sys.argv[6].encode("ascii")
force_failure = sys.argv[7] == "fail"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        ok = False
        if self.path == "/health" and not force_failure:
            try:
                with sqlite3.connect(str(db_path)) as conn:
                    marker = conn.execute("SELECT value FROM truth WHERE id=1").fetchone()[0]
                    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                    tables = {x[0] for x in conn.execute("SELECT name FROM sqlite_master")}
                ok = (marker == expected_value and integrity == "ok"
                      and {"users", "patients"}.issubset(tables)
                      and (media_path / media_name).read_bytes() == expected_media)
            except Exception:
                ok = False
        status = 200 if ok else 503
        body = json.dumps({"status": "ok" if ok else "bad", "db": "ok" if ok else "bad"}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *_args):
        pass

ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
"""


def load_restore_classes():
    def load(name: str, relative_path: str):
        spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("BACKEND_RESTORE_CODE_NOT_FOUND")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    service_mod = load("backend.services.guided_restore", "backend/services/guided_restore.py")
    worker_mod = load("backend.services.guided_restore_worker", "backend/services/guided_restore_worker.py")
    return service_mod.GuidedRestoreService, worker_mod.GuidedRestoreWorker


def fresh_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def only_nonportable_fixture(portable_archive: Path, destination: Path) -> None:
    """Produce test-only manifest without portable rebind metadata; leave payload bytes intact."""
    with zipfile.ZipFile(portable_archive, "r") as z, zipfile.ZipFile(destination, "w", zipfile.ZIP_STORED) as out:
        manifest = json.loads(z.read("manifest.json"))
        if not isinstance(manifest.pop("portable", None), dict):
            raise AssertionError("PORTABLE_METADATA_MISSING")
        assert manifest["format"] == "digital-crown-guided-restore"
        out.writestr("manifest.json", json.dumps(manifest, separators=(",", ":")))
        for filename in ("database.db.enc", "media.zip.enc"):
            content = z.read(filename)
            assert hashlib.sha256(content).hexdigest() == manifest[
                "database" if filename.startswith("database") else "media"
            ]["sha256"]
            out.writestr(filename, content)


def assert_state(db: Path, media: Path, value: str, media_name: str, data: bytes) -> None:
    assert read_db_marker(db) == (value, 63)
    assert (media / media_name).read_bytes() == data
    if media_name.startswith("radios/"):
        assert not (media / "before.txt").exists()
    else:
        assert not (media / "radios" / "SYNTHETIC.txt").exists()


def main() -> int:
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("GITHUB_WINDOWS_RUNNER_ONLY")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(os.getenv(name) for name in (
        "DATABASE_URL", "SQLCIPHER_KEY_HEX", "CABINET_MASTER_KEY_HEX",
        "DIGITALCROWN_USER_DATA_DIR", "MEDIA_ROOT",
    )):
        raise RuntimeError("LIVE_CABINET_ENV_NOT_ALLOWED")
    secret = test_secret()
    input_dir = args.input.resolve()
    evidence = json.loads((input_dir / SOURCE_RECORD).read_text(encoding="utf-8"))
    assert evidence.get("marker") == MARKER
    assert evidence.get("source_os") == "Windows"
    assert evidence.get("source_machine_hash") != machine_pseudonym(), "SAME_MACHINE_NOT_ALLOWED"
    source_bundle = input_dir / BUNDLE_NAME
    assert source_bundle.is_file()
    assert evidence["bundle_sha256"] == sha256_file(source_bundle)
    assert set(evidence["media_sha256"]) == {"radios/SYNTHETIC.txt", "documents/SYNTHETIC.txt"}
    new_dir(args.output)
    work = new_dir(args.output / "private-synthetic-lab")
    setup_synthetic_environment(work)
    appdata = Path(os.environ["DIGITALCROWN_USER_DATA_DIR"])
    media = work / "synthetic-media"
    media.mkdir()
    os.environ["MEDIA_ROOT"] = str(media)
    os.environ["ENVIRONMENT"] = "restore03_synthetic_ci"
    port = fresh_port()
    os.environ["CABINET_PORT"] = str(port)

    backups, _, portable = load_slice()
    service, worker = load_restore_classes()
    portable_archive = work / "portable-guided.zip"
    portable.to_local_guided_restore_archive(
        source_bundle, secret, portable_archive, active_engine=("sqlite", "pysqlite")
    )
    assert portable_archive.is_file()
    nonportable = work / "synthetic-test-manifest-only.zip"
    only_nonportable_fixture(portable_archive, nonportable)

    db = appdata / "clinical_vault.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    test_server = work / "synthetic-health-server.py"
    test_server.write_text(TEST_HEALTH_SERVER, encoding="utf-8")
    processes: list[subprocess.Popen] = []
    marker_after = evidence["fixture_token"]
    before_marker = "RESTORE03_B_BEFORE"
    before_media = b"SYNTHETIC_BEFORE_NOT_CLINICAL"

    def reset_to_before():
        if db.exists():
            db.unlink()
        create_db(db, before_marker)
        if media.exists():
            shutil.rmtree(media)
        media.mkdir()
        (media / "before.txt").write_bytes(before_media)

    def make_verified_rescue_backup():
        path = appdata / "backups" / "synthetic-before.db.enc"
        path.parent.mkdir(parents=True, exist_ok=True)
        backups._encrypt_and_save(db, path, backups._get_or_create_key())
        return {
            "status": "SUCCESS",
            "backup_filename": path.name,
            "checksum": sha256_file(path),
            "engine": "sqlite",
            "size_bytes": path.stat().st_size,
        }

    # The production prepare flow calls this hook. Use real SQLite snapshot and
    # encryption for this synthetic active DB; never connect to a live cabinet.
    backups.backup_active_database = staticmethod(make_verified_rescue_backup)

    # Run real GuidedRestoreWorker DB/media mutation and real loopback HTTP
    # health checks, but launch only a synthetic stand-in server.
    worker._wait_parent_exit = classmethod(lambda cls, pid, timeout=20.0: None)
    original_smoke = worker._smoke_check
    worker._smoke_check = staticmethod(lambda timeout=60: original_smoke(timeout=5.0))
    launch_count = 0
    phase = "success"

    def launch_stand_in(_executable):
        nonlocal launch_count
        launch_count += 1
        force_failure = phase == "rollback" and launch_count == 1
        expected = before_marker if (phase == "rollback" and launch_count > 1) else marker_after
        media_name, media_bytes = (
            ("before.txt", before_media)
            if expected == before_marker
            else ("radios/SYNTHETIC.txt", b"SYNTHETIC_RADIO_NOT_CLINICAL")
        )
        proc = subprocess.Popen(
            [sys.executable, "-u", str(test_server), str(port), str(db), str(media),
             expected, media_name, media_bytes.decode("ascii"), "fail" if force_failure else "pass"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        processes.append(proc)
        return proc

    worker._launch_app = staticmethod(launch_stand_in)

    results = {}
    try:
        for scenario in ("success", "rollback"):
            phase = scenario
            launch_count = 0
            reset_to_before()
            assert_state(db, media, before_marker, "before.txt", before_media)
            candidate = service.preflight_file(
                nonportable, original_name="synthetic-DB-media.zip", active_engine=("sqlite", "pysqlite")
            )
            assert candidate["compatible"] is True and candidate["restore_media"] is True
            prepared = service.prepare(candidate["restore_id"])
            assert prepared["status"] == "prepared"
            persisted = service.get_job(candidate["restore_id"])
            assert persisted["prepared_rescue_db_sha256"]
            assert persisted["prepared_media_digest"]["files"] == 1

            # In a production executable, request_apply() detaches and waits for
            # the backend parent to exit. CI calls the real worker directly here.
            persisted["status"] = "scheduled"
            service._write_job(persisted)
            return_code = worker.run(
                candidate["restore_id"], parent_pid=999999,
                executable="SYNTHETIC_NOT_A_REAL_DIGITALCROWN_EXE",
            )
            final = service.get_job(candidate["restore_id"])
            if scenario == "success":
                assert return_code == 0 and final["status"] == "success"
                assert final["smoke_check"] == "passed" and final["rollback"] == "not_needed"
                assert_state(db, media, marker_after, "radios/SYNTHETIC.txt", b"SYNTHETIC_RADIO_NOT_CLINICAL")
                assert (media / "documents" / "SYNTHETIC.txt").read_bytes() == b"SYNTHETIC_DOCUMENT_NOT_CLINICAL"
            else:
                assert return_code == 2 and final["status"] == "rolled_back"
                assert final["smoke_check"] == "failed" and final["rollback"] == "passed"
                assert_state(db, media, before_marker, "before.txt", before_media)
                assert launch_count == 2
            results[scenario] = {
                "status": final["status"],
                "smoke_check": final["smoke_check"],
                "rollback": final["rollback"],
                "database_oracle": "PASS",
                "media_oracle": "PASS",
                "loopback_http_health_checked": True,
                "health_server_is_stand_in": True,
            }
            for proc in processes:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=5)
            processes.clear()
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)

    report = {
        "marker": "RESTORE03_REMOTE_WINDOWS_WORKER_SYNTHETIC_ONLY_NO_CLINICAL_GO",
        "tested_head": os.environ.get("GITHUB_SHA"),
        "source_os": evidence["source_os"],
        "target_os": "Windows",
        "hosts_distinct_by_pseudonym": True,
        "bundle_sha256_equal_to_source": True,
        "fixture_only": True,
        "real_guided_restore_service_preflight_prepare_worker": True,
        "test_only_nonportable_manifest_for_worker": True,
        "portable_bundle_decryption_and_rekey_at_B": True,
        "portable_license_rebind": "NOT_RUN",
        "frozen_cabinet_exe_installed": False,
        "actual_cabinet_backend_health": "NOT_RUN",
        "parent_process_shutdown": "SIMULATED",
        "result": results,
        "nas_smb_real": "NOT_RUN",
        "physical_cabinet_pc": "NOT_RUN",
        "clinical_go": False,
    }
    # Only non-sensitive, no-PHI proof survives; do not upload plaintext DB/media
    # nor the converted or nonportable packages. Source bundle artifact is test-only.
    shutil.rmtree(work)
    if appdata.exists():
        shutil.rmtree(appdata)
    (args.output / EVIDENCE_NAME).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    assert {x.name for x in args.output.iterdir()} == {EVIDENCE_NAME}
    print("RESTORE03_REMOTE_WINDOWS_WORKER_SUCCESS_AND_ROLLBACK_PASS_SYNTHETIC_NO_CLINICAL_GO")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Do not leak the file paths or values of any confidential environment.
        print("RESTORE03_REMOTE_WINDOWS_WORKER_LAB_FAIL:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2) from None
