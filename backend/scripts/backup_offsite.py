"""Copie best-effort des backups planifiés (DB + médias, déjà chiffrés) vers une
destination hors machine (partage réseau) configurable.

Module pur, entièrement paramétré par l'appelant (backend/scripts/scheduled_backup.py)
-- aucune lecture d'env ici, contrairement à backup_db.py/backup_media.py qui lisent
CABINET_MASTER_KEY_HEX en interne : ce module ne manipule que des octets déjà
chiffrés, aucun secret à charger.

Doctrine produit (verrouillée) : cette copie ne doit JAMAIS faire échouer ni
bloquer le backup local principal. Toute erreur ici se traduit par un statut
structuré, jamais par une exception qui remonterait à l'appelant.
"""
import hashlib
import logging
import os
import shutil
import time
from pathlib import Path

logger = logging.getLogger("backup_offsite")


def _copy_one(source: Path, expected_checksum: str, dest_dir: Path) -> tuple[bool, str | None, str | None]:
    """Copie un seul fichier de backup déjà produit vers dest_dir, vérifie son
    intégrité par re-hash de la copie (jamais du fichier source -- garde ce module
    découplé de la forme interne des résultats de backup local). Ne lève jamais.
    Retourne (copied, error_code, error_message).
    """
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        return False, "DEST_UNREACHABLE", f"Destination inaccessible : {type(e).__name__}"

    dest_path = dest_dir / source.name
    temp_path = dest_dir / f".tmp_{source.name}"
    try:
        shutil.copy2(source, temp_path)
    except (OSError, PermissionError) as e:
        return False, "COPY_FAILED", f"Échec de la copie : {type(e).__name__}"

    try:
        actual_checksum = hashlib.sha256(temp_path.read_bytes()).hexdigest()
        if actual_checksum != expected_checksum:
            return False, "CHECKSUM_MISMATCH", "Le fichier copié ne correspond pas au checksum attendu"
        os.replace(temp_path, dest_path)
    except (OSError, PermissionError) as e:
        return False, "VERIFY_FAILED", f"Échec de vérification/finalisation : {type(e).__name__}"
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    return True, None, None


def copy_to_offsite(
    db_source: Path | None, db_checksum: str | None,
    media_source: Path | None, media_checksum: str | None,
    dest_root: Path,
) -> dict:
    """Copie best-effort des fichiers de backup déjà produits localement vers
    dest_root/db et dest_root/media. Ne lève jamais -- toute erreur devient un champ
    structuré du dict retourné.

    Retourne : {
      "status": "SUCCESS"|"PARTIAL"|"FAILED"|"UNREACHABLE",
      "db_copied": bool, "media_copied": bool,
      "error_code": str|None, "error_message": str|None,
      "duration_seconds": float,
    }

    NOT_CONFIGURED n'est jamais retourné par cette fonction -- c'est à l'appelant
    (scheduled_backup.py) de court-circuiter avant d'appeler cette fonction quand
    aucune destination n'est configurée.
    """
    started = time.monotonic()
    result = {
        "status": "FAILED", "db_copied": False, "media_copied": False,
        "error_code": None, "error_message": None, "duration_seconds": 0.0,
    }

    def _record_error(code: str, message: str):
        if result["error_code"] is None:
            result["error_code"] = code
            result["error_message"] = message

    try:
        dest_root.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.warning("Backup hors-site : destination injoignable (%s).", type(e).__name__)
        result["status"] = "UNREACHABLE"
        result["error_code"] = "DEST_UNREACHABLE"
        result["error_message"] = f"Destination injoignable : {type(e).__name__}"
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        return result

    attempted = 0

    if db_source is not None and db_checksum is not None:
        attempted += 1
        if not db_source.exists():
            _record_error("DB_SOURCE_MISSING", "Fichier de backup DB local introuvable")
            logger.warning("Backup hors-site : source DB introuvable (%s).", db_source)
        else:
            ok, code, msg = _copy_one(db_source, db_checksum, dest_root / "db")
            result["db_copied"] = ok
            if not ok:
                _record_error(code, msg)
                logger.warning("Backup hors-site : copie DB échouée (%s : %s).", code, msg)

    if media_source is not None and media_checksum is not None:
        attempted += 1
        if not media_source.exists():
            _record_error("MEDIA_SOURCE_MISSING", "Fichier de backup médias local introuvable")
            logger.warning("Backup hors-site : source médias introuvable (%s).", media_source)
        else:
            ok, code, msg = _copy_one(media_source, media_checksum, dest_root / "media")
            result["media_copied"] = ok
            if not ok:
                _record_error(code, msg)
                logger.warning("Backup hors-site : copie médias échouée (%s : %s).", code, msg)

    copied_count = int(result["db_copied"]) + int(result["media_copied"])
    if attempted == 0:
        result["status"] = "FAILED"
        _record_error("NOTHING_TO_COPY", "Aucun fichier de backup local à copier")
    elif copied_count == attempted:
        result["status"] = "SUCCESS"
        logger.info("Backup hors-site : copie réussie (%d fichier(s)).", copied_count)
    elif copied_count == 0:
        result["status"] = "FAILED"
    else:
        result["status"] = "PARTIAL"

    result["duration_seconds"] = round(time.monotonic() - started, 3)
    return result
