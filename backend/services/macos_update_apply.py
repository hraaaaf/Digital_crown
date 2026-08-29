from __future__ import annotations

import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from backend.core.platform import get_platform_adapter
from backend.services.update_apply import CONFIRMATION_TOKEN
from backend.services.update_engine import UpdateEngine, UpdatePreparationError


MACOS_WORKER_CONTRACT = "macos-dmg-v1"
MACOS_RECOVERY_CONTRACT = "macos-interruption-v1"
MACOS_BUNDLE_ID = "com.saninova.digitalcrown"
MACOS_APP_NAME = "DigitalCrown.app"
MACOS_EXECUTABLE_REL = Path("Contents") / "MacOS" / "DigitalCrown"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MacOSUpdateApplyService:
    """Fail-closed P10 apply boundary for a notarized macOS DMG."""

    @staticmethod
    def runtime_apply_supported() -> bool:
        adapter = get_platform_adapter()
        return (
            bool(getattr(sys, "frozen", False))
            and os.environ.get("ENVIRONMENT", "").strip().lower() == "cabinet"
            and adapter.is_macos
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
    def _installed_app() -> Path:
        executable = Path(sys.executable).resolve()
        if (
            executable.name != "DigitalCrown"
            or executable.parent.name != "MacOS"
            or executable.parent.parent.name != "Contents"
        ):
            raise UpdatePreparationError("UPDATE_MACOS_INSTALLED_EXECUTABLE_INVALID")
        app = executable.parent.parent.parent
        if app.name != MACOS_APP_NAME or not app.is_dir():
            raise UpdatePreparationError("UPDATE_MACOS_INSTALLED_APP_INVALID")
        return app

    @staticmethod
    def _health_url() -> str:
        raw = os.environ.get("CABINET_PORT", "8005").strip()
        try:
            port = int(raw)
        except ValueError as exc:
            raise UpdatePreparationError("UPDATE_MACOS_HEALTH_PORT_INVALID") from exc
        if not (1 <= port <= 65535):
            raise UpdatePreparationError("UPDATE_MACOS_HEALTH_PORT_INVALID")
        return f"http://127.0.0.1:{port}/health"

    @classmethod
    def _validate_prepared_job(cls, job: dict[str, Any]) -> tuple[Path, Path]:
        if str(job.get("status") or "") != "prepared":
            raise UpdatePreparationError("UPDATE_JOB_STATE_INVALID")
        if str(job.get("platform") or "").lower() != "macos":
            raise UpdatePreparationError("UPDATE_PLATFORM_APPLY_NOT_WIRED")
        if str(job.get("architecture") or "").lower() not in {"arm64", "aarch64"}:
            raise UpdatePreparationError("UPDATE_MACOS_ARCHITECTURE_UNSUPPORTED")

        job_dir = UpdateEngine._job_dir(str(job.get("job_id") or ""))
        artifact_name = str(job.get("artifact_filename") or "")
        if Path(artifact_name).name != artifact_name or not artifact_name.lower().endswith(".dmg"):
            raise UpdatePreparationError("UPDATE_MACOS_ARTIFACT_FILENAME_INVALID")
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
    def _run_checked(args: list[str], error_code: str, *, timeout: float = 120.0) -> str:
        try:
            proc = subprocess.run(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise UpdatePreparationError(error_code) from exc
        if proc.returncode != 0:
            raise UpdatePreparationError(f"{error_code}:{proc.returncode}")
        return proc.stdout

    @classmethod
    @contextmanager
    def _mounted_dmg(cls, dmg: Path) -> Iterator[Path]:
        mount = Path(tempfile.mkdtemp(prefix="digitalcrown-update-mount-"))
        attached = False
        try:
            cls._run_checked(
                ["/usr/bin/hdiutil", "attach", str(dmg), "-mountpoint", str(mount), "-nobrowse", "-readonly"],
                "UPDATE_MACOS_DMG_ATTACH_FAILED",
            )
            attached = True
            yield mount
        finally:
            if attached:
                subprocess.run(
                    ["/usr/bin/hdiutil", "detach", str(mount), "-force"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    timeout=30,
                )
            shutil.rmtree(mount, ignore_errors=True)

    @classmethod
    def _verify_app_bundle(cls, app: Path, *, expected_version: str) -> dict[str, str]:
        if not app.is_dir() or app.name != MACOS_APP_NAME:
            raise UpdatePreparationError("UPDATE_MACOS_DMG_APP_MISSING")
        info_path = app / "Contents" / "Info.plist"
        executable = app / MACOS_EXECUTABLE_REL
        if not info_path.is_file() or not executable.is_file():
            raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_INVALID")
        try:
            info = plistlib.loads(info_path.read_bytes())
        except Exception as exc:
            raise UpdatePreparationError("UPDATE_MACOS_INFO_PLIST_INVALID") from exc
        if info.get("CFBundleIdentifier") != MACOS_BUNDLE_ID:
            raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_ID_MISMATCH")
        if str(info.get("CFBundleShortVersionString") or "") != expected_version:
            raise UpdatePreparationError("UPDATE_MACOS_BUNDLE_VERSION_MISMATCH")
        cls._run_checked(
            ["/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=4", str(app)],
            "UPDATE_MACOS_CODESIGN_VERIFY_FAILED",
        )
        cls._run_checked(
            ["/usr/sbin/spctl", "--assess", "--type", "execute", "--verbose=4", str(app)],
            "UPDATE_MACOS_GATEKEEPER_APP_FAILED",
        )
        details = cls._run_checked(
            ["/usr/bin/codesign", "-d", "--verbose=4", str(app)],
            "UPDATE_MACOS_CODESIGN_DETAILS_FAILED",
        )
        if "Authority=Developer ID Application" not in details:
            raise UpdatePreparationError("UPDATE_MACOS_DEVELOPER_ID_REQUIRED")
        if "(runtime)" not in details:
            raise UpdatePreparationError("UPDATE_MACOS_HARDENED_RUNTIME_REQUIRED")
        if "Timestamp=" not in details:
            raise UpdatePreparationError("UPDATE_MACOS_SECURE_TIMESTAMP_REQUIRED")
        return {
            "bundle_id": MACOS_BUNDLE_ID,
            "version": expected_version,
            "developer_id": "valid",
            "hardened_runtime": "valid",
            "secure_timestamp": "valid",
        }

    @classmethod
    def _verify_macos_distribution(cls, dmg: Path, *, expected_version: str) -> dict[str, str]:
        cls._run_checked(
            ["/usr/bin/xcrun", "stapler", "validate", str(dmg)],
            "UPDATE_MACOS_STAPLE_INVALID",
        )
        cls._run_checked(
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
            "UPDATE_MACOS_GATEKEEPER_DMG_FAILED",
        )
        with cls._mounted_dmg(dmg) as mount:
            app = mount / MACOS_APP_NAME
            result = cls._verify_app_bundle(app, expected_version=expected_version)
        result.update(notarization="stapled", gatekeeper="valid")
        return result

    @staticmethod
    def _tree_manifest(root: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                rows.append({"path": rel, "type": "symlink", "target": os.readlink(path)})
            elif path.is_file():
                rows.append({"path": rel, "type": "file", "size": path.stat().st_size, "sha256": _sha256(path)})
            elif path.is_dir():
                rows.append({"path": rel, "type": "dir"})
        return rows

    @classmethod
    def _copy_bundle_verified(cls, source: Path, destination: Path) -> list[dict[str, Any]]:
        expected = cls._tree_manifest(source)
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        cls._run_checked(["/usr/bin/ditto", str(source), str(destination)], "UPDATE_MACOS_PROGRAM_COPY_FAILED")
        actual = cls._tree_manifest(destination)
        if actual != expected:
            shutil.rmtree(destination, ignore_errors=True)
            raise UpdatePreparationError("UPDATE_MACOS_PROGRAM_COPY_VERIFY_FAILED")
        return actual

    @classmethod
    def _snapshot_current_app(cls, job: dict[str, Any], install_app: Path) -> tuple[Path, str]:
        job_dir = UpdateEngine._job_dir(str(job["job_id"]))
        rescue_app = job_dir / "rescue" / "program" / MACOS_APP_NAME
        manifest_path = job_dir / "rescue" / "program-manifest.json"
        if rescue_app.exists() or manifest_path.exists():
            if not rescue_app.is_dir() or not manifest_path.is_file():
                raise UpdatePreparationError("UPDATE_MACOS_PROGRAM_RESCUE_INCOMPLETE")
            manifest_sha = _sha256(manifest_path)
            try:
                expected = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise UpdatePreparationError("UPDATE_MACOS_PROGRAM_RESCUE_MANIFEST_INVALID") from exc
            if cls._tree_manifest(rescue_app) != expected:
                raise UpdatePreparationError("UPDATE_MACOS_PROGRAM_RESCUE_INTEGRITY_FAILED")
            return rescue_app, manifest_sha

        manifest = cls._copy_bundle_verified(install_app, rescue_app)
        get_platform_adapter().atomic_write_text(
            manifest_path,
            json.dumps(manifest, indent=2, sort_keys=True),
        )
        return rescue_app, _sha256(manifest_path)

    @classmethod
    def _arm_job(cls, job: dict[str, Any], artifact: Path) -> dict[str, Any]:
        install_app = cls._installed_app()
        current_version = cls._current_version()
        if str(job.get("version") or "") == current_version:
            raise UpdatePreparationError("UPDATE_VERSION_NOT_NEWER")
        cls._verify_app_bundle(install_app, expected_version=current_version)
        distribution = cls._verify_macos_distribution(artifact, expected_version=str(job["version"]))
        rescue_app, manifest_sha = cls._snapshot_current_app(job, install_app)
        rescue_executable = rescue_app / MACOS_EXECUTABLE_REL
        if not rescue_executable.is_file():
            raise UpdatePreparationError("UPDATE_MACOS_RESCUE_EXECUTABLE_MISSING")
        job.update(
            current_version=current_version,
            install_app=str(install_app),
            health_url=cls._health_url(),
            health_timeout_seconds=60,
            worker_contract=MACOS_WORKER_CONTRACT,
            recovery_contract=MACOS_RECOVERY_CONTRACT,
            rescue_app_filename=str(rescue_app.relative_to(UpdateEngine._job_dir(str(job["job_id"])))).replace("\\", "/"),
            program_manifest_sha256=manifest_sha,
            macos_bundle_id=distribution["bundle_id"],
            macos_developer_id=distribution["developer_id"],
            macos_hardened_runtime=distribution["hardened_runtime"],
            macos_secure_timestamp=distribution["secure_timestamp"],
            macos_notarization=distribution["notarization"],
            macos_gatekeeper=distribution["gatekeeper"],
            apply_certified=True,
            apply_blocker=None,
            certification_checked_at=_utc_now(),
        )
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
        job = cls._arm_job(job, artifact)
        UpdateEngine.require_certified_apply(job_id)
        job_dir = UpdateEngine._job_dir(job_id)
        rescue_app = (job_dir / str(job["rescue_app_filename"])).resolve()
        rescue_executable = rescue_app / MACOS_EXECUTABLE_REL
        job["status"] = "scheduled"
        job["scheduled_at"] = _utc_now()
        job["updated_at"] = job["scheduled_at"]
        UpdateEngine._write_job(job)
        try:
            cls._launch_detached_worker(rescue_executable, job_dir / "job.json", os.getpid())
        except Exception as exc:
            job["status"] = "prepared"
            job["apply_certified"] = False
            job["apply_blocker"] = "UPDATE_MACOS_WORKER_LAUNCH_FAILED"
            job["updated_at"] = _utc_now()
            UpdateEngine._write_job(job)
            raise UpdatePreparationError("UPDATE_MACOS_WORKER_LAUNCH_FAILED") from exc
        cls._schedule_parent_exit()
        from backend.services.update_apply import UpdateApplyService
        return UpdateApplyService.public_job(job)

    @staticmethod
    def _launch_detached_worker(executable: Path, job_path: Path, parent_pid: int) -> None:
        if not executable.is_file():
            raise UpdatePreparationError("UPDATE_MACOS_RESCUE_EXECUTABLE_MISSING")
        subprocess.Popen(
            [str(executable), "--macos-update-worker", str(job_path), "--parent-pid", str(parent_pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "DIGITALCROWN_RESTORE_RESTART": "1"},
            **get_platform_adapter().detached_process_kwargs(),
        )

    @classmethod
    def _schedule_parent_exit(cls) -> None:
        threading.Thread(target=cls._terminate_parent_after_response, daemon=True).start()

    @staticmethod
    def _terminate_parent_after_response() -> None:
        time.sleep(0.8)
        os._exit(0)
