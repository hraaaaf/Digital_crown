from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.core.platform import get_platform_adapter
from backend.services.update_engine import UpdateEngine, UpdatePreparationError


CONFIRMATION_TOKEN = "METTRE_A_JOUR"
WINDOWS_WORKER_CONTRACT = "windows-inno-v1"
WINDOWS_RECOVERY_CONTRACT = "windows-interruption-v1"
WINDOWS_PRIVATE_PUBLISHER_SUBJECT = "CN=Digital Crown Private Publisher"
WINDOWS_ENTRY_FILE = "windows_update_worker_entry.ps1"
WINDOWS_WORKER_FILES = (
    "windows_update_worker.ps1",
    "windows_update_worker_core.ps1",
)
WINDOWS_RECOVERY_FILE = "windows_update_recovery.ps1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class UpdateApplyService:
    @staticmethod
    def runtime_apply_supported() -> bool:
        adapter = get_platform_adapter()
        return (
            bool(getattr(sys, "frozen", False))
            and os.environ.get("ENVIRONMENT", "").strip().lower() == "cabinet"
            and adapter.is_windows
        )

    @staticmethod
    def _bundle_root() -> Path:
        frozen_root = getattr(sys, "_MEIPASS", None)
        if frozen_root:
            return Path(str(frozen_root)).resolve()
        return Path(__file__).resolve().parents[2]

    @classmethod
    def _current_version(cls) -> str:
        path = cls._bundle_root() / "VERSION"
        if not path.is_file():
            raise UpdatePreparationError("UPDATE_CURRENT_VERSION_MISSING")
        value = path.read_text(encoding="utf-8").strip()
        parts = value.split(".")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise UpdatePreparationError("UPDATE_CURRENT_VERSION_INVALID")
        return value

    @staticmethod
    def _windows_powershell51() -> Path:
        path = get_platform_adapter().windows_powershell51_path()
        if path is None:
            raise UpdatePreparationError("UPDATE_WINDOWS_POWERSHELL51_MISSING")
        return path

    @staticmethod
    def _installed_executable() -> Path:
        executable = Path(sys.executable).resolve()
        if executable.name.lower() != "digitalcrown.exe" or not executable.is_file():
            raise UpdatePreparationError("UPDATE_WINDOWS_INSTALLED_EXECUTABLE_INVALID")
        return executable

    @staticmethod
    def _health_url() -> str:
        raw = os.environ.get("CABINET_PORT", "8005").strip()
        try:
            port = int(raw)
        except ValueError as exc:
            raise UpdatePreparationError("UPDATE_WINDOWS_HEALTH_PORT_INVALID") from exc
        if not (1 <= port <= 65535):
            raise UpdatePreparationError("UPDATE_WINDOWS_HEALTH_PORT_INVALID")
        return f"http://127.0.0.1:{port}/health"

    @classmethod
    def _validate_prepared_job(cls, job: dict[str, Any]) -> tuple[Path, Path]:
        if str(job.get("status") or "") != "prepared":
            raise UpdatePreparationError("UPDATE_JOB_STATE_INVALID")
        if str(job.get("platform") or "").lower() != "windows":
            raise UpdatePreparationError("UPDATE_PLATFORM_APPLY_NOT_WIRED")

        job_dir = UpdateEngine._job_dir(str(job.get("job_id") or ""))
        artifact_name = str(job.get("artifact_filename") or "")
        if Path(artifact_name).name != artifact_name or not artifact_name.lower().endswith(".exe"):
            raise UpdatePreparationError("UPDATE_WINDOWS_ARTIFACT_FILENAME_INVALID")
        artifact = job_dir / artifact_name
        if not artifact.is_file():
            raise UpdatePreparationError("UPDATE_ARTIFACT_MISSING")
        try:
            expected_size = int(job.get("artifact_size_bytes"))
        except (TypeError, ValueError) as exc:
            raise UpdatePreparationError("UPDATE_ARTIFACT_SIZE_INVALID") from exc
        if artifact.stat().st_size != expected_size:
            raise UpdatePreparationError("UPDATE_ARTIFACT_SIZE_MISMATCH")
        expected_artifact_sha = str(job.get("artifact_sha256") or "").lower()
        if len(expected_artifact_sha) != 64 or _sha256(artifact) != expected_artifact_sha:
            raise UpdatePreparationError("UPDATE_ARTIFACT_SHA256_MISMATCH")

        rescue_rel = Path(str(job.get("rescue_backup_filename") or ""))
        if rescue_rel.is_absolute() or ".." in rescue_rel.parts:
            raise UpdatePreparationError("UPDATE_RESCUE_PATH_INVALID")
        rescue = (job_dir / rescue_rel).resolve()
        try:
            rescue.relative_to(job_dir.resolve())
        except ValueError as exc:
            raise UpdatePreparationError("UPDATE_RESCUE_PATH_INVALID") from exc
        if not rescue.is_file():
            raise UpdatePreparationError("UPDATE_RESCUE_BACKUP_MISSING")
        expected_rescue_sha = str(job.get("rescue_backup_sha256") or "").lower()
        if len(expected_rescue_sha) != 64 or _sha256(rescue) != expected_rescue_sha:
            raise UpdatePreparationError("UPDATE_RESCUE_BACKUP_SHA256_MISMATCH")
        return artifact, rescue

    @staticmethod
    def _stage_script(source: Path, target: Path, expected: str) -> None:
        partial = target.with_name(target.name + ".partial")
        try:
            shutil.copy2(source, partial)
            if _sha256(partial) != expected:
                raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_COPY_VERIFY_FAILED")
            os.replace(partial, target)
        finally:
            partial.unlink(missing_ok=True)

    @classmethod
    def _stage_windows_workers(cls, job: dict[str, Any]) -> None:
        job_dir = UpdateEngine._job_dir(str(job["job_id"]))
        source_dir = cls._bundle_root() / "scripts"
        target_dir = get_platform_adapter().ensure_private_directory(job_dir / "worker")
        entry_source = source_dir / WINDOWS_ENTRY_FILE
        if not entry_source.is_file():
            raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_SOURCE_MISSING")
        entry_sha = _sha256(entry_source)
        cls._stage_script(entry_source, target_dir / WINDOWS_ENTRY_FILE, entry_sha)
        job[f"{WINDOWS_ENTRY_FILE}_sha256"] = entry_sha

        for filename in WINDOWS_WORKER_FILES:
            source = source_dir / filename
            if not source.is_file():
                raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_SOURCE_MISSING")
            expected = _sha256(source)
            target = target_dir / filename
            cls._stage_script(source, target, expected)
            job[f"{filename}_sha256"] = expected

        recovery_source = source_dir / WINDOWS_RECOVERY_FILE
        if not recovery_source.is_file():
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_SOURCE_MISSING")
        recovery_sha = _sha256(recovery_source)
        recovery_target = target_dir / WINDOWS_RECOVERY_FILE
        cls._stage_script(recovery_source, recovery_target, recovery_sha)
        job[f"{WINDOWS_RECOVERY_FILE}_sha256"] = recovery_sha

        job["worker_filename"] = f"worker/{WINDOWS_ENTRY_FILE}"
        job["worker_wrapper_filename"] = f"worker/{WINDOWS_WORKER_FILES[0]}"
        job["worker_core_filename"] = f"worker/{WINDOWS_WORKER_FILES[1]}"
        job["worker_recovery_filename"] = f"worker/{WINDOWS_RECOVERY_FILE}"
        job["worker_contract"] = WINDOWS_WORKER_CONTRACT
        job["recovery_contract"] = WINDOWS_RECOVERY_CONTRACT

    @classmethod
    def _verify_staged_workers(cls, job: dict[str, Any]) -> tuple[Path, Path]:
        job_dir = UpdateEngine._job_dir(str(job["job_id"]))

        def resolve(field: str, filename: str, error_code: str) -> Path:
            rel = Path(str(job.get(field) or ""))
            if rel.is_absolute() or ".." in rel.parts:
                raise UpdatePreparationError(error_code)
            path = (job_dir / rel).resolve()
            try:
                path.relative_to(job_dir.resolve())
            except ValueError as exc:
                raise UpdatePreparationError(error_code) from exc
            expected = str(job.get(f"{filename}_sha256") or "").lower()
            if not path.is_file() or len(expected) != 64 or _sha256(path) != expected:
                raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_SHA256_MISMATCH")
            return path

        entry = resolve("worker_filename", WINDOWS_ENTRY_FILE, "UPDATE_WINDOWS_WORKER_PATH_INVALID")
        resolve("worker_wrapper_filename", WINDOWS_WORKER_FILES[0], "UPDATE_WINDOWS_WORKER_PATH_INVALID")
        core = resolve("worker_core_filename", WINDOWS_WORKER_FILES[1], "UPDATE_WINDOWS_WORKER_PATH_INVALID")
        recovery = resolve("worker_recovery_filename", WINDOWS_RECOVERY_FILE, "UPDATE_RECOVERY_WORKER_PATH_INVALID")
        if str(job.get("recovery_contract") or "") != WINDOWS_RECOVERY_CONTRACT or not recovery.is_file():
            raise UpdatePreparationError("UPDATE_RECOVERY_WORKER_SHA256_MISMATCH")
        return entry, core

    @classmethod
    def _verify_windows_authenticode(cls, artifact: Path) -> dict[str, str]:
        powershell = cls._windows_powershell51()
        command = (
            "$s=Get-AuthenticodeSignature -LiteralPath $args[0];"
            "$signer='';$subject='';if($s.SignerCertificate){$signer=[string]$s.SignerCertificate.Thumbprint;$subject=[string]$s.SignerCertificate.Subject};"
            "$timestamp='';if($s.TimeStamperCertificate){$timestamp=[string]$s.TimeStamperCertificate.Thumbprint};"
            r"$publisherTrusted=$false;if($signer){$publisherTrusted=[bool](Get-ChildItem Cert:\LocalMachine\TrustedPublisher | Where-Object {$_.Thumbprint -eq $signer} | Select-Object -First 1)};"
            r"$rootTrusted=$false;if($signer){$rootTrusted=[bool](Get-ChildItem Cert:\LocalMachine\Root | Where-Object {$_.Thumbprint -eq $signer} | Select-Object -First 1)};"
            "$o=[ordered]@{status=[string]$s.Status;signer_thumbprint=$signer;signer_subject=$subject;timestamp_thumbprint=$timestamp;publisher_trusted=$publisherTrusted;root_trusted=$rootTrusted};"
            "$o|ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                [str(powershell), "-NoProfile", "-NonInteractive", "-Command", command, str(artifact)],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise UpdatePreparationError("UPDATE_WINDOWS_AUTHENTICODE_CHECK_FAILED") from exc
        if result.returncode != 0:
            raise UpdatePreparationError("UPDATE_WINDOWS_AUTHENTICODE_CHECK_FAILED")
        try:
            payload = json.loads(result.stdout.strip())
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise UpdatePreparationError("UPDATE_WINDOWS_AUTHENTICODE_CHECK_INVALID") from exc
        status = str(payload.get("status") or "")
        signer = str(payload.get("signer_thumbprint") or "").strip().upper()
        subject = str(payload.get("signer_subject") or "").strip()
        timestamp = str(payload.get("timestamp_thumbprint") or "").strip().upper()
        publisher_trusted = payload.get("publisher_trusted") is True
        root_trusted = payload.get("root_trusted") is True
        if status != "Valid" or not signer:
            raise UpdatePreparationError("UPDATE_WINDOWS_AUTHENTICODE_INVALID")
        if subject != WINDOWS_PRIVATE_PUBLISHER_SUBJECT:
            raise UpdatePreparationError("UPDATE_WINDOWS_AUTHENTICODE_SIGNER_NOT_DIGITALCROWN")
        if not publisher_trusted or not root_trusted:
            raise UpdatePreparationError("UPDATE_WINDOWS_PRIVATE_PUBLISHER_TRUST_REQUIRED")
        if not timestamp:
            raise UpdatePreparationError("UPDATE_WINDOWS_AUTHENTICODE_TIMESTAMP_REQUIRED")
        return {
            "status": status,
            "signer_thumbprint": signer,
            "signer_subject": subject,
            "timestamp_thumbprint": timestamp,
        }

    @classmethod
    def _arm_windows_job(cls, job: dict[str, Any], artifact: Path) -> dict[str, Any]:
        cls._stage_windows_workers(job)
        cls._verify_staged_workers(job)
        executable = cls._installed_executable()
        job.update(
            current_version=cls._current_version(),
            install_dir=str(executable.parent),
            health_url=cls._health_url(),
            health_timeout_seconds=60,
            apply_certified=False,
            apply_blocker="WINDOWS_AUTHENTICODE_REQUIRED",
        )
        try:
            signature = cls._verify_windows_authenticode(artifact)
        except UpdatePreparationError as exc:
            job["updated_at"] = _utc_now()
            job["apply_certified"] = False
            job["apply_blocker"] = str(exc)
            UpdateEngine._write_job(job)
            raise
        job.update(
            apply_certified=True,
            apply_blocker=None,
            authenticode_status=signature["status"],
            authenticode_signer_thumbprint=signature["signer_thumbprint"],
            authenticode_signer_subject=signature["signer_subject"],
            authenticode_timestamp_thumbprint=signature["timestamp_thumbprint"],
            certification_checked_at=_utc_now(),
        )
        cls._verify_staged_workers(job)
        job["updated_at"] = _utc_now()
        UpdateEngine._write_job(job)
        return job

    @classmethod
    def request_apply(cls, job_id: str, confirmation: str) -> dict[str, Any]:
        if confirmation != CONFIRMATION_TOKEN:
            raise ValueError(f"Confirmation exacte requise : {CONFIRMATION_TOKEN}")
        if not cls.runtime_apply_supported():
            raise UpdatePreparationError("UPDATE_RUNTIME_APPLY_UNSUPPORTED")

        job = UpdateEngine.get_job(job_id)
        artifact, _ = cls._validate_prepared_job(job)
        job = cls._arm_windows_job(job, artifact)
        UpdateEngine.require_certified_apply(job_id)
        worker, _ = cls._verify_staged_workers(job)

        job["status"] = "scheduled"
        job["scheduled_at"] = _utc_now()
        job["updated_at"] = job["scheduled_at"]
        UpdateEngine._write_job(job)
        try:
            cls._launch_detached_worker(worker, UpdateEngine._job_dir(job_id) / "job.json", os.getpid())
        except Exception as exc:
            job["status"] = "prepared"
            job["apply_certified"] = False
            job["apply_blocker"] = "UPDATE_WINDOWS_WORKER_LAUNCH_FAILED"
            job["updated_at"] = _utc_now()
            UpdateEngine._write_job(job)
            raise UpdatePreparationError("UPDATE_WINDOWS_WORKER_LAUNCH_FAILED") from exc
        cls._schedule_parent_exit()
        return cls.public_job(job)

    @classmethod
    def _launch_detached_worker(cls, worker: Path, job_path: Path, parent_pid: int) -> None:
        powershell = cls._windows_powershell51()
        subprocess.Popen(
            [
                str(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(worker),
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

    @classmethod
    def _schedule_parent_exit(cls) -> None:
        threading.Thread(target=cls._terminate_parent_after_response, daemon=True).start()

    @staticmethod
    def _terminate_parent_after_response() -> None:
        time.sleep(0.8)
        os._exit(0)

    @staticmethod
    def public_job(job: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "job_id",
            "status",
            "created_at",
            "updated_at",
            "scheduled_at",
            "sequence",
            "version",
            "current_version",
            "platform",
            "architecture",
            "artifact_filename",
            "apply_certified",
            "apply_blocker",
            "authenticode_status",
            "authenticode_signer_subject",
            "certification_checked_at",
            "worker_contract",
            "recovery_contract",
            "worker_result",
            "package_self_test",
            "runtime_health",
            "rollback",
            "database_rollback",
            "failure_reason",
            "rollback_failure_reason",
            "recovery_scheduled_at",
            "recovery_started_at",
            "recovery_failure_reason",
        }
        return {key: value for key, value in job.items() if key in allowed}

    @classmethod
    def get_public_job(cls, job_id: str) -> dict[str, Any]:
        return cls.public_job(UpdateEngine.get_job(job_id))