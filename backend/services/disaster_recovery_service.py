from __future__ import annotations

import errno
import hashlib
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.core.paths import AppPaths
from backend.core.platform import get_platform_adapter
from backend.services.backup_service import BackupService
from backend.services.cabinet_bundle import CabinetBundleService

logger = logging.getLogger(__name__)

DR_DESTINATION_ENV = "DIGITALCROWN_DR_DESTINATION"
DR_SECRET_ENV = "DIGITALCROWN_DR_SECRET"
DR_KEEP_ENV = "DIGITALCROWN_DR_KEEP"
DEFAULT_KEEP = 14
MAX_KEEP = 90
BUNDLE_PREFIX = "digital-crown-dr-"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DisasterRecoveryService:
    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _persist_status(status: dict) -> None:
        status_path = AppPaths.get_user_data_dir() / "backups" / "last_dr_status.json"
        try:
            get_platform_adapter().atomic_write_text(
                status_path,
                json.dumps(status, indent=2, sort_keys=True),
            )
        except Exception as exc:
            logger.warning("Impossible d'écrire le statut DR : %s", type(exc).__name__)

    @staticmethod
    def _is_within(path: Path, parent: Path) -> bool:
        try:
            path.resolve(strict=False).relative_to(parent.resolve(strict=False))
            return True
        except ValueError:
            return False

    @staticmethod
    def _configured_keep() -> int:
        raw = os.getenv(DR_KEEP_ENV, str(DEFAULT_KEEP)).strip()
        try:
            keep = int(raw)
        except ValueError as exc:
            raise ValueError(f"{DR_KEEP_ENV} doit être un entier") from exc
        if not 1 <= keep <= MAX_KEEP:
            raise ValueError(f"{DR_KEEP_ENV} doit être compris entre 1 et {MAX_KEEP}")
        return keep

    @staticmethod
    def _configuration() -> tuple[Path, str, int]:
        raw_destination = os.getenv(DR_DESTINATION_ENV, "").strip()
        secret = os.getenv(DR_SECRET_ENV, "").strip()
        if not raw_destination or not secret:
            raise RuntimeError("DR_CONFIGURATION_REQUIRED")

        destination = Path(raw_destination).expanduser()
        if not destination.is_absolute():
            raise ValueError(f"{DR_DESTINATION_ENV} doit être un chemin absolu")
        if len(secret.encode("utf-8")) < 16:
            raise ValueError(f"{DR_SECRET_ENV} doit contenir au moins 16 octets")

        user_data = AppPaths.get_user_data_dir().resolve(strict=False)
        destination = destination.resolve(strict=False)
        if DisasterRecoveryService._is_within(destination, user_data):
            raise ValueError("La destination DR doit être hors du répertoire local Digital Crown")

        get_platform_adapter().ensure_private_directory(destination)
        destination = destination.resolve()
        if DisasterRecoveryService._is_within(destination, user_data):
            raise ValueError("La destination DR doit être hors du répertoire local Digital Crown")

        probe = destination / f".digitalcrown-dr-probe-{uuid.uuid4().hex}"
        try:
            probe.write_bytes(b"DigitalCrown DR probe")
            if probe.read_bytes() != b"DigitalCrown DR probe":
                raise OSError("Destination DR illisible après écriture")
        finally:
            probe.unlink(missing_ok=True)
        return destination, secret, DisasterRecoveryService._configured_keep()

    @staticmethod
    def _sidecar_path(bundle: Path) -> Path:
        return bundle.with_name(bundle.name + ".sha256")

    @staticmethod
    def _write_checksum_sidecar(bundle: Path, sha256: str) -> Path:
        sidecar = DisasterRecoveryService._sidecar_path(bundle)
        get_platform_adapter().atomic_write_text(sidecar, f"{sha256}  {bundle.name}\n")
        expected = f"{sha256}  {bundle.name}\n"
        if sidecar.read_text(encoding="utf-8") != expected:
            raise RuntimeError("Sidecar SHA-256 DR illisible après écriture")
        return sidecar

    @staticmethod
    def _is_verified_pair(bundle: Path) -> bool:
        sidecar = DisasterRecoveryService._sidecar_path(bundle)
        if not bundle.is_file() or not sidecar.is_file():
            return False
        try:
            raw = sidecar.read_text(encoding="utf-8")
        except OSError:
            return False
        expected_suffix = f"  {bundle.name}\n"
        if not raw.endswith(expected_suffix):
            return False
        digest = raw[: -len(expected_suffix)]
        return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest.lower())

    @staticmethod
    def _cleanup_verified_bundles(destination: Path, keep: int) -> list[str]:
        bundles = sorted(
            (
                path
                for path in destination.glob(f"{BUNDLE_PREFIX}*.dcbundle")
                if DisasterRecoveryService._is_verified_pair(path)
            ),
            key=lambda path: (path.stat().st_mtime_ns, path.name),
            reverse=True,
        )
        removed: list[str] = []
        for old in bundles[keep:]:
            old.unlink(missing_ok=True)
            DisasterRecoveryService._sidecar_path(old).unlink(missing_ok=True)
            removed.append(old.name)
        return removed

    @staticmethod
    def _configuration_failure(started_at: str, exc: Exception) -> dict:
        if isinstance(exc, RuntimeError) and str(exc) == "DR_CONFIGURATION_REQUIRED":
            return {
                "status": "CONFIGURATION_REQUIRED",
                "started_at": started_at,
                "completed_at": DisasterRecoveryService._utc_now(),
                "destination_configured": False,
                "bundle_filename": None,
                "sha256": None,
                "verified_restore_path": False,
                "error_code": "DR_CONFIGURATION_REQUIRED",
            }
        if isinstance(exc, ValueError):
            code = "DR_CONFIGURATION_INVALID"
        elif isinstance(exc, OSError) and getattr(exc, "errno", None) == errno.ENOSPC:
            code = "DR_DISK_FULL"
        elif isinstance(exc, OSError):
            code = "DR_DESTINATION_UNAVAILABLE"
        else:
            code = "DR_CONFIGURATION_FAILED"
        return {
            "status": "FAILED",
            "started_at": started_at,
            "completed_at": DisasterRecoveryService._utc_now(),
            "destination_configured": False,
            "bundle_filename": None,
            "sha256": None,
            "verified_restore_path": False,
            "error_code": code,
        }

    @staticmethod
    def create_verified_snapshot() -> dict:
        started_at = DisasterRecoveryService._utc_now()
        try:
            destination, secret, keep = DisasterRecoveryService._configuration()
        except Exception as exc:
            status = DisasterRecoveryService._configuration_failure(started_at, exc)
            DisasterRecoveryService._persist_status(status)
            if status["status"] == "FAILED":
                logger.error("DR configuration refused: %s", status["error_code"])
            return status

        final_target = destination / (
            f"{BUNDLE_PREFIX}{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-"
            f"{uuid.uuid4().hex[:8]}.dcbundle"
        )
        working_target = final_target.with_name(final_target.name + ".partial")
        sidecar = DisasterRecoveryService._sidecar_path(final_target)

        try:
            active_engine = BackupService._detect_engine()
            if active_engine[0] != "sqlite":
                raise RuntimeError("DR_PORTABLE_ENGINE_UNSUPPORTED")

            exported = CabinetBundleService.create_bundle(working_target, secret)
            if not working_target.exists() or working_target.stat().st_size <= 0:
                raise RuntimeError("DR bundle absent ou vide après export")

            sha256 = _sha256(working_target)
            if sha256 != str(exported.get("sha256") or ""):
                raise RuntimeError("DR bundle checksum incohérent après export")

            with tempfile.TemporaryDirectory(prefix="digitalcrown-dr-verify-") as temp_name:
                verify_archive = Path(temp_name) / "guided-restore.zip"
                verified = CabinetBundleService.to_local_guided_restore_archive(
                    working_target,
                    secret,
                    verify_archive,
                    active_engine=active_engine,
                )
                if not verify_archive.exists() or verify_archive.stat().st_size <= 0:
                    raise RuntimeError("DR verification archive absente ou vide")
                if not isinstance(verified, dict):
                    raise RuntimeError("DR verification result invalide")

            os.replace(working_target, final_target)
            DisasterRecoveryService._write_checksum_sidecar(final_target, sha256)
            removed = DisasterRecoveryService._cleanup_verified_bundles(destination, keep)
            status = {
                "status": "SUCCESS",
                "started_at": started_at,
                "completed_at": DisasterRecoveryService._utc_now(),
                "destination_configured": True,
                "bundle_filename": final_target.name,
                "size_bytes": final_target.stat().st_size,
                "sha256": sha256,
                "checksum_sidecar": sidecar.name,
                "verified_restore_path": True,
                "retention_keep": keep,
                "retention_removed": removed,
                "source_os": exported.get("source_os"),
                "source_architecture": exported.get("source_architecture"),
                "media_file_count": int(exported.get("media_file_count") or 0),
            }
            DisasterRecoveryService._persist_status(status)
            logger.info("DR snapshot vérifié créé : %s", final_target.name)
            return status
        except Exception as exc:
            working_target.unlink(missing_ok=True)
            final_target.unlink(missing_ok=True)
            sidecar.unlink(missing_ok=True)
            if isinstance(exc, OSError) and getattr(exc, "errno", None) == errno.ENOSPC:
                error_code = "DR_DISK_FULL"
            elif isinstance(exc, RuntimeError) and str(exc) == "DR_PORTABLE_ENGINE_UNSUPPORTED":
                error_code = "DR_PORTABLE_ENGINE_UNSUPPORTED"
            else:
                error_code = type(exc).__name__
            status = {
                "status": "FAILED",
                "started_at": started_at,
                "completed_at": DisasterRecoveryService._utc_now(),
                "destination_configured": True,
                "bundle_filename": None,
                "sha256": None,
                "verified_restore_path": False,
                "error_code": error_code,
            }
            DisasterRecoveryService._persist_status(status)
            logger.error("DR snapshot refusé : %s", error_code)
            return status

    @staticmethod
    def run_scheduled_snapshot() -> bool:
        try:
            return DisasterRecoveryService.create_verified_snapshot().get("status") in {
                "SUCCESS",
                "CONFIGURATION_REQUIRED",
            }
        except Exception as exc:
            logger.error("DR scheduler error : %s", type(exc).__name__)
            return False


disaster_recovery_service = DisasterRecoveryService()
