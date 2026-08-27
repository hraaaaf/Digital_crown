from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from backend.core.paths import AppPaths
from backend.core.platform import get_platform_adapter
from backend.services.update_engine import (
    SHA256_PATTERN,
    UpdateEngine,
    UpdatePreparationError,
    UpdateSecurityError,
    _sha256_file,
)

WORKER_CONTRACT = "windows-inno-v1"
SIGNED_MANIFEST_NAME = "signed-manifest.json"
WORKER_DIR_NAME = "worker"
WORKER_NAME = "windows_update_worker.ps1"
WORKER_CORE_NAME = "windows_update_worker_core.ps1"
HEALTH_TIMEOUT_SECONDS = 120


def _current_version() -> str:
    version_path = AppPaths.get_base_dir() / "VERSION"
    if not version_path.is_file():
        raise UpdatePreparationError("UPDATE_WINDOWS_CURRENT_VERSION_MISSING")
    value = version_path.read_text(encoding="utf-8").strip()
    if not value:
        raise UpdatePreparationError("UPDATE_WINDOWS_CURRENT_VERSION_MISSING")
    return value


def _canonical_job_dir(job_id: str) -> Path:
    UpdateEngine.get_job(job_id)
    return UpdateEngine.root() / "jobs" / job_id


def _require_windows() -> None:
    if get_platform_adapter().kind != "windows":
        raise UpdatePreparationError("UPDATE_WINDOWS_PLATFORM_REQUIRED")


def _require_frozen() -> None:
    if not bool(getattr(sys, "frozen", False)):
        raise UpdatePreparationError("UPDATE_WINDOWS_PACKAGED_RUNTIME_REQUIRED")


def _atomic_write_manifest(path: Path, raw: bytes) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UpdateSecurityError("UPDATE_MANIFEST_JSON_INVALID") from exc
    get_platform_adapter().atomic_write_text(path, text)


def _copy_verified(source: Path, target: Path) -> str:
    if not source.is_file():
        raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_SOURCE_MISSING")
    expected = _sha256_file(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".partial")
    try:
        partial.write_bytes(source.read_bytes())
        if _sha256_file(partial) != expected:
            raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_COPY_CHECKSUM_INVALID")
        os.replace(partial, target)
    finally:
        partial.unlink(missing_ok=True)
    return expected


def _rescue_path(job_dir: Path, job: dict[str, Any]) -> Path:
    raw = str(job.get("rescue_backup_filename") or "")
    rel = Path(raw)
    if rel.is_absolute() or len(rel.parts) != 2 or rel.parts[0] != "rescue" or rel.name != rel.parts[-1]:
        raise UpdatePreparationError("UPDATE_WINDOWS_RESCUE_PATH_INVALID")
    rescue = (job_dir / rel).resolve()
    if job_dir.resolve() not in rescue.parents:
        raise UpdatePreparationError("UPDATE_WINDOWS_RESCUE_PATH_INVALID")
    return rescue


def _compare_verified_job(job: dict[str, Any], verified: dict[str, Any]) -> None:
    checks = (
        (int(job.get("sequence") or 0), int(verified["sequence"])),
        (str(job.get("version") or ""), str(verified["version"])),
        (str(job.get("manifest_sha256") or ""), str(verified["manifest_sha256"])),
        (str(job.get("platform") or ""), str(verified["target"]["os"])),
        (str(job.get("architecture") or ""), str(verified["target"]["arch"])),
        (str(job.get("artifact_filename") or ""), str(verified["target"]["filename"])),
        (str(job.get("artifact_sha256") or "").lower(), str(verified["target"]["sha256"]).lower()),
        (int(job.get("artifact_size_bytes") or 0), int(verified["target"]["size_bytes"])),
    )
    if any(left != right for left, right in checks):
        raise UpdateSecurityError("UPDATE_WINDOWS_SIGNED_JOB_MISMATCH")


class UpdateWindowsApply:
    @classmethod
    def prepare_signed(
        cls,
        manifest_path: Path,
        artifact_path: Path,
    ) -> dict[str, Any]:
        _require_windows()
        raw = Path(manifest_path).read_bytes()
        current_version = _current_version()
        adapter = get_platform_adapter()
        verified = UpdateEngine.verify_manifest(
            raw,
            platform_kind="windows",
            architecture=adapter.architecture,
            current_version=current_version,
        )
        job = UpdateEngine.prepare_update(verified, artifact_path=Path(artifact_path))
        job_dir = _canonical_job_dir(str(job["job_id"]))
        manifest_target = job_dir / SIGNED_MANIFEST_NAME
        _atomic_write_manifest(manifest_target, raw)
        job["signed_manifest_filename"] = SIGNED_MANIFEST_NAME
        job["signed_manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        UpdateEngine._write_job(job)
        return job

    @classmethod
    def schedule(
        cls,
        job_id: str,
        parent_pid: int,
    ) -> dict[str, Any]:
        _require_windows()
        _require_frozen()
        adapter = get_platform_adapter()
        if parent_pid <= 0 or not adapter.is_process_alive(parent_pid):
            raise UpdatePreparationError("UPDATE_WINDOWS_PARENT_PROCESS_INVALID")

        job = UpdateEngine.get_job(job_id)
        if str(job.get("status") or "") != "prepared":
            raise UpdatePreparationError("UPDATE_WINDOWS_JOB_STATE_INVALID")
        if job.get("apply_certified") is not False:
            raise UpdatePreparationError("UPDATE_WINDOWS_JOB_ALREADY_CERTIFIED")
        if str(job.get("platform") or "") != "windows":
            raise UpdatePreparationError("UPDATE_WINDOWS_PLATFORM_INVALID")
        if not bool(job.get("rescue_staged")):
            raise UpdatePreparationError("UPDATE_WINDOWS_RESCUE_NOT_STAGED")

        current_version = _current_version()
        job_dir = _canonical_job_dir(job_id)
        manifest_path = job_dir / SIGNED_MANIFEST_NAME
        if str(job.get("signed_manifest_filename") or "") != SIGNED_MANIFEST_NAME or not manifest_path.is_file():
            raise UpdateSecurityError("UPDATE_WINDOWS_SIGNED_MANIFEST_MISSING")
        raw_manifest = manifest_path.read_bytes()
        if hashlib.sha256(raw_manifest).hexdigest() != str(job.get("signed_manifest_sha256") or ""):
            raise UpdateSecurityError("UPDATE_WINDOWS_SIGNED_MANIFEST_CHECKSUM_INVALID")

        verified = UpdateEngine.verify_manifest(
            raw_manifest,
            platform_kind="windows",
            architecture=adapter.architecture,
            current_version=current_version,
        )
        _compare_verified_job(job, verified)
        if str(verified["target"]["arch"]) != "amd64":
            raise UpdatePreparationError("UPDATE_WINDOWS_ARCHITECTURE_NOT_CERTIFIED")
        if not str(job.get("artifact_filename") or "").lower().endswith(".exe"):
            raise UpdatePreparationError("UPDATE_WINDOWS_ARTIFACT_FORMAT_UNSUPPORTED")

        state = UpdateEngine._read_trust_state()
        if (
            int(state.get("highest_sequence") or 0) != int(job["sequence"])
            or str(state.get("highest_manifest_sha256") or "") != str(job["manifest_sha256"])
        ):
            raise UpdateSecurityError("UPDATE_WINDOWS_TRUST_STATE_STALE")

        artifact = job_dir / str(job["artifact_filename"])
        UpdateEngine.verify_local_artifact(verified, artifact)

        rescue = _rescue_path(job_dir, job)
        rescue_sha = str(job.get("rescue_backup_sha256") or "").lower()
        if not SHA256_PATTERN.fullmatch(rescue_sha) or not rescue.is_file() or _sha256_file(rescue) != rescue_sha:
            raise UpdateSecurityError("UPDATE_WINDOWS_RESCUE_BACKUP_SHA256_MISMATCH")
        if rescue.suffixes[-2:] != [".db", ".enc"]:
            raise UpdatePreparationError("UPDATE_WINDOWS_DB_ROLLBACK_FORMAT_UNSUPPORTED")

        backup_key = AppPaths.get_user_data_dir() / "backup.key"
        if not backup_key.is_file() or backup_key.stat().st_size <= 0:
            raise UpdatePreparationError("UPDATE_WINDOWS_BACKUP_KEY_MISSING")

        bundle_scripts = AppPaths.get_base_dir() / "scripts"
        worker_dir = adapter.ensure_private_directory(job_dir / WORKER_DIR_NAME)
        worker = worker_dir / WORKER_NAME
        core = worker_dir / WORKER_CORE_NAME
        worker_sha = _copy_verified(bundle_scripts / WORKER_NAME, worker)
        core_sha = _copy_verified(bundle_scripts / WORKER_CORE_NAME, core)

        executable = Path(sys.executable).resolve()
        if not executable.is_file():
            raise UpdatePreparationError("UPDATE_WINDOWS_CURRENT_EXECUTABLE_MISSING")
        install_dir = executable.parent

        try:
            powershell = adapter.windows_powershell_executable()
        except (FileNotFoundError, RuntimeError) as exc:
            raise UpdatePreparationError("UPDATE_WINDOWS_POWERSHELL_51_MISSING") from exc

        port = int(os.environ.get("CABINET_PORT", "8005"))
        if port <= 0 or port > 65535:
            raise UpdatePreparationError("UPDATE_WINDOWS_HEALTH_PORT_INVALID")

        scheduled = dict(job)
        scheduled.update(
            {
                "status": "scheduled",
                "worker_contract": WORKER_CONTRACT,
                "apply_certified": True,
                "apply_blocker": None,
                "current_version": current_version,
                "install_dir": str(install_dir),
                "health_url": f"http://127.0.0.1:{port}/health",
                "health_timeout_seconds": HEALTH_TIMEOUT_SECONDS,
                "windows_worker_filename": f"{WORKER_DIR_NAME}/{WORKER_NAME}",
                "windows_worker_sha256": worker_sha,
                "windows_worker_core_filename": f"{WORKER_DIR_NAME}/{WORKER_CORE_NAME}",
                "windows_worker_core_sha256": core_sha,
            }
        )
        UpdateEngine._write_job(scheduled)

        command = [
            str(powershell),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(worker),
            "-JobPath",
            str(job_dir / "job.json"),
            "-ParentPid",
            str(parent_pid),
        ]
        try:
            proc = adapter.launch_detached(command)
        except Exception as exc:
            failed = dict(scheduled)
            failed.update(
                {
                    "status": "failed_pre_apply",
                    "worker_result": "scheduler_launch_failed",
                    "apply_certified": False,
                    "apply_blocker": "UPDATE_WINDOWS_WORKER_LAUNCH_FAILED",
                    "failure_reason": "UPDATE_WINDOWS_WORKER_LAUNCH_FAILED",
                }
            )
            UpdateEngine._write_job(failed)
            raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_LAUNCH_FAILED") from exc

        result = dict(scheduled)
        result["worker_pid"] = int(proc.pid)
        return result
