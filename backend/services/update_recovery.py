from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from backend.core.platform import get_platform_adapter
from backend.services.update_engine import UpdateEngine, UpdatePreparationError


RECOVERABLE_STATES = {
    "scheduled",
    "applying",
    "rolling_back",
    "health_pending",
    "database_rolling_back",
}
WINDOWS_RECOVERY_FILE = "windows_update_recovery.ps1"
WINDOWS_WORKER_CONTRACT = "windows-inno-v1"
WINDOWS_RECOVERY_CONTRACT = "windows-interruption-v1"
MACOS_WORKER_CONTRACT = "macos-dmg-v1"
MACOS_RECOVERY_CONTRACT = "macos-interruption-v1"
MACOS_EXECUTABLE_REL = Path("Contents") / "MacOS" / "DigitalCrown"
MACOS_DB_RECOVERY_FAILURES = {
    "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED",
    "UPDATE_MACOS_DB_ROLLBACK_FAILED",
    "UPDATE_MACOS_DB_ROLLBACK_RUNTIME_HEALTH_FAILED",
}
_JOB_ID = re.compile(r"^[0-9a-f]{32}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class UpdateRecoveryService:
    """Detect and hand off interrupted packaged update jobs before normal runtime startup."""

    @staticmethod
    def runtime_recovery_supported() -> bool:
        adapter = get_platform_adapter()
        return (
            bool(getattr(sys, "frozen", False))
            and os.environ.get("ENVIRONMENT", "").strip().lower() == "cabinet"
            and (adapter.is_windows or adapter.is_macos)
        )

    @staticmethod
    def _eligible(job: dict[str, Any]) -> bool:
        if int(job.get("schema") or 0) != 1 or job.get("apply_certified") is not True:
            return False
        platform = str(job.get("platform") or "").lower()
        status = str(job.get("status") or "")
        if platform == "windows":
            if str(job.get("worker_contract") or "") != WINDOWS_WORKER_CONTRACT:
                return False
            if str(job.get("recovery_contract") or "") != WINDOWS_RECOVERY_CONTRACT:
                return False
            if status in RECOVERABLE_STATES:
                return True
            return (
                status == "rollback_failed"
                and str(job.get("worker_result") or "") == "rollback_failed"
                and str(job.get("rollback") or "") == "failed"
                and str(job.get("rollback_failure_reason") or "")
                == "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
                and str(job.get("database_rollback") or "")
                in {"required_but_not_wired", "running"}
            )
        if platform == "macos":
            if str(job.get("worker_contract") or "") != MACOS_WORKER_CONTRACT:
                return False
            if str(job.get("recovery_contract") or "") != MACOS_RECOVERY_CONTRACT:
                return False
            if status in {"scheduled", "applying", "rolling_back", "health_pending"}:
                return True
            if status == "database_rolling_back":
                return (
                    str(job.get("worker_result") or "") == "rollback_failed"
                    and str(job.get("rollback") or "") == "failed"
                    and str(job.get("database_rollback") or "") == "running"
                    and str(job.get("rollback_failure_reason") or "")
                    == "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED"
                )
            return (
                status == "rollback_failed"
                and str(job.get("worker_result") or "") == "rollback_failed"
                and str(job.get("rollback") or "") == "failed"
                and str(job.get("database_rollback") or "") in {"running", "failed"}
                and str(job.get("rollback_failure_reason") or "") in MACOS_DB_RECOVERY_FAILURES
            )
        return False

    @classmethod
    def _recoverable_job(cls) -> dict[str, Any] | None:
        jobs_root = UpdateEngine.root() / "jobs"
        if not jobs_root.is_dir():
            return None
        candidates: list[dict[str, Any]] = []
        for job_dir in sorted(jobs_root.iterdir()):
            if not job_dir.is_dir() or not _JOB_ID.fullmatch(job_dir.name):
                continue
            job_path = job_dir / "job.json"
            if not job_path.is_file():
                continue
            try:
                payload = json.loads(job_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(payload, dict) or str(payload.get("job_id") or "") != job_dir.name:
                continue
            if cls._eligible(payload):
                candidates.append(payload)
        if len(candidates) > 1:
            raise UpdatePreparationError("UPDATE_RECOVERY_MULTIPLE_ACTIVE_JOBS")
        return candidates[0] if candidates else None

    @classmethod
    def _windows_recovery_script(cls, job: dict[str, Any]) -> Path:
        job_dir = UpdateEngine._job_dir(str(job.get("job_id") or ""))
        rel = Path(str(job.get("worker_recovery_filename") or ""))
        if rel.is_absolute() or ".." in rel.parts:
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_PATH_INVALID")
        script = (job_dir / rel).resolve()
        try:
            script.relative_to(job_dir.resolve())
        except ValueError as exc:
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_PATH_INVALID") from exc
        expected = str(job.get(f"{WINDOWS_RECOVERY_FILE}_sha256") or "").strip().lower()
        if not script.is_file() or len(expected) != 64 or _sha256(script) != expected:
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_SHA256_MISMATCH")
        return script

    @classmethod
    def _macos_recovery_executable(cls, job: dict[str, Any]) -> Path:
        job_dir = UpdateEngine._job_dir(str(job.get("job_id") or ""))
        rel = Path(str(job.get("rescue_app_filename") or ""))
        if rel.is_absolute() or ".." in rel.parts:
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_PATH_INVALID")
        app = (job_dir / rel).resolve()
        try:
            app.relative_to(job_dir.resolve())
        except ValueError as exc:
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_PATH_INVALID") from exc
        manifest = job_dir / "rescue" / "program-manifest.json"
        expected_manifest = str(job.get("program_manifest_sha256") or "").strip().lower()
        if not manifest.is_file() or len(expected_manifest) != 64 or _sha256(manifest) != expected_manifest:
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_SHA256_MISMATCH")
        executable = app / MACOS_EXECUTABLE_REL
        if not executable.is_file():
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_MISSING")
        return executable

    @staticmethod
    def _powershell51() -> Path:
        path = get_platform_adapter().windows_powershell51_path()
        if path is None:
            raise UpdatePreparationError("UPDATE_WINDOWS_POWERSHELL51_MISSING")
        return path

    @classmethod
    def schedule_startup_recovery(cls, parent_pid: int) -> dict[str, Any] | None:
        if not cls.runtime_recovery_supported():
            return None
        # Runtime instances launched by the update/rollback worker are controlled by that worker.
        if os.environ.get("DIGITALCROWN_RESTORE_RESTART") == "1":
            return None
        job = cls._recoverable_job()
        if job is None:
            return None
        job_path = UpdateEngine._job_dir(str(job["job_id"])) / "job.json"
        platform = str(job.get("platform") or "").lower()
        # Resolve and validate the recovery executable before the launch try/except.
        # Integrity/path failures must keep their precise fail-closed error code.
        if platform == "windows":
            script = cls._windows_recovery_script(job)
            args = [
                str(cls._powershell51()),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-JobPath",
                str(job_path),
                "-ParentPid",
                str(parent_pid),
            ]
            launch_env = None
        elif platform == "macos":
            executable = cls._macos_recovery_executable(job)
            args = [
                str(executable),
                "--macos-update-recovery",
                str(job_path),
                "--parent-pid",
                str(parent_pid),
            ]
            launch_env = {**os.environ, "DIGITALCROWN_RESTORE_RESTART": "1"}
        else:
            raise UpdatePreparationError("UPDATE_PLATFORM_APPLY_NOT_WIRED")

        # Do not touch job.json here. A live apply worker may still own worker.lock;
        # the recovery worker is the only process allowed to mutate recovery state
        # after it acquires that lock.
        launch_kwargs = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            **get_platform_adapter().detached_process_kwargs(),
        }
        if launch_env is not None:
            launch_kwargs["env"] = launch_env
        try:
            subprocess.Popen(args, **launch_kwargs)
        except Exception as exc:
            # Only process-launch failures are normalized here. Validation failures above
            # retain their exact security/error contract.
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_LAUNCH_FAILED") from exc
        result = {
            "job_id": str(job["job_id"]),
            "status": str(job.get("status") or ""),
            "recovery": "scheduled",
        }
        if platform == "macos":
            result["platform"] = "macos"
        return result
