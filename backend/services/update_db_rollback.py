import hashlib
import json
import os
import re
import shutil
import uuid
from pathlib import Path, PurePosixPath

from cryptography.fernet import Fernet, InvalidToken

from backend.core.paths import AppPaths
from backend.services.backup_service import BackupService


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
JOB_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class UpdateDatabaseRollbackError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict) -> None:
    tmp = path.with_name(path.name + ".partial")
    data = json.dumps(payload, indent=2, sort_keys=True)
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _copy_verified(source: Path, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = _sha256_file(source)
    shutil.copy2(source, target)
    if _sha256_file(target) != digest:
        target.unlink(missing_ok=True)
        raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_QUARANTINE_VERIFY_FAILED")
    return digest


class UpdateDatabaseRollback:
    """Last-resort P10 SQLite rescue, executed by the restored old package."""

    @classmethod
    def _load_job(cls, job_path: Path) -> tuple[Path, Path, dict, Path]:
        user_data = AppPaths.get_user_data_dir().resolve()
        jobs_root = (user_data / "updates" / "jobs").resolve()
        resolved = Path(job_path).resolve()
        if not resolved.is_file() or resolved.name != "job.json":
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_JOB_MISSING")
        if resolved.parent.parent != jobs_root:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_JOB_PATH_INVALID")
        try:
            job = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_JOB_INVALID") from exc
        if int(job.get("schema") or 0) != 1:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_JOB_SCHEMA_INVALID")
        job_id = str(job.get("job_id") or "")
        if not JOB_ID_PATTERN.fullmatch(job_id) or resolved.parent.name != job_id:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_JOB_ID_INVALID")
        return resolved, resolved.parent, job, user_data

    @classmethod
    def _require_authorized_rollback_state(cls, job: dict) -> None:
        if (
            str(job.get("platform") or "").lower() != "windows"
            or str(job.get("worker_contract") or "") != "windows-inno-v1"
            or job.get("apply_certified") is not True
            or str(job.get("status") or "") != "database_rolling_back"
            or str(job.get("worker_result") or "") != "rollback_failed"
            or str(job.get("rollback") or "") != "failed"
            or str(job.get("rollback_failure_reason") or "")
            != "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
            or str(job.get("database_rollback") or "") != "running"
        ):
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_NOT_AUTHORIZED")

    @classmethod
    def _resolve_rescue(cls, job_dir: Path, job: dict) -> Path:
        raw = str(job.get("rescue_backup_filename") or "").replace("\\", "/")
        relative = PurePosixPath(raw)
        if (
            not raw
            or relative.is_absolute()
            or any(part in ("", ".", "..") for part in relative.parts)
            or len(relative.parts) != 2
            or relative.parts[0] != "rescue"
            or not relative.name.endswith(".db.enc")
        ):
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_RESCUE_PATH_INVALID")
        rescue = job_dir.joinpath(*relative.parts).resolve()
        rescue_root = (job_dir / "rescue").resolve()
        if not rescue.is_relative_to(rescue_root) or not rescue.is_file():
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_RESCUE_MISSING")
        expected = str(job.get("rescue_backup_sha256") or "").strip().lower()
        if not SHA256_PATTERN.fullmatch(expected) or _sha256_file(rescue) != expected:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_RESCUE_SHA256_MISMATCH")
        return rescue

    @classmethod
    def _require_local_sqlite(cls) -> None:
        database_url = os.getenv("DATABASE_URL", "").strip().lower()
        if database_url and not database_url.startswith("sqlite"):
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_POSTGRES_UNSUPPORTED")

    @classmethod
    def _existing_backup_cipher(cls, user_data: Path) -> Fernet:
        key_path = user_data / "backup.key"
        if not key_path.is_file():
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_BACKUP_KEY_MISSING")
        try:
            key = key_path.read_bytes()
            if not key:
                raise ValueError("empty key")
            return Fernet(key)
        except Exception as exc:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_BACKUP_KEY_INVALID") from exc

    @classmethod
    def _sqlcipher_passphrase(cls) -> str:
        value = os.getenv("CABINET_MASTER_KEY_HEX") or os.getenv("SECRET_KEY")
        if not value:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_SQLCIPHER_KEY_MISSING")
        return value

    @classmethod
    def _restore_original_after_failure(
        cls,
        target: Path,
        quarantine: dict[str, Path],
        original_existed: bool,
    ) -> None:
        target.unlink(missing_ok=True)
        Path(str(target) + "-wal").unlink(missing_ok=True)
        Path(str(target) + "-shm").unlink(missing_ok=True)
        if original_existed:
            original = quarantine.get("database")
            if not original or not original.is_file():
                raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_ORIGINAL_RESTORE_MISSING")
            original_sha = _sha256_file(original)
            shutil.copy2(original, target)
            if _sha256_file(target) != original_sha:
                raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_ORIGINAL_RESTORE_VERIFY_FAILED")
        for suffix, key in (("-wal", "wal"), ("-shm", "shm")):
            source = quarantine.get(key)
            if source and source.is_file():
                destination = Path(str(target) + suffix)
                source_sha = _sha256_file(source)
                shutil.copy2(source, destination)
                if _sha256_file(destination) != source_sha:
                    raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_ORIGINAL_RESTORE_VERIFY_FAILED")

    @classmethod
    def execute(cls, job_path: Path) -> dict:
        resolved_job, job_dir, job, user_data = cls._load_job(job_path)
        cls._require_authorized_rollback_state(job)
        cls._require_local_sqlite()
        rescue = cls._resolve_rescue(job_dir, job)
        target = (user_data / "clinical_vault.db").resolve()
        if target.parent != user_data:
            raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_TARGET_INVALID")

        cipher = cls._existing_backup_cipher(user_data)
        passphrase = cls._sqlcipher_passphrase()
        temp = user_data / f".p10-db-rollback-{uuid.uuid4().hex}.db"
        quarantine_root = job_dir / "rescue" / "pre-db-rollback"
        quarantine_root.mkdir(parents=True, exist_ok=True)
        quarantine: dict[str, Path] = {}
        original_existed = target.is_file()
        replaced = False

        try:
            try:
                decrypted = cipher.decrypt(rescue.read_bytes())
            except InvalidToken as exc:
                raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_DECRYPT_FAILED") from exc
            if not decrypted:
                raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_DECRYPT_EMPTY")
            with temp.open("wb") as handle:
                handle.write(decrypted)
                handle.flush()
                os.fsync(handle.fileno())
            BackupService._verify_sqlcipher_file(temp, passphrase)

            sources = (
                ("database", target),
                ("wal", Path(str(target) + "-wal")),
                ("shm", Path(str(target) + "-shm")),
            )
            quarantine_hashes: dict[str, str] = {}
            for label, source in sources:
                if source.is_file():
                    destination = quarantine_root / source.name
                    quarantine[label] = destination
                    quarantine_hashes[label] = _copy_verified(source, destination)

            Path(str(target) + "-wal").unlink(missing_ok=True)
            Path(str(target) + "-shm").unlink(missing_ok=True)
            os.replace(temp, target)
            replaced = True
            try:
                BackupService._verify_sqlcipher_file(target, passphrase)
            except Exception as exc:
                cls._restore_original_after_failure(target, quarantine, original_existed)
                replaced = False
                if original_existed:
                    try:
                        BackupService._verify_sqlcipher_file(target, passphrase)
                    except Exception as original_exc:
                        raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_ORIGINAL_RESTORE_INVALID") from original_exc
                raise UpdateDatabaseRollbackError("UPDATE_DB_ROLLBACK_RESTORED_DB_INVALID") from exc

            report = {
                "schema": 1,
                "status": "success",
                "job_id": str(job["job_id"]),
                "rescue_sha256": _sha256_file(rescue),
                "restored_db_sha256": _sha256_file(target),
                "quarantine_sha256": quarantine_hashes,
            }
            _atomic_json(job_dir / "db-rollback-report.json", report)
            return report
        finally:
            temp.unlink(missing_ok=True)
            if replaced:
                Path(str(target) + "-wal").unlink(missing_ok=True)
                Path(str(target) + "-shm").unlink(missing_ok=True)

    @classmethod
    def run(cls, job_path: Path) -> int:
        try:
            cls.execute(job_path)
            return 0
        except UpdateDatabaseRollbackError as exc:
            try:
                resolved = Path(job_path).resolve()
                user_data = AppPaths.get_user_data_dir().resolve()
                if resolved.parent.parent == (user_data / "updates" / "jobs").resolve():
                    _atomic_json(
                        resolved.parent / "db-rollback-report.json",
                        {"schema": 1, "status": "failed", "error_code": exc.code},
                    )
            except Exception:
                pass
            return 4
        except Exception:
            try:
                resolved = Path(job_path).resolve()
                user_data = AppPaths.get_user_data_dir().resolve()
                if resolved.parent.parent == (user_data / "updates" / "jobs").resolve():
                    _atomic_json(
                        resolved.parent / "db-rollback-report.json",
                        {"schema": 1, "status": "failed", "error_code": "UPDATE_DB_ROLLBACK_INTERNAL_ERROR"},
                    )
            except Exception:
                pass
            return 4
