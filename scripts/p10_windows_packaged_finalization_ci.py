from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from scripts import p10_windows_packaged_lifecycle_ci as lifecycle


def positive_case(
    repo_root: Path,
    baseline: Path,
    target: Path,
    root: Path,
) -> dict[str, Any]:
    install_dir = root / "program"
    data_dir = root / "cabinet"
    env = lifecycle.make_case_env(data_dir, lifecycle.BASE_PORT)
    runtime: subprocess.Popen[bytes] | None = None
    worker_runtime_pid: int | None = None
    try:
        lifecycle.install_inno(baseline, install_dir, root / "baseline-install.log", env)
        executable = install_dir / "DigitalCrown.exe"
        lifecycle.run_self_test(
            executable,
            lifecycle.BASE_VERSION,
            env,
            root / "baseline-self-test.json",
        )
        runtime = lifecycle.start_runtime(executable, env)
        lifecycle.wait_health(lifecycle.BASE_PORT, process=runtime, timeout=120)
        lifecycle.stop_process_tree(runtime.pid)
        runtime.wait(timeout=30)
        runtime = None

        rescue, rescue_sha = lifecycle.create_real_rescue(repo_root, data_dir, env)
        job_path = lifecycle.prepare_job(
            data_dir=data_dir,
            target_installer=target,
            rescue=rescue,
            rescue_sha=rescue_sha,
            install_dir=install_dir,
            port=lifecycle.BASE_PORT,
            sequence=1,
        )
        exit_code, job = lifecycle.invoke_worker(repo_root, job_path, env, root)
        if exit_code != 0:
            raise lifecycle.LifecycleError(
                f"POSITIVE_WORKER_EXIT expected=0 actual={exit_code} job={job}"
            )
        if (
            job.get("status") != "healthy"
            or job.get("worker_result") != "install_verified"
            or job.get("package_self_test") != "passed"
            or job.get("runtime_health") != "passed"
            or job.get("rollback") != "not_needed"
        ):
            raise lifecycle.LifecycleError(f"POSITIVE_JOB_TRUTH_FAILED {job}")

        worker_runtime_pid = int(job.get("runtime_pid") or 0)
        lifecycle.wait_health(lifecycle.BASE_PORT, timeout=30)
        lifecycle.run_self_test(
            executable,
            lifecycle.TARGET_VERSION,
            env,
            root / "target-self-test.json",
        )

        trust_path = data_dir / "updates" / "trusted_state.json"
        if not trust_path.is_file():
            raise lifecycle.LifecycleError("POSITIVE_TRUST_STATE_MISSING")
        trust = json.loads(trust_path.read_text(encoding="utf-8"))
        if (
            trust.get("installed_version") != lifecycle.TARGET_VERSION
            or int(trust.get("installed_sequence") or 0) != 1
        ):
            raise lifecycle.LifecycleError(f"POSITIVE_TRUST_STATE_INVALID {trust}")

        finalize_report_path = job_path.parent / "update-finalize-report.json"
        if not finalize_report_path.is_file():
            raise lifecycle.LifecycleError("POSITIVE_FINALIZE_REPORT_MISSING")
        finalize_report = json.loads(finalize_report_path.read_text(encoding="utf-8"))
        if (
            finalize_report.get("status") != "success"
            or finalize_report.get("version") != lifecycle.TARGET_VERSION
            or int(finalize_report.get("sequence") or 0) != 1
        ):
            raise lifecycle.LifecycleError(
                f"POSITIVE_FINALIZE_REPORT_INVALID {finalize_report}"
            )

        return {
            "status": "success",
            "worker_exit": exit_code,
            "job_status": job["status"],
            "worker_result": job["worker_result"],
            "package_version": lifecycle.TARGET_VERSION,
            "runtime_health": job["runtime_health"],
            "rollback": job["rollback"],
            "rescue_sha256": rescue_sha,
            "installed_version": trust["installed_version"],
            "installed_sequence": trust["installed_sequence"],
            "finalization": "passed",
        }
    finally:
        if runtime is not None:
            lifecycle.stop_process_tree(runtime.pid)
        if worker_runtime_pid:
            lifecycle.stop_process_tree(worker_runtime_pid)
        try:
            lifecycle.uninstall_inno(
                install_dir,
                root / "positive-uninstall.log",
                env,
            )
        except Exception as exc:
            print(f"::warning::positive cleanup uninstall failed: {exc}")


def main() -> int:
    lifecycle.positive_case = positive_case
    return lifecycle.main()


if __name__ == "__main__":
    raise SystemExit(main())
