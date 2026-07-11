import os
import shutil
import logging
import sqlite3
import subprocess
import hashlib
import json
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
        temp_db = target_enc.with_suffix('.temp.db')
        try:
            # sqlite3 native backup API is WAL-safe; fallback to shutil for non-DB files
            if source_db.suffix == '.db':
                import sqlite3 as _sqlite3
                src_conn = None
                dst_conn = None
                try:
                    src_conn = _sqlite3.connect(str(source_db))
                    dst_conn = _sqlite3.connect(str(temp_db))
                    src_conn.backup(dst_conn)
                finally:
                    if dst_conn:
                        dst_conn.close()
                    if src_conn:
                        src_conn.close()
            else:
                shutil.copy2(source_db, temp_db)

            data = temp_db.read_bytes()
            encrypted_data = cipher_suite.encrypt(data)
            target_enc.write_bytes(encrypted_data)
        finally:
            if temp_db.exists():
                temp_db.unlink()

    @staticmethod
    def _detect_engine() -> tuple[str, str]:
        """Moteur SQLAlchemy réellement actif (pas une heuristique fichier).

        Réutilise le même pattern que database.py::migrate_appointment_columns()
        (engine.dialect.name). engine.driver distingue en plus pysqlite (SQLite en
        clair) de pysqlcipher (SQLite chiffré SQLCipher) — les deux partagent le
        même dialect.name="sqlite" mais nécessitent des stratégies différentes.
        """
        from backend.database import engine as active_engine
        return active_engine.dialect.name, active_engine.driver

    @staticmethod
    def _backup_postgres(backups_dir: Path, timestamp: str) -> dict:
        """Sauvegarde PostgreSQL via pg_dump — jamais sqlite3, jamais clinical_vault.db.

        Réutilise find_pg_binary/_parse_postgres_url/get_cipher de backup_db.py
        (mécanisme déjà validé manuellement pendant RRIG-1) plutôt que d'en
        récrire une troisième implémentation.
        """
        from backend.config import settings
        from backend.scripts.backup_db import find_pg_binary, _parse_postgres_url, get_cipher

        status = {
            "engine": "postgresql", "status": "FAILED", "backup_filename": None,
            "size_bytes": 0, "checksum": None, "error_code": None, "error_message": None,
        }

        try:
            user, password, host, port, dbname = _parse_postgres_url(settings.DATABASE_URL)
        except Exception as e:
            status["error_code"] = "URL_PARSE_ERROR"
            status["error_message"] = "Impossible d'interpréter DATABASE_URL"
            logger.error("Backup Postgres : échec parsing DATABASE_URL (%s).", type(e).__name__)
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
            status["error_code"] = "PG_DUMP_NOT_FOUND"
            status["error_message"] = "pg_dump introuvable sur ce système"
            logger.error("Backup Postgres : pg_dump introuvable.")
            return status

        if process.returncode != 0:
            status["error_code"] = "PG_DUMP_FAILED"
            status["error_message"] = f"pg_dump a échoué (code {process.returncode})"
            logger.error("Backup Postgres : pg_dump a échoué (code %s).", process.returncode)
            return status

        dump_data = process.stdout
        if not dump_data:
            status["error_code"] = "EMPTY_DUMP"
            status["error_message"] = "pg_dump a produit une sortie vide"
            logger.error("Backup Postgres : dump vide, refusé.")
            return status

        try:
            cipher = get_cipher()
            encrypted_data = cipher.encrypt(dump_data)
        except SystemExit:
            # get_cipher() appelle sys.exit(1) si CABINET_MASTER_KEY_HEX manque —
            # acceptable pour un script CLI, inacceptable dans ce thread serveur
            # long-vivant. Converti en échec propre plutôt que de laisser
            # SystemExit remonter et tuer le thread du scheduler.
            status["error_code"] = "MISSING_MASTER_KEY"
            status["error_message"] = "CABINET_MASTER_KEY_HEX manquant"
            logger.error("Backup Postgres : CABINET_MASTER_KEY_HEX manquant, backup refusé.")
            return status
        except Exception as e:
            status["error_code"] = "ENCRYPTION_FAILED"
            status["error_message"] = "Échec du chiffrement"
            logger.error("Backup Postgres : échec chiffrement (%s).", type(e).__name__)
            return status

        if not encrypted_data:
            status["error_code"] = "EMPTY_ENCRYPTED_OUTPUT"
            status["error_message"] = "Sortie chiffrée vide"
            return status

        final_name = f"db_backup_{timestamp}.sql.enc"
        final_path = backups_dir / final_name
        temp_path = backups_dir / f".tmp_{uuid.uuid4().hex}_{final_name}"
        checksum = hashlib.sha256(encrypted_data).hexdigest()
        try:
            temp_path.write_bytes(encrypted_data)
            if temp_path.stat().st_size == 0:
                raise RuntimeError("temp backup file is empty")
            os.replace(temp_path, final_path)
        except Exception as e:
            status["error_code"] = "WRITE_FAILED"
            status["error_message"] = "Échec écriture du fichier de backup"
            logger.error("Backup Postgres : échec écriture (%s).", type(e).__name__)
            return status
        finally:
            if temp_path.exists():
                temp_path.unlink()

        status["status"] = "SUCCESS"
        status["backup_filename"] = final_name
        status["size_bytes"] = final_path.stat().st_size
        status["checksum"] = checksum
        logger.info("Backup Postgres réussi : %s (%d octets).", final_name, status["size_bytes"])
        return status

    @staticmethod
    def _backup_sqlite_family(backups_dir: Path, timestamp: str, driver: str) -> dict:
        """SQLite/SQLCipher : échec explicite pour SQLCipher (non supporté ici, voir
        backlog SQLCIPHER-AUTO-BACKUP-FIX-1), comportement historique inchangé pour du
        SQLite réellement en clair (cas résiduel), sur le fichier réellement utilisé
        par l'engine actif — jamais un chemin recalculé séparément.
        """
        status = {
            "engine": "sqlite", "status": "FAILED", "backup_filename": None,
            "size_bytes": 0, "checksum": None, "error_code": None, "error_message": None,
        }

        if driver == "pysqlcipher":
            status["status"] = "SKIPPED_UNSUPPORTED_ENGINE"
            status["error_code"] = "SQLCIPHER_AUTO_BACKUP_UNSUPPORTED"
            status["error_message"] = "SQLCipher automatic backup unsupported"
            logger.warning(
                "Backup automatique : moteur SQLite/SQLCipher détecté, non supporté par "
                "cette version du service (backlog SQLCIPHER-AUTO-BACKUP-FIX-1). "
                "Aucune tentative sqlite3 standard sur un fichier chiffré."
            )
            return status

        try:
            from backend.database import engine as active_engine
            db_path_str = active_engine.url.database
        except Exception as e:
            status["error_code"] = "ENGINE_INTROSPECTION_FAILED"
            status["error_message"] = "Impossible de déterminer le fichier SQLite actif"
            logger.error("Backup SQLite : introspection engine échouée (%s).", type(e).__name__)
            return status

        if not db_path_str or db_path_str == ":memory:":
            status["status"] = "SKIPPED_UNSUPPORTED_ENGINE"
            status["error_code"] = "IN_MEMORY_DB"
            status["error_message"] = "Base SQLite en mémoire, rien à sauvegarder"
            return status

        db_path = Path(db_path_str)
        if not db_path.exists():
            status["error_code"] = "SOURCE_NOT_FOUND"
            status["error_message"] = "Fichier SQLite introuvable"
            logger.warning("Backup SQLite : fichier introuvable à %s.", db_path)
            return status

        final_name = f"db_backup_{timestamp}.db.enc"
        final_path = backups_dir / final_name
        cipher = BackupService._get_or_create_key()
        try:
            BackupService._encrypt_and_save(db_path, final_path, cipher)
        except Exception as e:
            status["error_code"] = "ENCRYPTION_FAILED"
            status["error_message"] = "Échec du chiffrement SQLite"
            logger.error("Backup SQLite : échec (%s).", type(e).__name__)
            return status

        if not final_path.exists() or final_path.stat().st_size == 0:
            status["error_code"] = "EMPTY_OUTPUT"
            status["error_message"] = "Fichier de backup SQLite vide"
            return status

        status["status"] = "SUCCESS"
        status["backup_filename"] = final_name
        status["size_bytes"] = final_path.stat().st_size
        status["checksum"] = hashlib.sha256(final_path.read_bytes()).hexdigest()
        return status

    @staticmethod
    def _persist_status(backups_dir: Path, status: dict) -> None:
        """Best-effort : un échec d'écriture du statut ne doit jamais faire échouer
        le backup lui-même ni remonter comme une exception au scheduler."""
        try:
            status_path = backups_dir / "last_backup_status.json"
            status_path.write_text(json.dumps(status, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.warning("Impossible d'écrire le statut de backup : %s", type(e).__name__)

    @staticmethod
    def backup_active_database() -> dict:
        """Orchestrateur unique : détecte le moteur réellement actif et route vers
        la stratégie de backup correspondante. Aucun chemin codé en dur vers
        clinical_vault.db ici — voir _backup_sqlite_family pour le cas résiduel
        SQLite en clair, qui dérive son chemin de l'engine actif lui-même.
        """
        started_at = datetime.utcnow().isoformat() + "Z"
        data_dir = AppPaths.get_user_data_dir()
        backups_dir = data_dir / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            dialect_name, driver = BackupService._detect_engine()
        except Exception as e:
            result = {
                "engine": "unknown", "status": "SKIPPED_UNSUPPORTED_ENGINE",
                "backup_filename": None, "size_bytes": 0, "checksum": None,
                "error_code": "ENGINE_DETECTION_FAILED",
                "error_message": "Impossible de déterminer le moteur actif",
            }
            logger.error("Backup automatique : détection du moteur échouée (%s).", type(e).__name__)
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
            logger.error("Backup automatique : moteur non supporté (%s).", dialect_name)

        result["started_at"] = started_at
        result["completed_at"] = datetime.utcnow().isoformat() + "Z"

        if result["status"] == "SUCCESS":
            BackupService._cleanup_old_backups(backups_dir, prefix="db_backup_", keep=7)
        BackupService._persist_status(backups_dir, result)
        return result

    @staticmethod
    def run_daily_backup():
        """Point d'entrée historique, conservé pour daily_scheduler.py et
        admin.py::trigger_backup (signature booléenne inchangée). Délègue
        entièrement à backup_active_database() — plus de chemin codé en dur."""
        try:
            result = BackupService.backup_active_database()
            if result["status"] == "SUCCESS":
                logger.info(
                    "Sauvegarde automatique réussie (%s, %s).",
                    result["engine"], result["backup_filename"],
                )
                return True
            elif result["status"] == "SKIPPED_UNSUPPORTED_ENGINE":
                logger.warning("Sauvegarde automatique ignorée : %s", result.get("error_message"))
                return False
            else:
                logger.error(
                    "Sauvegarde automatique échouée : %s (%s)",
                    result.get("error_message"), result.get("error_code"),
                )
                return False
        except Exception as e:
            logger.error("Erreur inattendue lors de la sauvegarde automatique : %s", type(e).__name__)
            return False

    @staticmethod
    def restore_backup(enc_file: Path, restore_db: Path):
        cipher_suite = BackupService._get_or_create_key()
        if not enc_file.exists():
            raise FileNotFoundError(f"Fichier chiffré introuvable : {enc_file}")
            
        encrypted_data = enc_file.read_bytes()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        restore_db.write_bytes(decrypted_data)
        logger.info(f"Restauration réussie vers {restore_db}")

    @staticmethod
    def _cleanup_old_backups(backups_dir: Path, prefix: str, keep: int = 7):
        try:
            backups = sorted(
                backups_dir.glob(f"{prefix}*.enc"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if len(backups) > keep:
                for old_backup in backups[keep:]:
                    old_backup.unlink()
                    logger.info(f"Ancienne sauvegarde chiffrée supprimée : {old_backup.name}")
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage : {e}")

backup_service = BackupService()
