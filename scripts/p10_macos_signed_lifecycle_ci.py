from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

BASE_VERSION = "1.0.0"
TARGET_VERSION = "1.0.1"
WORKER_CONTRACT = "macos-dmg-v1"
RECOVERY_CONTRACT = "macos-interruption-v1"
APP_NAME = "DigitalCrown.app"
EXECUTABLE_REL = Path("Contents") / "MacOS" / "DigitalCrown"
BASE_PORT = 18820


class LifecycleError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_checked(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise LifecycleError(
            "COMMAND_FAILED rc={} cmd={} stdout={} stderr={}".format(
                proc.returncode,
                args,
                proc.stdout[-4000:],
                proc.stderr[-4000:],
            )
        )
    return proc


def make_case_env(data_dir: Path, port: int) -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "DATABASE_URL",
        "ENVIRONMENT",
        "SECRET_KEY",
        "CABINET_MASTER_KEY_HEX",
        "ALLOWED_ORIGINS",
    ):
        env.pop(key, None)
    env.update(
        {
            "DIGITALCROWN_USER_DATA_DIR": str(data_dir),
            "DIGITALCROWN_CONFIG_DIR": str(data_dir),
            "DIGITALCROWN_LOG_DIR": str(data_dir / "logs"),
            "DIGITALCROWN_RUNTIME_DIR": str(data_dir / "runtime"),
            "DIGITALCROWN_ENV_FILE": str(data_dir / ".env"),
            "DIGITALCROWN_RESTORE_RESTART": "1",
            "CABINET_PORT": str(port),
        }
    )
    return env


@contextmanager
def mounted_dmg(dmg: Path, mount: Path) -> Iterator[Path]:
    mount.mkdir(parents=True, exist_ok=True)
    run_checked(
        [
            "/usr/bin/hdiutil",
            "attach",
            str(dmg),
            "-mountpoint",
            str(mount),
            "-nobrowse",
            "-readonly",
        ],
        timeout=120,
    )
    try:
        yield mount
    finally:
        subprocess.run(
            ["/usr/bin/hdiutil", "detach", str(mount), "-force"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
        shutil.rmtree(mount, ignore_errors=True)


def app_executable(app: Path) -> Path:
    executable = app / EXECUTABLE_REL
    if not executable.is_file():
        raise LifecycleError(f"APP_EXECUTABLE_MISSING {executable}")
    return executable


def verify_app(app: Path, expected_version: str) -> None:
    info_path = app / "Contents" / "Info.plist"
    if not info_path.is_file():
        raise LifecycleError(f"INFO_PLIST_MISSING {info_path}")
    info = plistlib.loads(info_path.read_bytes())
    if info.get("CFBundleIdentifier") != "com.saninova.digitalcrown":
        raise LifecycleError(f"BUNDLE_ID_INVALID {info.get('CFBundleIdentifier')}")
    if str(info.get("CFBundleShortVersionString") or "") != expected_version:
        raise LifecycleError(
            f"BUNDLE_VERSION_INVALID expected={expected_version} actual={info.get('CFBundleShortVersionString')}"
        )
    run_checked(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=4", str(app)],
        timeout=120,
    )
    detail_proc = run_checked(
        ["/usr/bin/codesign", "-d", "--verbose=4", str(app)],
        timeout=120,
    )
    details = (detail_proc.stdout or "") + (detail_proc.stderr or "")
    if "Authority=Developer ID Application" not in details:
        raise LifecycleError("DEVELOPER_ID_REQUIRED")
    if "(runtime)" not in details:
        raise LifecycleError("HARDENED_RUNTIME_REQUIRED")
    if "Timestamp=" not in details:
        raise LifecycleError("SECURE_TIMESTAMP_REQUIRED")
    run_checked(
        ["/usr/sbin/spctl", "--assess", "--type", "execute", "--verbose=4", str(app)],
        timeout=120,
    )


def verify_distribution(dmg: Path, expected_version: str, mount_root: Path) -> None:
    run_checked(["/usr/bin/xcrun", "stapler", "validate", str(dmg)], timeout=120)
    run_checked(
        [
            "/usr/sbin/spctl",
            "--assess",
            "--type",
            "open",
            "--context",
            "context:primary-signature",
            "--verbose=4",
            str(dmg),
        ],
        timeout=120,
    )
    with mounted_dmg(dmg, mount_root) as mount:
        verify_app(mount / APP_NAME, expected_version)


def install_from_dmg(
    dmg: Path,
    install_app: Path,
    expected_version: str,
    mount_root: Path,
) -> None:
    install_app.parent.mkdir(parents=True, exist_ok=True)
    if install_app.exists():
        shutil.rmtree(install_app)
    with mounted_dmg(dmg, mount_root) as mount:
        source = mount / APP_NAME
        verify_app(source, expected_version)
        run_checked(["/usr/bin/ditto", str(source), str(install_app)], timeout=180)
    verify_app(install_app, expected_version)


def run_self_test(
    executable: Path,
    expected_version: str,
    env: dict[str, str],
    report_path: Path,
) -> dict[str, Any]:
    local_env = env.copy()
    local_env["DIGITALCROWN_PACKAGE_SELF_TEST_REPORT"] = str(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.unlink(missing_ok=True)
    proc = run_checked(
        [str(executable), "--package-self-test"],
        cwd=executable.parent,
        env=local_env,
        timeout=180,
    )
    if not report_path.is_file():
        raise LifecycleError(
            f"PACKAGE_SELF_TEST_REPORT_MISSING {report_path} stdout={proc.stdout[-2000:]}"
        )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    required = (
        payload.get("status") == "ok",
        payload.get("frozen") is True,
        payload.get("version") == expected_version,
        not payload.get("missing"),
        not payload.get("forbidden_present"),
        not payload.get("unqualified_scientific_weights_present"),
        payload.get("scientific_manifest_policy_ok") is True,
        payload.get("scientific_capabilities") == "FAIL_CLOSED_NO_WEIGHTS",
    )
    if not all(required):
        raise LifecycleError(
            f"PACKAGE_SELF_TEST_TRUTH_FAILED version={expected_version} payload={payload}"
        )
    return payload


def start_runtime(executable: Path, env: dict[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(executable)],
        cwd=str(executable.parent),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_health(
    port: int,
    *,
    process: subprocess.Popen[bytes] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/health"
    last_error = "not_started"
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise LifecycleError(f"RUNTIME_EXITED_BEFORE_HEALTH rc={process.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("status") == "ok" and payload.get("db") == "ok":
                return payload
            last_error = f"payload={payload}"
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last_error = f"{type(exc).__name__}:{exc}"
        time.sleep(0.5)
    raise LifecycleError(f"RUNTIME_HEALTH_TIMEOUT url={url} last={last_error}")


def stop_process(proc: subprocess.Popen[Any] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def stop_pid(pid: int | None) -> None:
    if not pid or pid <= 0:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def create_real_rescue(
    repo_root: Path,
    data_dir: Path,
    env: dict[str, str],
) -> tuple[Path, str]:
    code = r'''
import json
from backend.env_loader import load_backend_env
load_backend_env(override=True)
from backend.services.backup_service import BackupService
result = BackupService.backup_active_database()
print("P10_BACKUP_JSON=" + json.dumps(result, sort_keys=True, default=str))
'''
    proc = run_checked(
        [sys.executable, "-c", code],
        cwd=repo_root,
        env=env,
        timeout=240,
    )
    marker = next(
        (
            line
            for line in reversed(proc.stdout.splitlines())
            if line.startswith("P10_BACKUP_JSON=")
        ),
        None,
    )
    if marker is None:
        raise LifecycleError(f"BACKUP_RESULT_MISSING stdout={proc.stdout[-3000:]}")
    result = json.loads(marker.split("=", 1)[1])
    if result.get("status") != "SUCCESS" or not result.get("backup_filename"):
        raise LifecycleError(f"BACKUP_FAILED result={result}")
    rescue = data_dir / "backups" / str(result["backup_filename"])
    expected_sha = str(result.get("checksum") or "").lower()
    if not rescue.is_file() or sha256_file(rescue) != expected_sha:
        raise LifecycleError("BACKUP_PROOF_INVALID")
    if rescue.suffix != ".enc" or not rescue.name.endswith(".db.enc"):
        raise LifecycleError(f"BACKUP_FORMAT_UNEXPECTED {rescue.name}")
    return rescue, expected_sha


def tree_manifest(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append({"path": rel, "type": "symlink", "target": os.readlink(path)})
        elif path.is_file():
            rows.append(
                {
                    "path": rel,
                    "type": "file",
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        elif path.is_dir():
            rows.append({"path": rel, "type": "dir"})
    return rows


def copy_app_verified(source: Path, destination: Path) -> list[dict[str, Any]]:
    expected = tree_manifest(source)
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_checked(["/usr/bin/ditto", str(source), str(destination)], timeout=240)
    actual = tree_manifest(destination)
    if actual != expected:
        shutil.rmtree(destination, ignore_errors=True)
        raise LifecycleError("APP_COPY_VERIFY_FAILED")
    return actual


def prepare_job(
    *,
    data_dir: Path,
    install_app: Path,
    target_dmg: Path,
    rescue_db: Path,
    rescue_sha: str,
    port: int,
    sequence: int,
    health_timeout: int,
) -> Path:
    job_id = uuid.uuid4().hex
    job_dir = data_dir / "updates" / "jobs" / job_id
    rescue_dir = job_dir / "rescue"
    rescue_dir.mkdir(parents=True, exist_ok=False)

    staged_dmg = job_dir / target_dmg.name
    staged_db = rescue_dir / rescue_db.name
    shutil.copy2(target_dmg, staged_dmg)
    shutil.copy2(rescue_db, staged_db)
    if sha256_file(staged_db) != rescue_sha:
        raise LifecycleError("STAGED_RESCUE_SHA256_MISMATCH")

    rescue_app = rescue_dir / "program" / APP_NAME
    manifest = copy_app_verified(install_app, rescue_app)
    verify_app(rescue_app, BASE_VERSION)
    manifest_path = rescue_dir / "program-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    job = {
        "schema": 1,
        "job_id": job_id,
        "status": "scheduled",
        "created_at": now,
        "updated_at": now,
        "scheduled_at": now,
        "sequence": sequence,
        "platform": "macos",
        "architecture": "arm64",
        "worker_contract": WORKER_CONTRACT,
        "recovery_contract": RECOVERY_CONTRACT,
        "apply_certified": True,
        "apply_blocker": None,
        "current_version": BASE_VERSION,
        "version": TARGET_VERSION,
        "manifest_sha256": hashlib.sha256(
            f"p10-macos-signed-ci:{sequence}:{TARGET_VERSION}".encode("utf-8")
        ).hexdigest(),
        "artifact_filename": staged_dmg.name,
        "artifact_sha256": sha256_file(staged_dmg),
        "artifact_size_bytes": staged_dmg.stat().st_size,
        "rescue_staged": True,
        "rescue_backup_filename": f"rescue/{staged_db.name}",
        "rescue_backup_sha256": sha256_file(staged_db),
        "rescue_app_filename": rescue_app.relative_to(job_dir).as_posix(),
        "program_manifest_sha256": sha256_file(manifest_path),
        "install_app": str(install_app.resolve()),
        "health_url": f"http://127.0.0.1:{port}/health",
        "health_timeout_seconds": health_timeout,
    }
    job_path = job_dir / "job.json"
    job_path.write_text(json.dumps(job, indent=2, sort_keys=True), encoding="utf-8")
    return job_path


def worker_executable(job_path: Path) -> Path:
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    rel = Path(str(payload["rescue_app_filename"]))
    executable = job_path.parent / rel / EXECUTABLE_REL
    if not executable.is_file():
        raise LifecycleError(f"RESCUE_WORKER_MISSING {executable}")
    return executable


def invoke_worker(
    job_path: Path,
    env: dict[str, str],
    case_root: Path,
    *,
    recovery: bool = False,
    timeout: int = 720,
) -> tuple[int, dict[str, Any]]:
    executable = worker_executable(job_path)
    mode = "--macos-update-recovery" if recovery else "--macos-update-worker"
    parent = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        env=env,
    )
    proc = subprocess.Popen(
        [
            str(executable),
            mode,
            str(job_path),
            "--parent-pid",
            str(parent.pid),
        ],
        cwd=str(executable.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
    )
    try:
        time.sleep(1.0)
        parent.terminate()
        try:
            parent.wait(timeout=10)
        except subprocess.TimeoutExpired:
            parent.kill()
            parent.wait(timeout=10)
        stdout, stderr = proc.communicate(timeout=timeout)
    except Exception:
        stop_process(proc)
        raise
    finally:
        stop_process(parent)
    case_root.mkdir(parents=True, exist_ok=True)
    prefix = "recovery" if recovery else "worker"
    (case_root / f"{prefix}-stdout.log").write_text(
        stdout or "", encoding="utf-8", errors="replace"
    )
    (case_root / f"{prefix}-stderr.log").write_text(
        stderr or "", encoding="utf-8", errors="replace"
    )
    return proc.returncode, json.loads(job_path.read_text(encoding="utf-8"))


def initialize_baseline(
    *,
    baseline_dmg: Path,
    repo_root: Path,
    root: Path,
    port: int,
) -> tuple[Path, Path, dict[str, str], Path, str]:
    data_dir = root / "cabinet"
    install_app = root / "Applications" / APP_NAME
    env = make_case_env(data_dir, port)
    install_from_dmg(
        baseline_dmg,
        install_app,
        BASE_VERSION,
        root / "mount-baseline",
    )
    executable = app_executable(install_app)
    run_self_test(executable, BASE_VERSION, env, root / "baseline-self-test.json")
    runtime = start_runtime(executable, env)
    try:
        wait_health(port, process=runtime, timeout=180)
    finally:
        stop_process(runtime)
    rescue_db, rescue_sha = create_real_rescue(repo_root, data_dir, env)
    return data_dir, install_app, env, rescue_db, rescue_sha


def positive_case(
    repo_root: Path,
    baseline_dmg: Path,
    target_dmg: Path,
    root: Path,
) -> dict[str, Any]:
    port = BASE_PORT
    runtime_pid: int | None = None
    data_dir, install_app, env, rescue_db, rescue_sha = initialize_baseline(
        baseline_dmg=baseline_dmg,
        repo_root=repo_root,
        root=root,
        port=port,
    )
    try:
        job_path = prepare_job(
            data_dir=data_dir,
            install_app=install_app,
            target_dmg=target_dmg,
            rescue_db=rescue_db,
            rescue_sha=rescue_sha,
            port=port,
            sequence=1,
            health_timeout=45,
        )
        exit_code, job = invoke_worker(job_path, env, root)
        if exit_code != 0:
            raise LifecycleError(
                f"POSITIVE_WORKER_EXIT expected=0 actual={exit_code} job={job}"
            )
        if (
            job.get("status") != "healthy"
            or job.get("worker_result") != "install_verified"
            or job.get("package_self_test") != "passed"
            or job.get("runtime_health") != "passed"
            or job.get("rollback") != "not_needed"
            or job.get("database_rollback") != "not_needed"
        ):
            raise LifecycleError(f"POSITIVE_JOB_TRUTH_FAILED {job}")
        runtime_pid = int(job.get("runtime_pid") or 0)
        wait_health(port, timeout=45)
        run_self_test(
            app_executable(install_app),
            TARGET_VERSION,
            env,
            root / "target-self-test.json",
        )
        trust_path = data_dir / "updates" / "trusted_state.json"
        if not trust_path.is_file():
            raise LifecycleError("POSITIVE_TRUST_STATE_MISSING")
        trust = json.loads(trust_path.read_text(encoding="utf-8"))
        if trust.get("installed_version") != TARGET_VERSION or int(
            trust.get("installed_sequence") or 0
        ) != 1:
            raise LifecycleError(f"POSITIVE_TRUST_STATE_INVALID {trust}")
        finalize = job_path.parent / "update-finalize-report.json"
        if not finalize.is_file():
            raise LifecycleError("POSITIVE_FINALIZE_REPORT_MISSING")
        finalize_payload = json.loads(finalize.read_text(encoding="utf-8"))
        if (
            finalize_payload.get("status") != "success"
            or finalize_payload.get("version") != TARGET_VERSION
            or int(finalize_payload.get("sequence") or 0) != 1
        ):
            raise LifecycleError(
                f"POSITIVE_FINALIZE_REPORT_INVALID {finalize_payload}"
            )
        return {
            "status": "success",
            "worker_exit": exit_code,
            "job_status": job["status"],
            "installed_version": trust["installed_version"],
            "installed_sequence": trust["installed_sequence"],
            "runtime_health": job["runtime_health"],
            "rollback": job["rollback"],
            "database_rollback": job["database_rollback"],
            "finalization": "passed",
        }
    finally:
        stop_pid(runtime_pid)


def interrupt_at_applying(
    job_path: Path,
    env: dict[str, str],
    case_root: Path,
) -> dict[str, Any]:
    executable = worker_executable(job_path)
    parent = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        env=env,
    )
    case_root.mkdir(parents=True, exist_ok=True)
    stdout_path = case_root / "interrupted-worker-stdout.log"
    stderr_path = case_root / "interrupted-worker-stderr.log"
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr:
        worker = subprocess.Popen(
            [
                str(executable),
                "--macos-update-worker",
                str(job_path),
                "--parent-pid",
                str(parent.pid),
            ],
            cwd=str(executable.parent),
            env=env,
            stdout=stdout,
            stderr=stderr,
            text=True,
        )
        try:
            time.sleep(1.0)
            parent.terminate()
            try:
                parent.wait(timeout=10)
            except subprocess.TimeoutExpired:
                parent.kill()
                parent.wait(timeout=10)
            deadline = time.monotonic() + 180
            observed = None
            while time.monotonic() < deadline:
                if worker.poll() is not None:
                    break
                try:
                    payload = json.loads(job_path.read_text(encoding="utf-8"))
                    observed = str(payload.get("status") or "")
                except (OSError, ValueError):
                    observed = None
                if observed == "applying":
                    worker.terminate()
                    try:
                        worker.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        worker.kill()
                        worker.wait(timeout=10)
                    return {
                        "interrupted_state": observed,
                        "worker_pid": worker.pid,
                    }
                time.sleep(0.02)
            raise LifecycleError(
                f"INTERRUPTION_WINDOW_MISSED state={observed} worker_rc={worker.poll()}"
            )
        finally:
            stop_process(parent)
            stop_process(worker)


def interruption_case(
    repo_root: Path,
    baseline_dmg: Path,
    target_dmg: Path,
    root: Path,
) -> dict[str, Any]:
    port = BASE_PORT + 1
    recovery_runtime_pid: int | None = None
    data_dir, install_app, env, rescue_db, rescue_sha = initialize_baseline(
        baseline_dmg=baseline_dmg,
        repo_root=repo_root,
        root=root,
        port=port,
    )
    try:
        job_path = prepare_job(
            data_dir=data_dir,
            install_app=install_app,
            target_dmg=target_dmg,
            rescue_db=rescue_db,
            rescue_sha=rescue_sha,
            port=port,
            sequence=2,
            health_timeout=30,
        )
        interrupted = interrupt_at_applying(job_path, env, root)
        recovery_exit, recovered = invoke_worker(
            job_path,
            env,
            root,
            recovery=True,
            timeout=600,
        )
        if recovery_exit != 2:
            raise LifecycleError(
                f"INTERRUPTION_RECOVERY_EXIT expected=2 actual={recovery_exit} job={recovered}"
            )
        if (
            recovered.get("status") != "rolled_back"
            or recovered.get("rollback") != "passed"
            or recovered.get("database_rollback") != "not_needed"
        ):
            raise LifecycleError(f"INTERRUPTION_RECOVERY_TRUTH_FAILED {recovered}")
        recovery_runtime_pid = int(recovered.get("runtime_pid") or 0)
        wait_health(port, timeout=45)
        run_self_test(
            app_executable(install_app),
            BASE_VERSION,
            env,
            root / "recovered-self-test.json",
        )
        return {
            "status": "success",
            "interrupted_state": interrupted["interrupted_state"],
            "recovery_exit": recovery_exit,
            "job_status": recovered["status"],
            "rollback": recovered["rollback"],
            "database_rollback": recovered["database_rollback"],
        }
    finally:
        stop_pid(recovery_runtime_pid)


def corrupt_database(data_dir: Path) -> tuple[str, str]:
    database = data_dir / "clinical_vault.db"
    if not database.is_file() or database.stat().st_size <= 0:
        raise LifecycleError("DATABASE_MISSING_BEFORE_FAULT")
    before = sha256_file(database)
    database.write_bytes(
        b"P10-MACOS-DETERMINISTIC-CORRUPTION-AFTER-VERIFIED-RESCUE\x00" * 128
    )
    Path(str(database) + "-wal").unlink(missing_ok=True)
    Path(str(database) + "-shm").unlink(missing_ok=True)
    after = sha256_file(database)
    if after == before:
        raise LifecycleError("DATABASE_FAULT_NOT_APPLIED")
    return before, after


def db_rollback_case(
    repo_root: Path,
    baseline_dmg: Path,
    target_dmg: Path,
    root: Path,
) -> dict[str, Any]:
    port = BASE_PORT + 2
    rollback_runtime_pid: int | None = None
    data_dir, install_app, env, rescue_db, rescue_sha = initialize_baseline(
        baseline_dmg=baseline_dmg,
        repo_root=repo_root,
        root=root,
        port=port,
    )
    try:
        job_path = prepare_job(
            data_dir=data_dir,
            install_app=install_app,
            target_dmg=target_dmg,
            rescue_db=rescue_db,
            rescue_sha=rescue_sha,
            port=port,
            sequence=3,
            health_timeout=8,
        )
        before, corrupted = corrupt_database(data_dir)
        exit_code, job = invoke_worker(job_path, env, root, timeout=720)
        if exit_code != 2:
            raise LifecycleError(
                f"DB_ROLLBACK_WORKER_EXIT expected=2 actual={exit_code} job={job}"
            )
        if (
            job.get("status") != "rolled_back"
            or job.get("rollback") != "passed"
            or job.get("database_rollback") != "passed"
        ):
            raise LifecycleError(f"DB_ROLLBACK_JOB_TRUTH_FAILED {job}")
        rollback_runtime_pid = int(job.get("runtime_pid") or 0)
        wait_health(port, timeout=45)
        run_self_test(
            app_executable(install_app),
            BASE_VERSION,
            env,
            root / "db-rollback-self-test.json",
        )
        restored_sha = sha256_file(data_dir / "clinical_vault.db")
        if restored_sha == corrupted:
            raise LifecycleError("DB_ROLLBACK_DATABASE_STILL_CORRUPTED")
        report = job_path.parent / "db-rollback-report.json"
        if not report.is_file():
            raise LifecycleError("DB_ROLLBACK_REPORT_MISSING")
        report_payload = json.loads(report.read_text(encoding="utf-8"))
        if report_payload.get("status") != "success":
            raise LifecycleError(f"DB_ROLLBACK_REPORT_INVALID {report_payload}")
        return {
            "status": "success",
            "worker_exit": exit_code,
            "job_status": job["status"],
            "rollback": job["rollback"],
            "database_rollback": job["database_rollback"],
            "database_sha_before_fault": before,
            "database_sha_corrupted": corrupted,
            "database_sha_after_restore": restored_sha,
        }
    finally:
        stop_pid(rollback_runtime_pid)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-dmg", type=Path, required=True)
    parser.add_argument("--target-dmg", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    baseline_dmg = args.baseline_dmg.resolve()
    target_dmg = args.target_dmg.resolve()
    work_root = args.work_root.resolve()
    report = args.report.resolve()
    if not baseline_dmg.is_file() or not target_dmg.is_file():
        raise SystemExit("P10_MACOS_SIGNED_DMG_PAIR_MISSING")

    work_root.mkdir(parents=True, exist_ok=True)
    verify_distribution(
        baseline_dmg,
        BASE_VERSION,
        work_root / "verify-baseline-mount",
    )
    verify_distribution(
        target_dmg,
        TARGET_VERSION,
        work_root / "verify-target-mount",
    )

    proof: dict[str, Any] = {
        "schema": 1,
        "status": "running",
        "source_head": os.environ.get("GITHUB_SHA"),
        "baseline": {
            "version": BASE_VERSION,
            "filename": baseline_dmg.name,
            "sha256": sha256_file(baseline_dmg),
            "distribution": "developer_id_notarized_stapled_gatekeeper_valid",
        },
        "target": {
            "version": TARGET_VERSION,
            "filename": target_dmg.name,
            "sha256": sha256_file(target_dmg),
            "distribution": "developer_id_notarized_stapled_gatekeeper_valid",
        },
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    try:
        proof["positive"] = positive_case(
            repo_root,
            baseline_dmg,
            target_dmg,
            work_root / "positive",
        )
        proof["interruption_recovery"] = interruption_case(
            repo_root,
            baseline_dmg,
            target_dmg,
            work_root / "interruption",
        )
        proof["database_rollback"] = db_rollback_case(
            repo_root,
            baseline_dmg,
            target_dmg,
            work_root / "db-rollback",
        )
        proof["status"] = "success"
    except Exception as exc:
        proof["status"] = "failed"
        proof["error"] = f"{type(exc).__name__}:{exc}"
        report.write_text(
            json.dumps(proof, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        raise

    report.write_text(
        json.dumps(proof, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print("P10_MACOS_SIGNED_LIFECYCLE_PROOF=" + json.dumps(proof, sort_keys=True))


if __name__ == "__main__":
    main()
