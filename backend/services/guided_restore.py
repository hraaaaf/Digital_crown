from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService
from backend.services.guided_restore_archive import (
    _decrypt_backup_key, _inspect_encrypted_media, _safe_job_id, _sha256,
    _validate_database_file, _validate_zip_infos,
)

FORMAT_VERSION = 1
CONFIRMATION_TOKEN = "RESTAURER"
MAX_UPLOAD_BYTES = int(os.environ.get("GUIDED_RESTORE_MAX_BYTES", str(8 * 1024**3)))
RESTORE_ROOT_NAME = "guided-restore"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class GuidedRestoreService:
    @staticmethod
    def root() -> Path:
        root = AppPaths.get_user_data_dir() / RESTORE_ROOT_NAME
        root.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def job_dir(cls, restore_id: str) -> Path:
        return cls.root() / _safe_job_id(restore_id)

    @classmethod
    def _job_path(cls, restore_id: str) -> Path:
        return cls.job_dir(restore_id) / "job.json"

    @classmethod
    def _write_job(cls, job: dict[str, Any]) -> None:
        restore_id = _safe_job_id(str(job["restore_id"]))
        directory = cls.job_dir(restore_id)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "job.json"
        temp = directory / f".job-{uuid.uuid4().hex}.tmp"
        temp.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, target)

    @classmethod
    def get_job(cls, restore_id: str) -> dict[str, Any]:
        path = cls._job_path(restore_id)
        if not path.exists():
            raise FileNotFoundError("Restauration introuvable")
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    async def preflight_upload(cls, upload) -> dict[str, Any]:
        restore_id = uuid.uuid4().hex
        directory = cls.job_dir(restore_id)
        directory.mkdir(parents=True, exist_ok=False)
        source = directory / "source.upload"
        size = 0
        try:
            with source.open("wb") as target:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise ValueError("Sauvegarde trop volumineuse")
                    target.write(chunk)
            if size <= 0:
                raise ValueError("Fichier de sauvegarde vide")
            result = cls.preflight_file(
                source,
                original_name=Path(getattr(upload, "filename", "backup") or "backup").name,
                restore_id=restore_id,
            )
            return result
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise
        finally:
            try:
                await upload.close()
            except Exception:
                pass

    @classmethod
    def preflight_file(
        cls,
        source: Path,
        *,
        original_name: str,
        restore_id: str | None = None,
        active_engine: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        restore_id = _safe_job_id(restore_id or uuid.uuid4().hex)
        directory = cls.job_dir(restore_id)
        directory.mkdir(parents=True, exist_ok=True)
        stored_source = directory / "source.upload"
        if source.resolve() != stored_source.resolve():
            shutil.copy2(source, stored_source)
        source = stored_source

        detected_runtime_engine = active_engine is None
        if active_engine is None:
            active_engine = BackupService._detect_engine()
        dialect, driver = active_engine
        warnings: list[str] = []
        errors: list[str] = []
        created_at: str | None = None
        archive_type = "Sauvegarde base de données"
        db_source = directory / "database.enc"
        media_source: Path | None = None
        media_file_count = 0
        format_name = "legacy-db"
        manifest: dict[str, Any] = {}

        if zipfile.is_zipfile(source):
            archive_type = "Archive complète manifestée"
            format_name = "manifest-archive"
            with zipfile.ZipFile(source, "r") as archive:
                infos = archive.infolist()
                _validate_zip_infos(infos)
                names = [info.filename for info in infos if not info.is_dir()]
                manifest_names = [
                    name for name in names
                    if PurePosixPath(name).name == "manifest.json"
                    or PurePosixPath(name).name.startswith("manifest_") and PurePosixPath(name).suffix == ".json"
                ]
                if len(manifest_names) != 1:
                    raise ValueError("Archive non reconnue : manifeste unique requis")
                manifest = json.loads(archive.read(manifest_names[0]).decode("utf-8"))
                created_at = manifest.get("completed_at") or manifest.get("created_at") or manifest.get("started_at")

                if manifest.get("format") == "digital-crown-guided-restore":
                    if int(manifest.get("version", 0)) != FORMAT_VERSION:
                        errors.append("Version d'archive incompatible")
                    database = manifest.get("database") or {}
                    media = manifest.get("media") or {}
                    db_name = str(database.get("filename") or "")
                    db_checksum = str(database.get("sha256") or "")
                    db_encryption = str(database.get("encryption") or "backup_key")
                    media_name = str(media.get("filename") or "") if media.get("included") else ""
                    media_checksum = str(media.get("sha256") or "") if media_name else ""
                    media_encryption = str(media.get("encryption") or "master_key") if media_name else None
                    manifest_engine = str(database.get("engine") or "sqlite")
                else:
                    db_name = str(manifest.get("db_backup_filename") or "")
                    db_checksum = str(manifest.get("db_checksum") or "")
                    db_encryption = "master_key" if db_name.endswith(".sql.enc") else "backup_key"
                    media_name = str(manifest.get("media_backup_filename") or "")
                    media_checksum = str(manifest.get("media_checksum") or "")
                    media_encryption = "master_key" if media_name else None
                    manifest_engine = "postgresql" if db_name.endswith(".sql.enc") else "sqlite"
                    if manifest.get("overall_status") not in (None, "SUCCESS"):
                        errors.append("Le manifeste indique une sauvegarde incomplète")

                member_by_basename = {PurePosixPath(name).name: name for name in names}
                if not db_name or PurePosixPath(db_name).name not in member_by_basename:
                    raise ValueError("Archive non reconnue : sauvegarde DB absente")
                with archive.open(member_by_basename[PurePosixPath(db_name).name]) as src, db_source.open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
                if db_checksum and _sha256(db_source) != db_checksum:
                    raise ValueError("Checksum base de données invalide")

                if media_name:
                    media_member = member_by_basename.get(PurePosixPath(media_name).name)
                    if not media_member:
                        raise ValueError("Archive non reconnue : sauvegarde média absente")
                    media_source = directory / "media.enc"
                    with archive.open(media_member) as src, media_source.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                    if media_checksum and _sha256(media_source) != media_checksum:
                        raise ValueError("Checksum médias invalide")
                else:
                    warnings.append("Aucun média dans le manifeste : les médias actuels seront préservés")
        else:
            shutil.copy2(source, db_source)
            db_encryption = "backup_key"
            media_encryption = None
            manifest_engine = "sqlite" if original_name.lower().endswith(".db.enc") else dialect
            warnings.append("Sauvegarde DB seule : les médias actuels seront préservés")

        compatible = dialect == "sqlite" and manifest_engine == "sqlite"
        if not compatible:
            errors.append("Cette version de la restauration guidée applique uniquement les sauvegardes SQLite/SQLCipher du cabinet")

        if compatible:
            decrypted_db = directory / "preflight.db"
            try:
                if db_encryption == "backup_key":
                    _decrypt_backup_key(db_source, decrypted_db)
                else:
                    raise ValueError("Format DB chiffré non supporté pour le runtime cabinet SQLite")
                _validate_database_file(decrypted_db, driver)
            finally:
                if decrypted_db.exists():
                    decrypted_db.unlink()

            if media_source:
                if media_encryption != "master_key":
                    raise ValueError("Format de chiffrement média non supporté")
                media_file_count = _inspect_encrypted_media(media_source)

        target_db_path = None
        if dialect == "sqlite" and detected_runtime_engine:
            try:
                from backend.database import engine as active_engine_obj
                db_value = active_engine_obj.url.database
                if db_value and db_value != ":memory:":
                    target_db_path = str(Path(str(db_value)).resolve())
            except Exception:
                target_db_path = None

        now = _utc_now()
        job: dict[str, Any] = {
            "restore_id": restore_id,
            "status": "preflight_ready" if compatible and not errors else "blocked",
            "created_at": now,
            "updated_at": now,
            "original_name": Path(original_name).name,
            "size_bytes": source.stat().st_size,
            "archive_type": archive_type,
            "format": format_name,
            "format_version": FORMAT_VERSION,
            "backup_created_at": created_at,
            "compatible": bool(compatible and not errors),
            "active_engine": dialect,
            "active_driver": driver,
            "restore_database": True,
            "restore_media": bool(media_source),
            "media_file_count": media_file_count,
            "preserved": [] if media_source else ["Médias actuels"],
            "warnings": warnings,
            "errors": errors,
            "database_encryption": db_encryption,
            "media_encryption": media_encryption,
            "target_db_path": target_db_path,
            "steps": [{"at": now, "state": "preflight", "result": "ok" if compatible and not errors else "blocked"}],
        }
        cls._write_job(job)
        return cls.public_job(job)

    @staticmethod
    def public_job(job: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "restore_id", "status", "created_at", "updated_at", "original_name", "size_bytes",
            "archive_type", "format", "format_version", "backup_created_at", "compatible",
            "restore_database", "restore_media", "media_file_count", "preserved", "warnings", "errors",
            "steps", "rescue_created_at", "smoke_check", "rollback", "message",
        }
        return {key: value for key, value in job.items() if key in allowed}

    @classmethod
    def cancel(cls, restore_id: str) -> None:
        job = cls.get_job(restore_id)
        if job.get("status") in {"scheduled", "applying", "restarting", "rolling_back"}:
            raise RuntimeError("Restauration déjà engagée : annulation impossible")
        shutil.rmtree(cls.job_dir(restore_id), ignore_errors=True)

    @staticmethod
    def runtime_apply_supported() -> bool:
        return bool(getattr(sys, "frozen", False)) and os.environ.get("ENVIRONMENT", "").strip().lower() == "cabinet"

    @classmethod
    def request_apply(cls, restore_id: str, confirmation: str) -> dict[str, Any]:
        if confirmation != CONFIRMATION_TOKEN:
            raise ValueError(f"Confirmation exacte requise : {CONFIRMATION_TOKEN}")
        job = cls.get_job(restore_id)
        if not job.get("compatible") or job.get("status") != "preflight_ready":
            raise ValueError("Préflight valide requis avant restauration")
        if not cls.runtime_apply_supported():
            raise RuntimeError("Apply hors-processus disponible uniquement dans l'exécutable cabinet")

        job["status"] = "scheduled"
        job["updated_at"] = _utc_now()
        job.setdefault("steps", []).append({"at": job["updated_at"], "state": "scheduled", "result": "ok"})
        cls._write_job(job)

        cls._launch_detached_worker(restore_id, os.getpid(), sys.executable)
        threading.Thread(target=cls._terminate_parent_after_response, daemon=True).start()
        return cls.public_job(job)

    @staticmethod
    def _launch_detached_worker(restore_id: str, parent_pid: int, executable: str) -> None:
        creationflags = 0
        kwargs: dict[str, Any] = {"close_fds": True}
        if os.name == "nt":
            creationflags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
            )
            kwargs["creationflags"] = creationflags
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen(
            [executable, "--guided-restore-worker", restore_id, "--parent-pid", str(parent_pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **kwargs,
        )

    @staticmethod
    def _terminate_parent_after_response() -> None:
        time.sleep(0.8)
        os._exit(0)


