from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from backend.core.media_paths import get_media_root
from backend.core.paths import AppPaths
from backend.services.guided_restore import GuidedRestoreService, _utc_now
from backend.services.guided_restore_archive import (
    _decrypt_backup_key,
    _directory_digest,
    _extract_encrypted_media,
    _validate_database_file,
)


class GuidedRestoreWorker:
    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, check=False
            )
            return str(pid) in result.stdout
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @classmethod
    def _wait_parent_exit(cls, pid: int, timeout: float = 20.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not cls._pid_alive(pid):
                return
            time.sleep(0.25)
        raise RuntimeError("Le processus applicatif ne s'est pas arrêté à temps")

    @staticmethod
    def _db_target(job: dict[str, Any]) -> Path:
        configured = str(job.get("target_db_path") or "").strip()
        if configured:
            return Path(configured)
        return AppPaths.get_user_data_dir() / "clinical_vault.db"

    @staticmethod
    def _rescue_database(target: Path, rescue_dir: Path) -> list[str]:
        rescue_dir.mkdir(parents=True, exist_ok=True)
        rescued: list[str] = []
        for suffix in ("", "-wal"):
            source = Path(str(target) + suffix)
            if source.exists():
                destination = rescue_dir / ("clinical_vault.db" + suffix)
                shutil.copy2(source, destination)
                rescued.append(destination.name)
        if not rescued:
            raise RuntimeError("Base active introuvable : secours impossible")
        return rescued

    @staticmethod
    def _verify_database_rescue(rescue_dir: Path, driver: str) -> None:
        source = rescue_dir / "clinical_vault.db"
        if not source.exists():
            raise RuntimeError("Secours DB introuvable")
        _validate_database_file(source, driver)

    @staticmethod
    def _restore_database_from_rescue(target: Path, rescue_dir: Path) -> None:
        for suffix in ("", "-wal", "-shm"):
            current = Path(str(target) + suffix)
            if current.exists():
                current.unlink()
        source = rescue_dir / "clinical_vault.db"
        if not source.exists():
            raise RuntimeError("Secours DB introuvable")
        for suffix in ("", "-wal"):
            candidate = rescue_dir / ("clinical_vault.db" + suffix)
            if candidate.exists():
                shutil.copy2(candidate, Path(str(target) + suffix))

    @staticmethod
    def _apply_database(source_enc: Path, target: Path, driver: str) -> None:
        temp = target.parent / f".guided-restore-{uuid.uuid4().hex}.db"
        try:
            _decrypt_backup_key(source_enc, temp)
            _validate_database_file(temp, driver)
            for suffix in ("-wal", "-shm"):
                stale = Path(str(target) + suffix)
                if stale.exists():
                    stale.unlink()
            os.replace(temp, target)
        finally:
            if temp.exists():
                temp.unlink()

    @staticmethod
    def _apply_media(
        source_enc: Path,
        media_root: Path,
        rescue_media: Path,
        expected_current_digest: dict[str, Any] | None,
    ) -> None:
        prepared = media_root.parent / f".guided-restore-media-{uuid.uuid4().hex}"
        if prepared.exists():
            shutil.rmtree(prepared)
        _extract_encrypted_media(source_enc, prepared)
        if rescue_media.exists():
            shutil.rmtree(rescue_media)
        if media_root.exists():
            if expected_current_digest is not None and _directory_digest(media_root) != expected_current_digest:
                shutil.rmtree(prepared, ignore_errors=True)
                raise RuntimeError("Médias modifiés depuis la préparation : restauration annulée")
            os.replace(media_root, rescue_media)
            if expected_current_digest is not None and _directory_digest(rescue_media) != expected_current_digest:
                os.replace(rescue_media, media_root)
                shutil.rmtree(prepared, ignore_errors=True)
                raise RuntimeError("Secours média non vérifiable : restauration annulée")
        elif expected_current_digest and int(expected_current_digest.get("files", 0)) > 0:
            shutil.rmtree(prepared, ignore_errors=True)
            raise RuntimeError("Médias actuels introuvables depuis la préparation")
        try:
            os.replace(prepared, media_root)
        except Exception:
            if rescue_media.exists() and not media_root.exists():
                os.replace(rescue_media, media_root)
            raise
        finally:
            if prepared.exists():
                shutil.rmtree(prepared, ignore_errors=True)

    @staticmethod
    def _rollback_media(media_root: Path, rescue_media: Path) -> None:
        if not rescue_media.exists():
            return
        failed = media_root.parent / f".guided-restore-failed-media-{uuid.uuid4().hex}"
        if media_root.exists():
            os.replace(media_root, failed)
        os.replace(rescue_media, media_root)
        shutil.rmtree(failed, ignore_errors=True)

    @staticmethod
    def _launch_app(executable: str):
        env = os.environ.copy()
        env["DIGITALCROWN_RESTORE_RESTART"] = "1"
        return subprocess.Popen(
            [executable], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, env=env,
        )

    @staticmethod
    def _smoke_check(timeout: float = 60.0) -> bool:
        port = int(os.environ.get("CABINET_PORT", "8005"))
        deadline = time.monotonic() + timeout
        url = f"http://127.0.0.1:{port}/health"
        while time.monotonic() < deadline:
            try:
                with urlopen(url, timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    if response.status == 200 and payload.get("status") == "ok" and payload.get("db") == "ok":
                        return True
            except Exception:
                pass
            time.sleep(1.0)
        return False

    @classmethod
    def run(cls, restore_id: str, parent_pid: int, executable: str | None = None) -> int:
        executable = executable or sys.executable
        job = GuidedRestoreService.get_job(restore_id)
        job_dir = GuidedRestoreService.job_dir(restore_id)
        rescue_dir = job_dir / "rescue"
        rescue_db = rescue_dir / "db"
        rescue_media = rescue_dir / "media-live"
        target_db = cls._db_target(job)
        media_root = get_media_root()
        relaunched = None

        def update(state: str, result: str = "ok", **extra: Any) -> None:
            job["status"] = state
            job["updated_at"] = _utc_now()
            job.setdefault("steps", []).append({"at": job["updated_at"], "state": state, "result": result})
            job.update(extra)
            GuidedRestoreService._write_job(job)

        try:
            cls._wait_parent_exit(parent_pid)
            GuidedRestoreService._verify_staged_job(job)
            update("applying")

            rescued = cls._rescue_database(target_db, rescue_db)
            driver = str(job.get("active_driver") or "pysqlite")
            cls._verify_database_rescue(rescue_db, driver)
            update(
                "applying",
                rescue_created_at=_utc_now(),
                rescue_database_files=rescued,
                rescue_database_verified=True,
                rescue_media_atomic=bool(job.get("restore_media") and media_root.exists()),
            )

            cls._apply_database(job_dir / "database.enc", target_db, driver)
            if job.get("restore_media"):
                cls._apply_media(
                    job_dir / "media.enc",
                    media_root,
                    rescue_media,
                    job.get("prepared_media_digest"),
                )

            update("restarting")
            relaunched = cls._launch_app(executable)
            if not cls._smoke_check():
                raise RuntimeError("Smoke check post-restauration en échec")

            if rescue_media.exists():
                shutil.rmtree(rescue_media, ignore_errors=True)
            update(
                "success",
                smoke_check="passed",
                rollback="not_needed",
                message="Restauration appliquée et redémarrage vérifié.",
            )
            return 0
        except Exception as exc:
            try:
                if relaunched is not None and relaunched.poll() is None:
                    relaunched.terminate()
                    try:
                        relaunched.wait(timeout=10)
                    except Exception:
                        relaunched.kill()
                update("rolling_back", result="warning", message=str(exc))
                if rescue_db.exists():
                    cls._restore_database_from_rescue(target_db, rescue_db)
                if job.get("restore_media"):
                    cls._rollback_media(media_root, rescue_media)
                rollback_process = cls._launch_app(executable)
                rollback_ok = cls._smoke_check()
                update(
                    "rolled_back" if rollback_ok else "rollback_failed",
                    result="warning" if rollback_ok else "error",
                    smoke_check="failed",
                    rollback="passed" if rollback_ok else "failed",
                    message=(
                        "Restauration annulée automatiquement : état précédent restauré."
                        if rollback_ok else "Restauration et rollback en échec : intervention locale requise."
                    ),
                )
                if not rollback_ok and rollback_process.poll() is None:
                    rollback_process.terminate()
                return 2 if rollback_ok else 3
            except Exception as rollback_exc:
                update(
                    "rollback_failed",
                    result="error",
                    smoke_check="failed",
                    rollback="failed",
                    message=f"Échec restauration puis rollback ({type(rollback_exc).__name__}).",
                )
                return 3


guided_restore_service = GuidedRestoreService()
