from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.core.platform import get_platform_adapter
from backend.services.macos_update_apply import (
    MACOS_APP_NAME,
    MACOS_EXECUTABLE_REL,
    MACOS_RECOVERY_CONTRACT,
    MACOS_WORKER_CONTRACT,
    MacOSUpdateApplyService,
)
from backend.services.update_engine import UpdateEngine, UpdatePreparationError
from backend.services.update_post_install import (
    UpdatePostInstallError,
    verify_package_self_test,
    wait_runtime_health,
)


MACOS_DB_RECOVERY_FAILURES = {
    "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED",
    "UPDATE_MACOS_DB_ROLLBACK_FAILED",
    "UPDATE_MACOS_DB_ROLLBACK_RUNTIME_HEALTH_FAILED",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MacOSUpdateWorker:
    """Detached macOS package mutation + rollback worker executed from the rescue app copy."""

    @classmethod
    def _load_job(cls, job_path: Path) -> tuple[Path, Path, dict[str, Any]]:
        resolved = Path(job_path).resolve()
        if resolved.name != "job.json" or not resolved.is_file():
            raise UpdatePreparationError("UPDATE_MACOS_JOB_MISSING")
        job_id = resolved.parent.name
        canonical = (UpdateEngine._job_dir(job_id) / "job.json").resolve()
        if resolved != canonical:
            raise UpdatePreparationError("UPDATE_MACOS_JOB_PATH_INVALID")
        try:
            job = json.loads(resolved.read_text(encoding="utf-8"))
        except Exception as exc:
            raise UpdatePreparationError("UPDATE_MACOS_JOB_INVALID") from exc
        if int(job.get("schema") or 0) != 1:
            raise UpdatePreparationError("UPDATE_MACOS_JOB_SCHEMA_UNSUPPORTED")
        if str(job.get("job_id") or "") != job_id:
            raise UpdatePreparationError("UPDATE_MACOS_JOB_ID_INVALID")
        if str(job.get("platform") or "").lower() != "macos":
            raise UpdatePreparationError("UPDATE_MACOS_PLATFORM_INVALID")
        if str(job.get("worker_contract") or "") != MACOS_WORKER_CONTRACT:
            raise UpdatePreparationError("UPDATE_MACOS_WORKER_CONTRACT_INVALID")
        if str(job.get("recovery_contract") or "") != MACOS_RECOVERY_CONTRACT:
            raise UpdatePreparationError("UPDATE_MACOS_RECOVERY_CONTRACT_INVALID")
        if job.get("apply_certified") is not True:
            raise UpdatePreparationError("UPDATE_PLATFORM_APPLY_NOT_CERTIFIED")
        return resolved, resolved.parent, job

    @classmethod
    def _save(cls, job: dict[str, Any]) -> None:
        job["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        UpdateEngine._write_job(job)

    @staticmethod
    def _wait_parent_exit(parent_pid: int, timeout: float = 30.0) -> None:
        if parent_pid <= 0 or parent_pid == os.getpid():
            raise UpdatePreparationError("UPDATE_MACOS_PARENT_PID_INVALID")
        deadline = time.monotonic() + timeout
        adapter = get_platform_adapter()
        while time.monotonic() < deadline:
            if not adapter.is_process_alive(parent_pid):
                return
            time.sleep(0.25)
        raise UpdatePreparationError("UPDATE_MACOS_PARENT_EXIT_TIMEOUT")

    @staticmethod
    def _resolve_job_child(job_dir: Path, raw: str, error_code: str) -> Path:
        rel = Path(str(raw or ""))
        if not str(raw or "") or rel.is_absolute() or ".." in rel.parts:
            raise UpdatePreparationError(error_code)
        path = (job_dir / rel).resolve()
        try:
            path.relative_to(job_dir.resolve())
        except ValueError as exc:
            raise UpdatePreparationError(error_code) from exc
        return path

    @staticmethod
    def _semver(value: str, error_code: str) -> tuple[int, int, int]:
        parts = str(value or "").strip().split(".")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise UpdatePreparationError(error_code)
        return tuple(int(part) for part in parts)  # type: ignore[return-value]

    @staticmethod
    def _validated_health_url(value: str) -> str:
        try:
            parsed = urlparse(str(value or ""))
            port = parsed.port
        except ValueError as exc:
            raise UpdatePreparationError("UPDATE_MACOS_HEALTH_URL_INVALID") from exc
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.path != "/health"
            or parsed.params
            or parsed.query
            or parsed.fragment
            or port is None
            or not (1 <= port <= 65535)
        ):
            raise UpdatePreparationError("UPDATE_MACOS_HEALTH_URL_NOT_LOOPBACK")
        return parsed.geturl()

    @classmethod
    def _validate_context(cls, job_dir: Path, job: dict[str, Any]) -> dict[str, Any]:
        artifact = cls._resolve_job_child(
            job_dir,
            str(job.get("artifact_filename") or ""),
            "UPDATE_MACOS_ARTIFACT_PATH_INVALID",
        )
        if not artifact.is_file() or artifact.suffix.lower() != ".dmg":
            raise UpdatePreparationError("UPDATE_MACOS_ARTIFACT_MISSING")
        if artifact.stat().st_size != int(job.get("artifact_size_bytes") or 0):
            raise UpdatePreparationError("UPDATE_ARTIFACT_SIZE_MISMATCH")
        expected_sha = str(job.get("artifact_sha256") or "").lower()
        if len(expected_sha) != 64 or _sha256(artifact) != expected_sha:
            raise UpdatePreparationError("UPDATE_ARTIFACT_SHA256_MISMATCH")

        rescue_db = cls._resolve_job_child(
            job_dir,
            str(job.get("rescue_backup_filename") or ""),
            "UPDATE_RESCUE_PATH_INVALID",
        )
        rescue_db_sha = str(job.get("rescue_backup_sha256") or "").lower()
        if not rescue_db.is_file() or len(rescue_db_sha) != 64 or _sha256(rescue_db) != rescue_db_sha:
            raise UpdatePreparationError("UPDATE_RESCUE_BACKUP_SHA256_MISMATCH")

        rescue_app = cls._resolve_job_child(
            job_dir,
            str(job.get("rescue_app_filename") or ""),
            "UPDATE_MACOS_RESCUE_APP_PATH_INVALID",
        )
        if not rescue_app.is_dir() or rescue_app.name != MACOS_APP_NAME:
            raise UpdatePreparationError("UPDATE_MACOS_RESCUE_APP_MISSING")
        manifest = job_dir / "rescue" / "program-manifest.json"
        expected_manifest_sha = str(job.get("program_manifest_sha256") or "").lower()
        if not manifest.is_file() or len(expected_manifest_sha) != 64 or _sha256(manifest) != expected_manifest_sha:
            raise UpdatePreparationError("UPDATE_MACOS_PROGRAM_RESCUE_MANIFEST_INVALID")
        try:
            expected_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception as exc:
            raise UpdatePreparationError("UPDATE_MACOS_PROGRAM_RESCUE_MANIFEST_INVALID") from exc
        if MacOSUpdateApplyService._tree_manifest(rescue_app) != expected_manifest:
            raise UpdatePreparationError("UPDATE_MACOS_PROGRAM_RESCUE_INTEGRITY_FAILED")

        raw_install = Path(str(job.get("install_app") or ""))
        if not raw_install.is_absolute():
            raise UpdatePreparationError("UPDATE_MACOS_INSTALL_APP_INVALID")
        install_app = raw_install.resolve()
        if install_app.name != MACOS_APP_NAME:
            raise UpdatePreparationError("UPDATE_MACOS_INSTALL_APP_INVALID")
        try:
            install_app.relative_to(job_dir.resolve())
            raise UpdatePreparationError("UPDATE_MACOS_PATH_OVERLAP")
        except ValueError:
            pass
        install_parent = install_app.parent
        if not install_parent.is_dir() or not os.access(install_parent, os.W_OK):
            raise UpdatePreparationError("UPDATE_MACOS_INSTALL_PARENT_NOT_WRITABLE")

        health_url = cls._validated_health_url(str(job.get("health_url") or ""))
        timeout = int(job.get("health_timeout_seconds") or 60)
        if not 3 <= timeout <= 180:
            raise UpdatePreparationError("UPDATE_MACOS_HEALTH_TIMEOUT_INVALID")

        current_version = str(job.get("current_version") or "")
        target_version = str(job.get("version") or "")
        current_semver = cls._semver(current_version, "UPDATE_MACOS_CURRENT_VERSION_INVALID")
        target_semver = cls._semver(target_version, "UPDATE_MACOS_TARGET_VERSION_INVALID")
        if target_semver <= current_semver:
            raise UpdatePreparationError("UPDATE_MACOS_TARGET_NOT_NEWER")
        return {
            "artifact": artifact,
            "rescue_db": rescue_db,
            "rescue_app": rescue_app,
            "install_app": install_app,
            "install_parent": install_parent,
            "health_url": health_url,
            "health_timeout": timeout,
            "current_version": current_version,
            "target_version": target_version,
        }

    @staticmethod
    def _executable(app: Path) -> Path:
        path = app / MACOS_EXECUTABLE_REL
        if not path.is_file():
            raise UpdatePreparationError("UPDATE_MACOS_EXECUTABLE_MISSING")
        return path

    @classmethod
    def _self_test(cls, app: Path, version: str, report_dir: Path) -> None:
        try:
            verify_package_self_test(
                cls._executable(app),
                expected_version=version,
                report_dir=report_dir,
                timeout=120,
            )
        except UpdatePostInstallError as exc:
            raise UpdatePreparationError("UPDATE_MACOS_PACKAGE_SELF_TEST_FAILED") from exc

    @staticmethod
    def _launch_runtime(app: Path) -> subprocess.Popen:
        executable = MacOSUpdateWorker._executable(app)
        env = os.environ.copy()
        env["DIGITALCROWN_RESTORE_RESTART"] = "1"
        return subprocess.Popen(
            [str(executable)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            **get_platform_adapter().detached_process_kwargs(),
        )

    @staticmethod
    def _stop_runtime(proc: subprocess.Popen | None) -> None:
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    @staticmethod
    def _wait_health(url: str, timeout: int) -> None:
        try:
            wait_runtime_health(health_url=url, timeout=timeout, poll_interval=0.5)
        except UpdatePostInstallError as exc:
            raise UpdatePreparationError("UPDATE_MACOS_RUNTIME_HEALTH_FAILED") from exc

    @classmethod
    def _stage_target(cls, context: dict[str, Any], job_id: str, report_dir: Path) -> Path:
        install_parent: Path = context["install_parent"]
        staged = install_parent / f".{MACOS_APP_NAME}.update-{job_id}"
        if staged.exists():
            shutil.rmtree(staged)
        with MacOSUpdateApplyService._mounted_dmg(context["artifact"]) as mount:
            source = mount / MACOS_APP_NAME
            MacOSUpdateApplyService._verify_app_bundle(
                source,
                expected_version=context["target_version"],
            )
            MacOSUpdateApplyService._copy_bundle_verified(source, staged)
        cls._self_test(staged, context["target_version"], report_dir)
        return staged

    @staticmethod
    def _side_backup(context: dict[str, Any], job_id: str) -> Path:
        return context["install_parent"] / f".{MACOS_APP_NAME}.rollback-{job_id}"

    @classmethod
    def _restore_program(cls, context: dict[str, Any], job_id: str, report_dir: Path) -> None:
        install_app: Path = context["install_app"]
        side_backup = cls._side_backup(context, job_id)
        if install_app.exists():
            shutil.rmtree(install_app)
        if side_backup.is_dir():
            os.replace(side_backup, install_app)
        else:
            MacOSUpdateApplyService._copy_bundle_verified(context["rescue_app"], install_app)
        cls._self_test(install_app, context["current_version"], report_dir)

    @classmethod
    def _finalize_target(cls, job_path: Path, context: dict[str, Any]) -> None:
        proc = subprocess.run(
            [
                str(cls._executable(context["install_app"])),
                "--update-finalize-worker",
                str(job_path),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=False,
            env={**os.environ, "DIGITALCROWN_RESTORE_RESTART": "1"},
        )
        if proc.returncode != 0:
            raise UpdatePreparationError("UPDATE_MACOS_FINALIZATION_FAILED")
        finalized = UpdateEngine.get_job(job_path.parent.name)
        if str(finalized.get("status") or "") != "healthy":
            raise UpdatePreparationError("UPDATE_MACOS_FINALIZATION_TRUTH_INVALID")

    @staticmethod
    def _cleanup_side_backup(side_backup: Path) -> None:
        """Best-effort cleanup after durable finalization; cleanup can never trigger rollback."""
        try:
            if side_backup.exists():
                shutil.rmtree(side_backup)
        except Exception:
            pass

    @staticmethod
    def _database_recovery_authorized(job: dict[str, Any]) -> bool:
        status = str(job.get("status") or "")
        if str(job.get("worker_result") or "") != "rollback_failed":
            return False
        if str(job.get("rollback") or "") != "failed":
            return False
        database_state = str(job.get("database_rollback") or "")
        failure = str(job.get("rollback_failure_reason") or "")
        if status == "database_rolling_back":
            return (
                database_state == "running"
                and failure == "UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED"
            )
        return (
            status == "rollback_failed"
            and database_state in {"running", "failed"}
            and failure in MACOS_DB_RECOVERY_FAILURES
        )

    @classmethod
    def _database_rollback(
        cls,
        job_path: Path,
        context: dict[str, Any],
        job: dict[str, Any],
    ) -> None:
        job.update(
            status="database_rolling_back",
            worker_result="rollback_failed",
            rollback="failed",
            rollback_failure_reason="UPDATE_MACOS_PACKAGE_ROLLBACK_HEALTH_FAILED",
            database_rollback="running",
        )
        cls._save(job)
        rescue_exe = cls._executable(context["rescue_app"])
        proc = subprocess.run(
            [
                str(rescue_exe),
                "--macos-update-db-rollback-worker",
                str(job_path),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
            check=False,
            env={**os.environ, "DIGITALCROWN_RESTORE_RESTART": "1"},
        )
        if proc.returncode != 0:
            raise UpdatePreparationError("UPDATE_MACOS_DB_ROLLBACK_FAILED")

    @classmethod
    def _finish_database_rollback(
        cls,
        job_path: Path,
        context: dict[str, Any],
        job: dict[str, Any],
    ) -> int:
        report_dir = job_path.parent
        cls._restore_program(context, str(job["job_id"]), report_dir)
        cls._database_rollback(job_path, context, job)
        rollback_runtime = cls._launch_runtime(context["install_app"])
        try:
            cls._wait_health(context["health_url"], context["health_timeout"])
        except Exception as exc:
            cls._stop_runtime(rollback_runtime)
            raise UpdatePreparationError("UPDATE_MACOS_DB_ROLLBACK_RUNTIME_HEALTH_FAILED") from exc
        job.update(
            status="rolled_back",
            worker_result="rolled_back",
            rollback="passed",
            database_rollback="passed",
            runtime_pid=int(rollback_runtime.pid),
        )
        cls._save(job)
        return 2

    @classmethod
    def _rollback(
        cls,
        job_path: Path,
        context: dict[str, Any],
        job: dict[str, Any],
        failure: str,
    ) -> int:
        job.update(status="rolling_back", failure_reason=failure)
        cls._save(job)
        report_dir = job_path.parent
        cls._restore_program(context, str(job["job_id"]), report_dir)
        rollback_runtime = cls._launch_runtime(context["install_app"])
        try:
            cls._wait_health(context["health_url"], context["health_timeout"])
            job.update(
                status="rolled_back",
                worker_result="rolled_back",
                rollback="passed",
                database_rollback="not_needed",
                runtime_pid=int(rollback_runtime.pid),
            )
            cls._save(job)
            return 2
        except Exception:
            cls._stop_runtime(rollback_runtime)

        return cls._finish_database_rollback(job_path, context, job)

    @classmethod
    def _apply(
        cls,
        job_path: Path,
        context: dict[str, Any],
        job: dict[str, Any],
        parent_pid: int,
    ) -> int:
        if str(job.get("status") or "") != "scheduled":
            raise UpdatePreparationError("UPDATE_MACOS_JOB_STATE_INVALID")
        cls._wait_parent_exit(parent_pid)
        report_dir = job_path.parent
        cls._self_test(context["rescue_app"], context["current_version"], report_dir)
        MacOSUpdateApplyService._verify_macos_distribution(
            context["artifact"],
            expected_version=context["target_version"],
        )
        staged = cls._stage_target(context, str(job["job_id"]), report_dir)
        side_backup = cls._side_backup(context, str(job["job_id"]))
        if side_backup.exists():
            shutil.rmtree(side_backup)

        job.update(
            status="applying",
            worker_started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        cls._save(job)
        mutation_started = False
        target_runtime: subprocess.Popen | None = None
        try:
            os.replace(context["install_app"], side_backup)
            mutation_started = True
            os.replace(staged, context["install_app"])
            cls._self_test(context["install_app"], context["target_version"], report_dir)
            target_runtime = cls._launch_runtime(context["install_app"])
            cls._wait_health(context["health_url"], context["health_timeout"])
            job.update(
                status="health_pending",
                worker_result="install_verified",
                package_self_test="passed",
                runtime_health="passed",
                rollback="not_needed",
                database_rollback="not_needed",
                runtime_pid=int(target_runtime.pid),
            )
            cls._save(job)
            cls._finalize_target(job_path, context)
        except Exception as exc:
            cls._stop_runtime(target_runtime)
            if staged.exists():
                shutil.rmtree(staged, ignore_errors=True)
            if not mutation_started:
                job.update(
                    status="failed_pre_apply",
                    worker_result="blocked_before_mutation",
                    failure_reason=str(exc),
                )
                cls._save(job)
                return 1
            try:
                return cls._rollback(job_path, context, job, str(exc))
            except Exception as rollback_exc:
                job.update(
                    status="rollback_failed",
                    worker_result="rollback_failed",
                    rollback="failed",
                    database_rollback=(
                        "failed"
                        if str(job.get("database_rollback")) == "running"
                        else job.get("database_rollback", "not_started")
                    ),
                    rollback_failure_reason=str(rollback_exc),
                )
                cls._save(job)
                return 3

        # Finalization has already committed canonical installed truth. Cleanup is
        # explicitly outside the rollback-capable try/except.
        cls._cleanup_side_backup(side_backup)
        return 0

    @classmethod
    def _recover(
        cls,
        job_path: Path,
        context: dict[str, Any],
        job: dict[str, Any],
        parent_pid: int,
    ) -> int:
        cls._wait_parent_exit(parent_pid)
        status = str(job.get("status") or "")
        report_dir = job_path.parent
        if status in {"healthy", "rolled_back", "failed_pre_apply"}:
            return 0
        if status == "health_pending":
            try:
                cls._self_test(context["install_app"], context["target_version"], report_dir)
                runtime = cls._launch_runtime(context["install_app"])
                cls._wait_health(context["health_url"], context["health_timeout"])
                job["runtime_pid"] = int(runtime.pid)
                cls._save(job)
                cls._finalize_target(job_path, context)
            except Exception as exc:
                return cls._rollback(job_path, context, job, str(exc))
            cls._cleanup_side_backup(cls._side_backup(context, str(job["job_id"])))
            return 0

        database_state = str(job.get("database_rollback") or "")
        if status == "database_rolling_back" or (
            status == "rollback_failed" and database_state in {"running", "failed"}
        ):
            if not cls._database_recovery_authorized(job):
                raise UpdatePreparationError("UPDATE_MACOS_DB_RECOVERY_NOT_AUTHORIZED")
            try:
                return cls._finish_database_rollback(job_path, context, job)
            except Exception as exc:
                job.update(
                    status="rollback_failed",
                    worker_result="rollback_failed",
                    rollback="failed",
                    database_rollback="failed",
                    rollback_failure_reason=str(exc),
                )
                cls._save(job)
                return 3

        if status in {"scheduled", "applying", "rolling_back", "rollback_failed"}:
            try:
                return cls._rollback(
                    job_path,
                    context,
                    job,
                    "UPDATE_MACOS_INTERRUPTION_RECOVERY",
                )
            except Exception as exc:
                job.update(
                    status="rollback_failed",
                    worker_result="rollback_failed",
                    rollback="failed",
                    rollback_failure_reason=str(exc),
                )
                cls._save(job)
                return 3
        raise UpdatePreparationError("UPDATE_MACOS_RECOVERY_STATE_INVALID")

    @classmethod
    def run(cls, job_path: Path, parent_pid: int, *, recovery: bool = False) -> int:
        lock = None
        try:
            resolved, job_dir, job = cls._load_job(job_path)
            context = cls._validate_context(job_dir, job)
            lock = get_platform_adapter().try_acquire_process_lock(job_dir / "worker.lock")
            if lock is None:
                return 5
            if recovery:
                return cls._recover(resolved, context, job, parent_pid)
            return cls._apply(resolved, context, job, parent_pid)
        except Exception:
            return 4
        finally:
            if lock is not None:
                lock.release()
