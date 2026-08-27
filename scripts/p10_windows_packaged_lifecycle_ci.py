from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

BASE_VERSION = "1.0.0"
TARGET_VERSION = "1.0.1"
WORKER_CONTRACT = "windows-inno-v1"
BASE_PORT = 18810
TARGET_HEALTH_TIMEOUT_SECONDS = 45


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
    system_root = Path(env.get("SystemRoot", r"C:\Windows"))
    native_modules = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "Modules"
    module_roots = [str(native_modules)]
    program_files = Path(env.get("ProgramFiles", r"C:\Program Files")) / "WindowsPowerShell" / "Modules"
    if program_files.is_dir():
        module_roots.append(str(program_files))
    existing = env.get("PSModulePath", "").strip()
    if existing:
        module_roots.append(existing)
    env["PSModulePath"] = ";".join(module_roots)
    return env


def install_inno(installer: Path, install_dir: Path, log_path: Path, env: dict[str, str]) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    run_checked(
        [
            str(installer),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/SP-",
            f"/DIR={install_dir}",
            f"/LOG={log_path}",
        ],
        env=env,
        timeout=240,
    )


def uninstall_inno(install_dir: Path, log_path: Path, env: dict[str, str]) -> None:
    uninstaller = install_dir / "unins000.exe"
    if not uninstaller.is_file():
        return
    run_checked(
        [
            str(uninstaller),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            f"/LOG={log_path}",
        ],
        env=env,
        timeout=180,
    )


def run_self_test(executable: Path, expected_version: str, env: dict[str, str], report_path: Path) -> dict[str, Any]:
    local_env = env.copy()
    local_env["DIGITALCROWN_PACKAGE_SELF_TEST_REPORT"] = str(report_path)
    report_path.unlink(missing_ok=True)
    proc = run_checked(
        [str(executable), "--package-self-test"],
        cwd=executable.parent,
        env=local_env,
        timeout=120,
    )
    if not report_path.is_file():
        raise LifecycleError(f"PACKAGE_SELF_TEST_REPORT_MISSING {report_path} stdout={proc.stdout[-2000:]}")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    required_truths = (
        payload.get("status") == "ok",
        payload.get("frozen") is True,
        payload.get("version") == expected_version,
        not payload.get("missing"),
        not payload.get("forbidden_present"),
        not payload.get("unqualified_scientific_weights_present"),
        payload.get("scientific_manifest_policy_ok") is True,
        payload.get("scientific_capabilities") == "FAIL_CLOSED_NO_WEIGHTS",
    )
    if not all(required_truths):
        raise LifecycleError(f"PACKAGE_SELF_TEST_TRUTH_FAILED version={expected_version} payload={payload}")
    return payload


def wait_health(port: int, *, process: subprocess.Popen[bytes] | None = None, timeout: int = 120) -> dict[str, Any]:
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


def stop_process_tree(pid: int | None) -> None:
    if not pid or pid <= 0:
        return
    subprocess.run(
        ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )


def start_runtime(executable: Path, env: dict[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(executable)],
        cwd=str(executable.parent),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def create_real_rescue(repo_root: Path, data_dir: Path, env: dict[str, str]) -> tuple[Path, str]:
    script = r'''
import json
from backend.env_loader import load_backend_env
load_backend_env(override=True)
from backend.services.backup_service import BackupService
result = BackupService.backup_active_database()
print("P10_BACKUP_JSON=" + json.dumps(result, sort_keys=True, default=str))
'''
    proc = run_checked([sys.executable, "-c", script], cwd=repo_root, env=env, timeout=180)
    marker = next((line for line in reversed(proc.stdout.splitlines()) if line.startswith("P10_BACKUP_JSON=")), None)
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


def prepare_job(
    *,
    data_dir: Path,
    target_installer: Path,
    rescue: Path,
    rescue_sha: str,
    install_dir: Path,
    port: int,
    sequence: int,
) -> Path:
    job_id = uuid.uuid4().hex
    job_dir = data_dir / "updates" / "jobs" / job_id
    rescue_dir = job_dir / "rescue"
    rescue_dir.mkdir(parents=True, exist_ok=False)
    staged_installer = job_dir / target_installer.name
    staged_rescue = rescue_dir / rescue.name
    shutil.copy2(target_installer, staged_installer)
    shutil.copy2(rescue, staged_rescue)
    artifact_sha = sha256_file(staged_installer)
    staged_rescue_sha = sha256_file(staged_rescue)
    if staged_rescue_sha != rescue_sha:
        raise LifecycleError("STAGED_RESCUE_SHA256_MISMATCH")
    job = {
        "schema": 1,
        "job_id": job_id,
        "status": "scheduled",
        "sequence": sequence,
        "platform": "windows",
        "architecture": "amd64",
        "worker_contract": WORKER_CONTRACT,
        "apply_certified": True,
        "current_version": BASE_VERSION,
        "version": TARGET_VERSION,
        "artifact_filename": staged_installer.name,
        "artifact_sha256": artifact_sha,
        "artifact_size_bytes": staged_installer.stat().st_size,
        "rescue_staged": True,
        "rescue_backup_filename": f"rescue/{staged_rescue.name}",
        "rescue_backup_sha256": staged_rescue_sha,
        "install_dir": str(install_dir),
        "health_url": f"http://127.0.0.1:{port}/health",
        "health_timeout_seconds": TARGET_HEALTH_TIMEOUT_SECONDS,
    }
    job_path = job_dir / "job.json"
    job_path.write_text(json.dumps(job, indent=2, sort_keys=True), encoding="utf-8")
    return job_path


def invoke_worker(repo_root: Path, job_path: Path, env: dict[str, str], case_root: Path) -> tuple[int, dict[str, Any]]:
    system_root = Path(env.get("SystemRoot", r"C:\Windows"))
    native_ps = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if not native_ps.is_file():
        raise LifecycleError(f"WINDOWS_POWERSHELL_51_MISSING {native_ps}")
    worker_script = repo_root / "scripts" / "windows_update_worker.ps1"
    core_script = repo_root / "scripts" / "windows_update_worker_core.ps1"
    if not worker_script.is_file() or not core_script.is_file():
        raise LifecycleError("WINDOWS_WORKER_SOURCE_MISSING")

    parent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], env=env)
    worker = subprocess.Popen(
        [
            str(native_ps),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(worker_script),
            "-JobPath",
            str(job_path),
            "-ParentPid",
            str(parent.pid),
        ],
        cwd=str(repo_root),
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
        stdout, stderr = worker.communicate(timeout=360)
    except Exception:
        worker.kill()
        worker.wait(timeout=10)
        raise
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait(timeout=10)

    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / "worker-stdout.log").write_text(stdout or "", encoding="utf-8", errors="replace")
    (case_root / "worker-stderr.log").write_text(stderr or "", encoding="utf-8", errors="replace")
    job = json.loads(job_path.read_text(encoding="utf-8"))
    return worker.returncode, job


def corrupt_database_after_rescue(data_dir: Path) -> str:
    database = data_dir / "clinical_vault.db"
    if not database.is_file() or database.stat().st_size == 0:
        raise LifecycleError("DATABASE_MISSING_BEFORE_FAULT")
    before = sha256_file(database)
    database.write_bytes(b"P10-DETERMINISTIC-CORRUPTION-AFTER-VERIFIED-RESCUE\x00" * 128)
    Path(str(database) + "-wal").unlink(missing_ok=True)
    Path(str(database) + "-shm").unlink(missing_ok=True)
    after = sha256_file(database)
    if after == before:
        raise LifecycleError("DATABASE_FAULT_NOT_APPLIED")
    print("P10_FAULT=CORRUPT_DB_AFTER_RESCUE")
    return after


def positive_case(repo_root: Path, baseline: Path, target: Path, root: Path) -> dict[str, Any]:
    install_dir = root / "program"
    data_dir = root / "cabinet"
    env = make_case_env(data_dir, BASE_PORT)
    runtime: subprocess.Popen[bytes] | None = None
    worker_runtime_pid: int | None = None
    try:
        install_inno(baseline, install_dir, root / "baseline-install.log", env)
        executable = install_dir / "DigitalCrown.exe"
        run_self_test(executable, BASE_VERSION, env, root / "baseline-self-test.json")
        runtime = start_runtime(executable, env)
        wait_health(BASE_PORT, process=runtime, timeout=120)
        stop_process_tree(runtime.pid)
        runtime.wait(timeout=30)
        runtime = None

        rescue, rescue_sha = create_real_rescue(repo_root, data_dir, env)
        job_path = prepare_job(
            data_dir=data_dir,
            target_installer=target,
            rescue=rescue,
            rescue_sha=rescue_sha,
            install_dir=install_dir,
            port=BASE_PORT,
            sequence=1,
        )
        exit_code, job = invoke_worker(repo_root, job_path, env, root)
        if exit_code != 0:
            raise LifecycleError(f"POSITIVE_WORKER_EXIT expected=0 actual={exit_code} job={job}")
        if (
            job.get("status") != "health_pending"
            or job.get("worker_result") != "install_verified"
            or job.get("package_self_test") != "passed"
            or job.get("runtime_health") != "passed"
            or job.get("rollback") != "not_needed"
        ):
            raise LifecycleError(f"POSITIVE_JOB_TRUTH_FAILED {job}")
        worker_runtime_pid = int(job.get("runtime_pid") or 0)
        wait_health(BASE_PORT, timeout=30)
        run_self_test(executable, TARGET_VERSION, env, root / "target-self-test.json")
        return {
            "status": "success",
            "worker_exit": exit_code,
            "job_status": job["status"],
            "worker_result": job["worker_result"],
            "package_version": TARGET_VERSION,
            "runtime_health": job["runtime_health"],
            "rollback": job["rollback"],
            "rescue_sha256": rescue_sha,
        }
    finally:
        if runtime is not None:
            stop_process_tree(runtime.pid)
        if worker_runtime_pid:
            stop_process_tree(worker_runtime_pid)
        try:
            uninstall_inno(install_dir, root / "positive-uninstall.log", env)
        except Exception as exc:
            print(f"::warning::positive cleanup uninstall failed: {exc}")


def rollback_case(repo_root: Path, baseline: Path, target: Path, root: Path) -> dict[str, Any]:
    port = BASE_PORT + 1
    install_dir = root / "program"
    data_dir = root / "cabinet"
    env = make_case_env(data_dir, port)
    runtime: subprocess.Popen[bytes] | None = None
    worker_runtime_pid: int | None = None
    try:
        install_inno(baseline, install_dir, root / "baseline-install.log", env)
        executable = install_dir / "DigitalCrown.exe"
        run_self_test(executable, BASE_VERSION, env, root / "baseline-self-test.json")
        runtime = start_runtime(executable, env)
        wait_health(port, process=runtime, timeout=120)
        stop_process_tree(runtime.pid)
        runtime.wait(timeout=30)
        runtime = None

        rescue, rescue_sha = create_real_rescue(repo_root, data_dir, env)
        corrupt_sha = corrupt_database_after_rescue(data_dir)
        job_path = prepare_job(
            data_dir=data_dir,
            target_installer=target,
            rescue=rescue,
            rescue_sha=rescue_sha,
            install_dir=install_dir,
            port=port,
            sequence=2,
        )
        exit_code, job = invoke_worker(repo_root, job_path, env, root)
        if exit_code != 2:
            raise LifecycleError(f"ROLLBACK_WORKER_EXIT expected=2 actual={exit_code} job={job}")
        if (
            job.get("status") != "rolled_back"
            or job.get("worker_result") != "rolled_back"
            or job.get("rollback") != "passed"
            or job.get("database_rollback") != "passed"
            or job.get("rollback_failure_reason") != "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
        ):
            raise LifecycleError(f"ROLLBACK_JOB_TRUTH_FAILED {job}")
        worker_runtime_pid = int(job.get("runtime_pid") or 0)
        wait_health(port, timeout=45)
        run_self_test(executable, BASE_VERSION, env, root / "rollback-self-test.json")
        db_report_path = job_path.parent / "db-rollback-report.json"
        if not db_report_path.is_file():
            raise LifecycleError("DB_ROLLBACK_REPORT_MISSING")
        db_report = json.loads(db_report_path.read_text(encoding="utf-8"))
        if db_report.get("status") != "success" or db_report.get("rescue_sha256") != rescue_sha:
            raise LifecycleError(f"DB_ROLLBACK_REPORT_INVALID {db_report}")
        restored_db = data_dir / "clinical_vault.db"
        restored_sha = sha256_file(restored_db)
        if restored_sha == corrupt_sha or db_report.get("restored_db_sha256") != restored_sha:
            raise LifecycleError("DB_ROLLBACK_RESTORED_HASH_INVALID")
        return {
            "status": "success",
            "worker_exit": exit_code,
            "job_status": job["status"],
            "worker_result": job["worker_result"],
            "package_version": BASE_VERSION,
            "rollback": job["rollback"],
            "database_rollback": job["database_rollback"],
            "rollback_failure_reason": job["rollback_failure_reason"],
            "rescue_sha256": rescue_sha,
            "restored_db_sha256": restored_sha,
            "quarantine_entries": sorted((db_report.get("quarantine_sha256") or {}).keys()),
        }
    finally:
        if runtime is not None:
            stop_process_tree(runtime.pid)
        if worker_runtime_pid:
            stop_process_tree(worker_runtime_pid)
        try:
            uninstall_inno(install_dir, root / "rollback-uninstall.log", env)
        except Exception as exc:
            print(f"::warning::rollback cleanup uninstall failed: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()

    if os.name != "nt":
        raise LifecycleError("WINDOWS_REQUIRED")
    repo_root = args.repo_root.resolve()
    baseline = args.baseline.resolve()
    target = args.target.resolve()
    if not baseline.is_file() or baseline.name != f"DigitalCrownSetup-{BASE_VERSION}.exe":
        raise LifecycleError(f"BASELINE_INSTALLER_INVALID {baseline}")
    if not target.is_file() or target.name != f"DigitalCrownSetup-{TARGET_VERSION}.exe":
        raise LifecycleError(f"TARGET_INSTALLER_INVALID {target}")
    if sha256_file(baseline) == sha256_file(target):
        raise LifecycleError("BASELINE_TARGET_IDENTICAL")

    work_root = args.work_root.resolve()
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    positive = positive_case(repo_root, baseline, target, work_root / "positive")
    rollback = rollback_case(repo_root, baseline, target, work_root / "rollback")
    report = {
        "schema": 1,
        "status": "success",
        "source_head": os.environ.get("GITHUB_SHA"),
        "baseline": {
            "version": BASE_VERSION,
            "filename": baseline.name,
            "sha256": sha256_file(baseline),
            "size_bytes": baseline.stat().st_size,
            "packaging": "real_pyinstaller_inno_rebuild",
            "authenticode_claim": "NOT_ASSERTED",
        },
        "target": {
            "version": TARGET_VERSION,
            "filename": target.name,
            "sha256": sha256_file(target),
            "size_bytes": target.stat().st_size,
            "packaging": "real_pyinstaller_inno_rebuild",
            "authenticode_claim": "NOT_ASSERTED",
        },
        "positive": positive,
        "rollback": rollback,
        "worker_source": "repository_external_windows_powershell_5_1",
        "production_wiring_claim": "NOT_ASSERTED",
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "P10_WINDOWS_PACKAGED_LIFECYCLE=SUCCESS "
        "current=1.0.0 target=1.0.1 positive=PASSED db_rollback=PASSED production_wiring=NOT_ASSERTED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
