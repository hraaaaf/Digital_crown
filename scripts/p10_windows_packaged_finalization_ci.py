from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import p10_windows_packaged_lifecycle_ci as lifecycle


RECOVERY_CONTRACT = "windows-interruption-v1"
_ORIGINAL_PREPARE_JOB = lifecycle.prepare_job


def _script_sha(repo_root: Path, name: str) -> str:
    return lifecycle.sha256_file(repo_root / "scripts" / name)


def prepare_job_with_recovery_contract(*, repo_root: Path, **kwargs) -> Path:
    job_path = _ORIGINAL_PREPARE_JOB(**kwargs)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    payload["recovery_contract"] = RECOVERY_CONTRACT
    payload["windows_update_worker_entry.ps1_sha256"] = _script_sha(repo_root, "windows_update_worker_entry.ps1")
    payload["windows_update_worker.ps1_sha256"] = _script_sha(repo_root, "windows_update_worker.ps1")
    payload["windows_update_worker_core.ps1_sha256"] = _script_sha(repo_root, "windows_update_worker_core.ps1")
    payload["windows_update_recovery.ps1_sha256"] = _script_sha(repo_root, "windows_update_recovery.ps1")
    job_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return job_path


def invoke_entry_worker(repo_root: Path, job_path: Path, env: dict[str, str], case_root: Path) -> tuple[int, dict[str, Any]]:
    system_root = Path(env.get("SystemRoot", r"C:\Windows"))
    native_ps = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    entry = repo_root / "scripts" / "windows_update_worker_entry.ps1"
    if not native_ps.is_file() or not entry.is_file():
        raise lifecycle.LifecycleError("WINDOWS_ENTRY_WORKER_MISSING")
    parent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], env=env)
    worker = subprocess.Popen([
        str(native_ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(entry),
        "-JobPath", str(job_path), "-ParentPid", str(parent.pid),
    ], cwd=str(repo_root), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    try:
        time.sleep(1.0)
        parent.terminate()
        try: parent.wait(timeout=10)
        except subprocess.TimeoutExpired:
            parent.kill(); parent.wait(timeout=10)
        stdout, stderr = worker.communicate(timeout=420)
    except Exception:
        lifecycle.stop_process_tree(worker.pid); worker.wait(timeout=20); raise
    finally:
        if parent.poll() is None:
            parent.kill(); parent.wait(timeout=10)
    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / "worker-stdout.log").write_text(stdout or "", encoding="utf-8", errors="replace")
    (case_root / "worker-stderr.log").write_text(stderr or "", encoding="utf-8", errors="replace")
    return worker.returncode, json.loads(job_path.read_text(encoding="utf-8"))


def positive_case(repo_root: Path, baseline: Path, target: Path, root: Path) -> dict[str, Any]:
    install_dir = root / "program"
    data_dir = root / "cabinet"
    env = lifecycle.make_case_env(data_dir, lifecycle.BASE_PORT)
    runtime: subprocess.Popen[bytes] | None = None
    worker_runtime_pid: int | None = None
    try:
        lifecycle.install_inno(baseline, install_dir, root / "baseline-install.log", env)
        executable = install_dir / "DigitalCrown.exe"
        lifecycle.run_self_test(executable, lifecycle.BASE_VERSION, env, root / "baseline-self-test.json")
        runtime = lifecycle.start_runtime(executable, env)
        lifecycle.wait_health(lifecycle.BASE_PORT, process=runtime, timeout=120)
        lifecycle.stop_process_tree(runtime.pid); runtime.wait(timeout=30); runtime = None
        rescue, rescue_sha = lifecycle.create_real_rescue(repo_root, data_dir, env)
        job_path = prepare_job_with_recovery_contract(
            repo_root=repo_root, data_dir=data_dir, target_installer=target, rescue=rescue,
            rescue_sha=rescue_sha, install_dir=install_dir, port=lifecycle.BASE_PORT, sequence=1,
        )
        exit_code, job = invoke_entry_worker(repo_root, job_path, env, root)
        if exit_code != 0:
            raise lifecycle.LifecycleError(f"POSITIVE_WORKER_EXIT expected=0 actual={exit_code} job={job}")
        if (
            job.get("status") != "healthy" or job.get("worker_result") != "install_verified"
            or job.get("package_self_test") != "passed" or job.get("runtime_health") != "passed"
            or job.get("rollback") != "not_needed" or job.get("recovery_contract") != RECOVERY_CONTRACT
        ):
            raise lifecycle.LifecycleError(f"POSITIVE_JOB_TRUTH_FAILED {job}")
        worker_runtime_pid = int(job.get("runtime_pid") or 0)
        lifecycle.wait_health(lifecycle.BASE_PORT, timeout=30)
        lifecycle.run_self_test(executable, lifecycle.TARGET_VERSION, env, root / "target-self-test.json")
        trust_path = data_dir / "updates" / "trusted_state.json"
        if not trust_path.is_file(): raise lifecycle.LifecycleError("POSITIVE_TRUST_STATE_MISSING")
        trust = json.loads(trust_path.read_text(encoding="utf-8"))
        if trust.get("installed_version") != lifecycle.TARGET_VERSION or int(trust.get("installed_sequence") or 0) != 1:
            raise lifecycle.LifecycleError(f"POSITIVE_TRUST_STATE_INVALID {trust}")
        finalize_report_path = job_path.parent / "update-finalize-report.json"
        if not finalize_report_path.is_file(): raise lifecycle.LifecycleError("POSITIVE_FINALIZE_REPORT_MISSING")
        finalize_report = json.loads(finalize_report_path.read_text(encoding="utf-8"))
        if finalize_report.get("status") != "success" or finalize_report.get("version") != lifecycle.TARGET_VERSION or int(finalize_report.get("sequence") or 0) != 1:
            raise lifecycle.LifecycleError(f"POSITIVE_FINALIZE_REPORT_INVALID {finalize_report}")
        return {
            "status": "success", "worker_exit": exit_code, "job_status": job["status"],
            "worker_result": job["worker_result"], "package_version": lifecycle.TARGET_VERSION,
            "runtime_health": job["runtime_health"], "rollback": job["rollback"],
            "rescue_sha256": rescue_sha, "installed_version": trust["installed_version"],
            "installed_sequence": trust["installed_sequence"], "finalization": "passed", "entry_lock": "exercised",
        }
    finally:
        if runtime is not None: lifecycle.stop_process_tree(runtime.pid)
        if worker_runtime_pid: lifecycle.stop_process_tree(worker_runtime_pid)
        try: lifecycle.uninstall_inno(install_dir, root / "positive-uninstall.log", env)
        except Exception as exc: print(f"::warning::positive cleanup uninstall failed: {exc}")


def _interrupt_at_applying(repo_root: Path, job_path: Path, env: dict[str, str], root: Path) -> dict[str, Any]:
    system_root = Path(env.get("SystemRoot", r"C:\Windows"))
    native_ps = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    entry = repo_root / "scripts" / "windows_update_worker_entry.ps1"
    parent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], env=env)
    worker = subprocess.Popen([
        str(native_ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(entry),
        "-JobPath", str(job_path), "-ParentPid", str(parent.pid),
    ], cwd=str(repo_root), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(0.8); parent.terminate()
        try: parent.wait(timeout=10)
        except subprocess.TimeoutExpired:
            parent.kill(); parent.wait(timeout=10)
        deadline = time.monotonic() + 90
        observed = None
        while time.monotonic() < deadline:
            if worker.poll() is not None: break
            try:
                payload = json.loads(job_path.read_text(encoding="utf-8")); observed = str(payload.get("status") or "")
            except (OSError, ValueError): observed = None
            if observed == "applying":
                lifecycle.stop_process_tree(worker.pid); worker.wait(timeout=30)
                return {"interrupted_state": observed, "worker_pid": worker.pid}
            time.sleep(0.05)
        raise lifecycle.LifecycleError(f"INTERRUPTION_WINDOW_MISSED state={observed} worker_rc={worker.poll()}")
    finally:
        if parent.poll() is None: parent.kill(); parent.wait(timeout=10)
        if worker.poll() is None: lifecycle.stop_process_tree(worker.pid); worker.wait(timeout=30)


def _invoke_recovery(repo_root: Path, job_path: Path, env: dict[str, str], root: Path) -> tuple[int, dict[str, Any]]:
    system_root = Path(env.get("SystemRoot", r"C:\Windows"))
    native_ps = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    recovery = repo_root / "scripts" / "windows_update_recovery.ps1"
    parent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], env=env)
    proc = subprocess.Popen([
        str(native_ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(recovery),
        "-JobPath", str(job_path), "-ParentPid", str(parent.pid),
    ], cwd=str(repo_root), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    try:
        time.sleep(0.8); parent.terminate()
        try: parent.wait(timeout=10)
        except subprocess.TimeoutExpired:
            parent.kill(); parent.wait(timeout=10)
        stdout, stderr = proc.communicate(timeout=360)
    finally:
        if parent.poll() is None: parent.kill(); parent.wait(timeout=10)
        if proc.poll() is None: lifecycle.stop_process_tree(proc.pid); proc.wait(timeout=20)
    root.mkdir(parents=True, exist_ok=True)
    (root / "recovery-stdout.log").write_text(stdout or "", encoding="utf-8", errors="replace")
    (root / "recovery-stderr.log").write_text(stderr or "", encoding="utf-8", errors="replace")
    return proc.returncode, json.loads(job_path.read_text(encoding="utf-8"))


def interruption_case(repo_root: Path, baseline: Path, target: Path, root: Path) -> dict[str, Any]:
    port = lifecycle.BASE_PORT + 2
    install_dir = root / "program"
    data_dir = root / "cabinet"
    env = lifecycle.make_case_env(data_dir, port)
    recovery_runtime_pid: int | None = None
    try:
        lifecycle.install_inno(baseline, install_dir, root / "baseline-install.log", env)
        executable = install_dir / "DigitalCrown.exe"
        lifecycle.run_self_test(executable, lifecycle.BASE_VERSION, env, root / "baseline-self-test.json")
        runtime = lifecycle.start_runtime(executable, env)
        lifecycle.wait_health(port, process=runtime, timeout=120)
        lifecycle.stop_process_tree(runtime.pid); runtime.wait(timeout=30)
        rescue, rescue_sha = lifecycle.create_real_rescue(repo_root, data_dir, env)
        job_path = prepare_job_with_recovery_contract(
            repo_root=repo_root, data_dir=data_dir, target_installer=target, rescue=rescue,
            rescue_sha=rescue_sha, install_dir=install_dir, port=port, sequence=3,
        )
        interruption = _interrupt_at_applying(repo_root, job_path, env, root)
        if not (job_path.parent / "rescue" / "program-manifest.json").is_file():
            raise lifecycle.LifecycleError("INTERRUPTION_PROGRAM_RESCUE_MISSING")
        if not (job_path.parent / "rescue" / "uninstall.reg").is_file():
            raise lifecycle.LifecycleError("INTERRUPTION_REGISTRY_RESCUE_MISSING")
        recovery_exit, recovered = _invoke_recovery(repo_root, job_path, env, root)
        if recovery_exit != 2:
            raise lifecycle.LifecycleError(f"INTERRUPTION_RECOVERY_EXIT expected=2 actual={recovery_exit} job={recovered}")
        if recovered.get("status") != "rolled_back" or recovered.get("rollback") != "passed" or recovered.get("database_rollback") != "not_needed":
            raise lifecycle.LifecycleError(f"INTERRUPTION_RECOVERY_TRUTH_FAILED {recovered}")
        recovery_runtime_pid = int(recovered.get("runtime_pid") or 0)
        lifecycle.wait_health(port, timeout=45)
        lifecycle.run_self_test(executable, lifecycle.BASE_VERSION, env, root / "recovered-self-test.json")
        return {
            "status": "success", "interrupted_state": interruption["interrupted_state"],
            "recovery_exit": recovery_exit, "job_status": recovered["status"],
            "package_version": lifecycle.BASE_VERSION, "rollback": recovered["rollback"],
            "database_rollback": recovered["database_rollback"], "reinstall_attempted": False,
        }
    finally:
        if recovery_runtime_pid: lifecycle.stop_process_tree(recovery_runtime_pid)
        try: lifecycle.uninstall_inno(install_dir, root / "interruption-uninstall.log", env)
        except Exception as exc: print(f"::warning::interruption cleanup uninstall failed: {exc}")


def target_application_start_failure_case(repo_root: Path, baseline: Path, target: Path, root: Path) -> dict[str, Any]:
    port = lifecycle.BASE_PORT + 3
    install_dir = root / "program"
    data_dir = root / "cabinet"
    env = lifecycle.make_case_env(data_dir, port)
    runtime: subprocess.Popen[bytes] | None = None
    rollback_runtime_pid: int | None = None
    blocker: subprocess.Popen[str] | None = None
    lease_seconds = 5

    def stop_blocker() -> None:
        nonlocal blocker
        if blocker is None or blocker.poll() is not None:
            return
        blocker.terminate()
        try:
            blocker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            blocker.kill()
            blocker.wait(timeout=5)

    try:
        lifecycle.install_inno(baseline, install_dir, root / "baseline-install.log", env)
        executable = install_dir / "DigitalCrown.exe"
        lifecycle.run_self_test(executable, lifecycle.BASE_VERSION, env, root / "baseline-self-test.json")
        runtime = lifecycle.start_runtime(executable, env)
        lifecycle.wait_health(port, process=runtime, timeout=120)
        lifecycle.stop_process_tree(runtime.pid); runtime.wait(timeout=30); runtime = None

        rescue, rescue_sha = lifecycle.create_real_rescue(repo_root, data_dir, env)
        job_path = prepare_job_with_recovery_contract(
            repo_root=repo_root, data_dir=data_dir, target_installer=target, rescue=rescue,
            rescue_sha=rescue_sha, install_dir=install_dir, port=port, sequence=4,
        )
        job_payload = json.loads(job_path.read_text(encoding="utf-8"))
        job_payload["health_timeout_seconds"] = 3
        job_path.write_text(json.dumps(job_payload, indent=2, sort_keys=True), encoding="utf-8")

        blocker_code = (
            "import socket,time\n"
            "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)\n"
            f"s.bind(('127.0.0.1',{port}))\n"
            "s.listen(1)\n"
            "print('READY', flush=True)\n"
            f"time.sleep({lease_seconds})\n"
        )
        blocker = subprocess.Popen(
            [sys.executable, "-c", blocker_code],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
        )
        if blocker.stdout is None:
            raise lifecycle.LifecycleError("TARGET_START_BLOCKER_STDOUT_MISSING")
        ready = blocker.stdout.readline().strip()
        if ready != "READY":
            stderr = blocker.stderr.read() if blocker.stderr is not None else ""
            raise lifecycle.LifecycleError(
                f"TARGET_START_BLOCKER_NOT_READY rc={blocker.poll()} stderr={stderr.strip()}"
            )

        exit_code, job = invoke_entry_worker(repo_root, job_path, env, root)
        try:
            blocker.wait(timeout=10)
        except subprocess.TimeoutExpired:
            raise lifecycle.LifecycleError("TARGET_START_BLOCKER_LEASE_DID_NOT_EXPIRE")
        if exit_code != 2:
            raise lifecycle.LifecycleError(f"TARGET_START_WORKER_EXIT expected=2 actual={exit_code} job={job}")
        if (
            job.get("status") != "rolled_back"
            or job.get("worker_result") != "rolled_back"
            or job.get("package_self_test") != "passed"
            or job.get("runtime_health") != "failed"
            or job.get("rollback") != "passed"
            or job.get("database_rollback") != "not_needed"
            or job.get("failure_reason") != "UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED"
        ):
            raise lifecycle.LifecycleError(f"TARGET_START_ROLLBACK_TRUTH_FAILED {job}")

        rollback_runtime_pid = int(job.get("runtime_pid") or 0)
        lifecycle.wait_health(port, timeout=45)
        lifecycle.run_self_test(executable, lifecycle.BASE_VERSION, env, root / "rollback-self-test.json")
        return {
            "status": "success",
            "fault": "time_bounded_loopback_port_lease_blocks_target_runtime_bind",
            "fault_injector": "isolated_subprocess",
            "fault_lease_seconds": lease_seconds,
            "failure_reason": job["failure_reason"],
            "worker_exit": exit_code,
            "job_status": job["status"],
            "package_version": lifecycle.BASE_VERSION,
            "rollback": job["rollback"],
            "database_rollback": job["database_rollback"],
            "target_package_self_test": "passed_before_runtime_start_failure",
            "target_package_self_test_job": job["package_self_test"],
            "target_runtime_health": job["runtime_health"],
            "rollback_runtime_health": "passed",
            "blocker_release": "independent_lease_expired_before_rollback_runtime_health",
            "rescue_sha256": rescue_sha,
        }
    finally:
        stop_blocker()
        if runtime is not None:
            lifecycle.stop_process_tree(runtime.pid)
        if rollback_runtime_pid:
            lifecycle.stop_process_tree(rollback_runtime_pid)
        try: lifecycle.uninstall_inno(install_dir, root / "target-start-uninstall.log", env)
        except Exception as exc: print(f"::warning::target-start cleanup uninstall failed: {exc}")


def main() -> int:
    def patched_prepare_job(**kwargs):
        return prepare_job_with_recovery_contract(repo_root=Path(__file__).resolve().parents[1], **kwargs)
    lifecycle.prepare_job = patched_prepare_job
    lifecycle.invoke_worker = invoke_entry_worker
    lifecycle.positive_case = positive_case
    rc = lifecycle.main()
    if rc != 0: return rc
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    args, _ = parser.parse_known_args()
    proof = json.loads(args.report.read_text(encoding="utf-8"))
    proof["interruption_recovery"] = interruption_case(
        args.repo_root.resolve(), args.baseline.resolve(), args.target.resolve(), args.work_root.resolve() / "interruption"
    )
    proof["target_application_start_failure"] = target_application_start_failure_case(
        args.repo_root.resolve(), args.baseline.resolve(), args.target.resolve(), args.work_root.resolve() / "target-start"
    )
    proof["production_wiring_claim"] = "WINDOWS_ENTRY_AND_RECOVERY_ASSERTED"
    args.report.write_text(json.dumps(proof, indent=2, sort_keys=True), encoding="utf-8")
    print("P10_WINDOWS_INTERRUPTION_RECOVERY=SUCCESS state=applying rollback=PASSED reinstall=NOT_ATTEMPTED")
    print("P10_WINDOWS_TARGET_START_FAILURE=SUCCESS fault=TIME_BOUNDED_LOOPBACK_PORT_LEASE rollback=PASSED db_rollback=NOT_NEEDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
