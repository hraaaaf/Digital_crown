import hashlib
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet

from backend.core.paths import AppPaths

logger = logging.getLogger(__name__)


class BackupService:
    @staticmethod
    def _get_or_create_key() -> Fernet:
        data_dir = AppPaths.get_user_data_dir()
        key_path = data_dir / "backup.key"
        if not key_path.exists():
            key = Fernet.generate_key()
            key_path.write_bytes(key)
            logger.info("Nouvelle clé de chiffrement générée pour les backups.")
        else:
            key = key_path.read_bytes()
        return Fernet(key)

    @staticmethod
    def _encrypt_and_save(source_db: Path, target_enc: Path, cipher_suite: Fernet):
        temp_db = target_enc.with_suffix(".temp.db")
        try:
            if source_db.suffix == ".db":
                src_conn = None
                dst_conn = None
                try:
                    src_conn = sqlite3.connect(str(source_db))
                    dst_conn = sqlite3.connect(str(temp_db))
                    src_conn.backup(dst_conn)
                finally:
                    if dst_conn:
                        dst_conn.close()
                    if src_conn:
                        src_conn.close()
            else:
                shutil.copy2(source_db, temp_db)

            target_enc.write_bytes(cipher_suite.encrypt(temp_db.read_bytes()))
        finally:
            if temp_db.exists():
                temp_db.unlink()

    @staticmethod
    def _encrypt_file_atomic(source: Path, target: Path, cipher_suite: Fernet) -> None:
        """Encrypt *source* into *target* atomically, never exposing a partial backup."""
        temp_target = target.parent / f".tmp_{uuid.uuid4().hex}_{target.name}"
        try:
            encrypted = cipher_suite.encrypt(source.read_bytes())
            if not encrypted:
                raise RuntimeError("empty encrypted output")
            temp_target.write_bytes(encrypted)
            if temp_target.stat().st_size == 0:
                raise RuntimeError("empty temporary backup")
            os.replace(temp_target, target)
        finally:
            if temp_target.exists():
                temp_target.unlink()

    @staticmethod
    def _detect_engine() -> tuple[str, str]:
        from backend.database import engine as active_engine
        return active_engine.dialect.name, active_engine.driver

    @staticmethod
    def _backup_postgres(backups_dir: Path, timestamp: str) -> dict:
        from backend.config import settings
        from backend.scripts.backup_db import find_pg_binary, _parse_postgres_url, get_cipher

        status = {
            "engine": "postgresql", "status": "FAILED", "backup_filename": None,
            "size_bytes": 0, "checksum": None, "error_code": None, "error_message": None,
        }
        try:
            user, password, host, port, dbname = _parse_postgres_url(settings.DATABASE_URL)
        except Exception as exc:
            status.update(error_code="URL_PARSE_ERROR", error_message="Impossible d'interpréter DATABASE_URL")
            logger.error("Backup Postgres : échec parsing DATABASE_URL (%s).", type(exc).__name__)
            return status

        env = os.environ.copy()
        env["PGPASSWORD"] = password
        cmd = [find_pg_binary("pg_dump"), "-U", user, "-h", host]
        if port:
            cmd += ["-p", port]
        cmd += ["-d", dbname, "-F", "p", "--clean"]

        try:
            process = subprocess.run(cmd, env=env, capture_output=True, check=False)
        except FileNotFoundError:
            status.update(error_code="PG_DUMP_NOT_FOUND", error_message="pg_dump introuvable sur ce système")
            return status
        if process.returncode != 0:
            status.update(error_code="PG_DUMP_FAILED", error_message=f"pg_dump a échoué (code {process.returncode})")
            return status
        if not process.stdout:
            status.update(error_code="EMPTY_DUMP", error_message="pg_dump a produit une sortie vide")
            return status

        try:
            cipher = get_cipher()
            encrypted_data = cipher.encrypt(process.stdout)
        except SystemExit:
            status.update(error_code="MISSING_MASTER_KEY", error_message="CABINET_MASTER_KEY_HEX manquant")
            return status
        except Exception as exc:
            status.update(error_code="ENCRYPTION_FAILED", error_message="Échec du chiffrement")
            logger.error("Backup Postgres : échec chiffrement (%s).", type(exc).__name__)
            return status
        if not encrypted_data:
            status.update(error_code="EMPTY_ENCRYPTED_OUTPUT", error_message="Sortie chiffrée vide")
            return status

        final_name = f"db_backup_{timestamp}.sql.enc"
        final_path = backups_dir / final_name
        temp_path = backups_dir / f".tmp_{uuid.uuid4().hex}_{final_name}"
        try:
            temp_path.write_bytes(encrypted_data)
            if temp_path.stat().st_size == 0:
                raise RuntimeError("temp backup file is empty")
            os.replace(temp_path, final_path)
        except Exception as exc:
            status.update(error_code="WRITE_FAILED", error_message="Échec écriture du fichier de backup")
            logger.error("Backup Postgres : échec écriture (%s).", type(exc).__name__)
            return status
        finally:
            if temp_path.exists():
                temp_path.unlink()

        status.update(
            status="SUCCESS",
            backup_filename=final_name,
            size_bytes=final_path.stat().st_size,
            checksum=hashlib.sha256(final_path.read_bytes()).hexdigest(),
        )
        return status

    @staticmethod
    def _sqlcipher_passphrase(active_engine) -> str:
        """Return the already-resolved SQLCipher key without inventing a fallback."""
        password = getattr(active_engine.url, "password", None)
        if password:
            return str(password)
        configured = os.getenv("CABINET_MASTER_KEY_HEX") or os.getenv("SECRET_KEY")
        if configured:
            return configured
        raise RuntimeError("SQLCipher key unavailable")

    @staticmethod
    def _verify_sqlcipher_file(db_path: Path, passphrase: str) -> None:
        """Open a SQLCipher DB with its key and require PRAGMA integrity_check=ok."""
        try:
            from sqlcipher3 import dbapi2 as sqlcipher
        except ImportError as exc:
            raise RuntimeError("sqlcipher3 unavailable") from exc

        conn = sqlcipher.connect(str(db_path))
        try:
            safe_key = passphrase.replace("'", "''")
            conn.execute(f"PRAGMA key = '{safe_key}'")
            row = conn.execute("PRAGMA integrity_check").fetchone()
            if not row or str(row[0]).lower() != "ok":
                raise RuntimeError("SQLCipher integrity_check failed")
        finally:
            conn.close()

    @staticmethod
    def _export_sqlcipher_snapshot(source_db: Path, snapshot_db: Path, passphrase: str) -> None:
        """Create a consistent encrypted SQLCipher snapshot using sqlcipher_export."""
        try:
            from sqlcipher3 import dbapi2 as sqlcipher
        except ImportError as exc:
            raise RuntimeError("sqlcipher3 unavailable") from exc

        if snapshot_db.exists():
            snapshot_db.unlink()
        source = sqlcipher.connect(str(source_db))
        attached = False
        try:
            safe_key = passphrase.replace("'", "''")
            safe_target = str(snapshot_db).replace("'", "''")
            source.execute(f"PRAGMA key = '{safe_key}'")
            # Force key validation before exporting. A wrong key must fail here.
            source.execute("SELECT count(*) FROM sqlite_master").fetchone()
            source.execute(f"ATTACH DATABASE '{safe_target}' AS backup KEY '{safe_key}'")
            attached = True
            source.execute("SELECT sqlcipher_export('backup')")
            source.commit()
            source.execute("DETACH DATABASE backup")
            attached = False
        finally:
            if attached:
                try:
                    source.execute("DETACH DATABASE backup")
                except Exception:
                    pass
            source.close()

        if not snapshot_db.exists() or snapshot_db.stat().st_size == 0:
            raise RuntimeError("SQLCipher export produced no snapshot")
        BackupService._verify_sqlcipher_file(snapshot_db, passphrase)

    @staticmethod
    def _backup_sqlite_family(backups_dir: Path, timestamp: str, driver: str) -> dict:
        status = {
            "engine": "sqlite", "status": "FAILED", "backup_filename": None,
            "size_bytes": 0, "checksum": None, "error_code": None, "error_message": None,
        }
        try:
            from backend.database import engine as active_engine
            db_path_str = active_engine.url.database
        except Exception as exc:
            status.update(error_code="ENGINE_INTROSPECTION_FAILED", error_message="Impossible de déterminer le fichier SQLite actif")
            logger.error("Backup SQLite : introspection engine échouée (%s).", type(exc).__name__)
            return status

        if not db_path_str or db_path_str == ":memory:":
            status.update(status="SKIPPED_UNSUPPORTED_ENGINE", error_code="IN_MEMORY_DB", error_message="Base SQLite en mémoire, rien à sauvegarder")
            return status
        db_path = Path(db_path_str)
        if not db_path.exists():
            status.update(error_code="SOURCE_NOT_FOUND", error_message="Fichier SQLite introuvable")
            return status

        final_name = f"db_backup_{timestamp}.db.enc"
        final_path = backups_dir / final_name
        cipher = BackupService._get_or_create_key()

        if driver == "pysqlcipher":
            snapshot = backups_dir / f".tmp_{uuid.uuid4().hex}_sqlcipher_snapshot.db"
            try:
                passphrase = BackupService._sqlcipher_passphrase(active_engine)
                BackupService._export_sqlcipher_snapshot(db_path, snapshot, passphrase)
                BackupService._encrypt_file_atomic(snapshot, final_path, cipher)
            except RuntimeError as exc:
                error_text = str(exc)
                error_code = "MISSING_SQLCIPHER_KEY" if "key unavailable" in error_text else "SQLCIPHER_BACKUP_FAILED"
                status.update(error_code=error_code, error_message="Échec de la sauvegarde SQLCipher")
                logger.error("Backup SQLCipher refusé (%s).", type(exc).__name__)
                return status
            except Exception as exc:
                status.update(error_code="SQLCIPHER_BACKUP_FAILED", error_message="Échec de la sauvegarde SQLCipher")
                logger.error("Backup SQLCipher échoué (%s).", type(exc).__name__)
                return status
            finally:
                if snapshot.exists():
                    snapshot.unlink()
        else:
            try:
                BackupService._encrypt_and_save(db_path, final_path, cipher)
            except Exception as exc:
                status.update(error_code="ENCRYPTION_FAILED", error_message="Échec du chiffrement SQLite")
                logger.error("Backup SQLite : échec (%s).", type(exc).__name__)
                return status

        if not final_path.exists() or final_path.stat().st_size == 0:
            status.update(error_code="EMPTY_OUTPUT", error_message="Fichier de backup SQLite vide")
            return status
        status.update(
            status="SUCCESS",
            backup_filename=final_name,
            size_bytes=final_path.stat().st_size,
            checksum=hashlib.sha256(final_path.read_bytes()).hexdigest(),
        )
        return status

    @staticmethod
    def _persist_status(backups_dir: Path, status: dict) -> None:
        try:
            (backups_dir / "last_backup_status.json").write_text(
                json.dumps(status, indent=2, default=str), encoding="utf-8"
            )
        except Exception as exc:
            logger.warning("Impossible d'écrire le statut de backup : %s", type(exc).__name__)

    @staticmethod
    def backup_active_database() -> dict:
        started_at = datetime.utcnow().isoformat() + "Z"
        backups_dir = AppPaths.get_user_data_dir() / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            dialect_name, driver = BackupService._detect_engine()
        except Exception as exc:
            result = {
                "engine": "unknown", "status": "SKIPPED_UNSUPPORTED_ENGINE",
                "backup_filename": None, "size_bytes": 0, "checksum": None,
                "error_code": "ENGINE_DETECTION_FAILED",
                "error_message": "Impossible de déterminer le moteur actif",
            }
            logger.error("Backup automatique : détection moteur échouée (%s).", type(exc).__name__)
            result["started_at"] = started_at
            result["completed_at"] = datetime.utcnow().isoformat() + "Z"
            BackupService._persist_status(backups_dir, result)
            return result

        if dialect_name == "postgresql":
            result = BackupService._backup_postgres(backups_dir, timestamp)
        elif dialect_name == "sqlite":
            result = BackupService._backup_sqlite_family(backups_dir, timestamp, driver)
        else:
            result = {
                "engine": dialect_name, "status": "SKIPPED_UNSUPPORTED_ENGINE",
                "backup_filename": None, "size_bytes": 0, "checksum": None,
                "error_code": "UNSUPPORTED_ENGINE",
                "error_message": f"Moteur non supporté : {dialect_name}",
            }

        result["started_at"] = started_at
        result["completed_at"] = datetime.utcnow().isoformat() + "Z"
        if result["status"] == "SUCCESS":
            BackupService._cleanup_old_backups(backups_dir, prefix="db_backup_", keep=7)
        BackupService._persist_status(backups_dir, result)
        return result

    @staticmethod
    def run_daily_backup():
        try:
            result = BackupService.backup_active_database()
            return result["status"] == "SUCCESS"
        except Exception as exc:
            logger.error("Erreur inattendue lors de la sauvegarde automatique : %s", type(exc).__name__)
            return False

    @staticmethod
    def restore_backup(enc_file: Path, restore_db: Path, *, verify_sqlcipher: bool = False, passphrase: str | None = None):
        """Decrypt a backup to a caller-selected path and optionally verify SQLCipher integrity.

        This never replaces the live DB automatically. The explicit destination keeps restore
        drills safe and testable.
        """
        cipher_suite = BackupService._get_or_create_key()
        if not enc_file.exists():
            raise FileNotFoundError(f"Fichier chiffré introuvable : {enc_file}")
        decrypted_data = cipher_suite.decrypt(enc_file.read_bytes())
        temp_restore = restore_db.parent / f".tmp_{uuid.uuid4().hex}_{restore_db.name}"
        try:
            temp_restore.write_bytes(decrypted_data)
            if verify_sqlcipher:
                if not passphrase:
                    raise RuntimeError("SQLCipher passphrase required for verification")
                BackupService._verify_sqlcipher_file(temp_restore, passphrase)
            os.replace(temp_restore, restore_db)
        finally:
            if temp_restore.exists():
                temp_restore.unlink()
        logger.info("Restauration réussie vers %s", restore_db)

    @staticmethod
    def _cleanup_old_backups(backups_dir: Path, prefix: str, keep: int = 7):
        try:
            backups = sorted(
                backups_dir.glob(f"{prefix}*.enc"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for old_backup in backups[keep:]:
                old_backup.unlink()
        except Exception as exc:
            logger.warning("Erreur lors du nettoyage : %s", type(exc).__name__)


backup_service = BackupService()
