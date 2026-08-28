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
_JOB_ID = re.compile(r"^[0-9a-f]{32}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class UpdateRecoveryService:
    """Detect and hand off interrupted Windows update jobs before normal runtime startup."""

    @staticmethod
    def runtime_recovery_supported() -> bool:
        adapter = get_platform_adapter()
        return (
            bool(getattr(sys, "frozen", False))
            and os.environ.get("ENVIRONMENT", "").strip().lower() == "cabinet"
            and adapter.is_windows
        )

    @staticmethod
    def _eligible(job: dict[str, Any]) -> bool:
        if int(job.get("schema") or 0) != 1:
            return False
        if str(job.get("platform") or "").lower() != "windows":
            return False
        if str(job.get("worker_contract") or "") != WINDOWS_WORKER_CONTRACT:
            return False
        if str(job.get("recovery_contract") or "") != WINDOWS_RECOVERY_CONTRACT:
            return False
        if job.get("apply_certified") is not True:
            return False
        status = str(job.get("status") or "")
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
    def _recovery_script(cls, job: dict[str, Any]) -> Path:
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
        script = cls._recovery_script(job)
        job_path = UpdateEngine._job_dir(str(job["job_id"])) / "job.json"
        # Do not touch job.json here. A live apply worker may still own worker.lock;
        # the recovery PowerShell worker is the only process allowed to mutate
        # recovery state after it acquires that lock.
        try:
            subprocess.Popen(
                [
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
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **get_platform_adapter().detached_process_kwargs(),
            )
        except Exception as exc:
            # Fail closed without writing job state outside worker.lock. The launcher
            # opens its existing non-destructive recovery surface for the operator.
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_LAUNCH_FAILED") from exc
        return {
            "job_id": str(job["job_id"]),
            "status": str(job.get("status") or ""),
            "recovery": "scheduled",
        }
