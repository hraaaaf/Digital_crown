"""Sauvegarde chiffrée du dossier média (radios, RVG, documents archivés).

Usage : python -m backend.scripts.backup_media

Réutilise le même chiffrement (Fernet dérivé de CABINET_MASTER_KEY_HEX)
que backup_db.py pour rester cohérent avec la stratégie de sauvegarde DB.
"""
import os
import sys
import datetime
import hashlib
import logging
import uuid
import zipfile
import io
import argparse
from pathlib import Path

from backend.env_loader import load_backend_env

# NE PAS appeler load_backend_env(override=True) ni importer get_cipher au niveau
# module : ce fichier est aussi importé comme librairie par
# backend/scripts/scheduled_backup.py, dans le process réel déjà démarré (env déjà
# chargé correctement par main.py). Même piège et même correctif que backup_db.py
# (AUTO-BACKUP-POSTGRES-ROUTING-FIX-1) — voir CLAUDE.md.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backup_media")


def _build_media_archive(dest_dir: Path, timestamp: str) -> dict:
    """Zippe puis chiffre le dossier média actif vers *dest_dir* (paramétrable).

    Réutilisé par backup_media() (destination historique backend/backups) et par
    backend/scripts/scheduled_backup.py (destination scheduled/media). Écriture
    atomique (temp scopé par UUID + os.replace()), checksum SHA-256, statut
    structuré — même esprit que BackupService._backup_postgres().
    """
    from backend.core.media_paths import get_media_root, get_real_media_root, is_rehearsal_environment

    status = {
        "status": "FAILED", "backup_filename": None, "size_bytes": 0,
        "file_count": 0, "checksum": None, "error_code": None, "error_message": None,
    }

    media_dir = get_media_root()
    real_media_dir = get_real_media_root().resolve(strict=False)
    if is_rehearsal_environment() and media_dir.resolve(strict=False) == real_media_dir:
        status["error_code"] = "UNSAFE_REHEARSAL_MEDIA_ROOT"
        status["error_message"] = "Unsafe MEDIA_ROOT for rehearsal"
        return status

    logger.info("Source media dir: %s", media_dir)
    if not media_dir.exists():
        status["error_code"] = "SOURCE_NOT_FOUND"
        status["error_message"] = "Dossier média introuvable"
        logger.warning("Dossier média introuvable : %s — rien à sauvegarder.", media_dir)
        return status

    dest_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Compression du dossier média : %s...", media_dir)
    buffer = io.BytesIO()
    file_count = 0
    try:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(media_dir):
                for filename in files:
                    abs_path = os.path.join(root, filename)
                    arcname = os.path.relpath(abs_path, media_dir)
                    try:
                        zf.write(abs_path, arcname)
                        file_count += 1
                    except OSError as e:
                        status["error_code"] = "UNREADABLE_FILE"
                        status["error_message"] = "Un fichier média est illisible"
                        logger.error("Backup média : fichier illisible %s (%s).", arcname, type(e).__name__)
                        return status
    except Exception as e:
        status["error_code"] = "ARCHIVE_BUILD_FAILED"
        status["error_message"] = "Échec de la compression"
        logger.error("Backup média : échec compression (%s).", type(e).__name__)
        return status

    logger.info("Chiffrement de l'archive (%d fichiers)...", file_count)
    try:
        from backend.scripts.backup_db import get_cipher
        cipher = get_cipher()
        encrypted_data = cipher.encrypt(buffer.getvalue())
    except SystemExit:
        status["error_code"] = "MISSING_MASTER_KEY"
        status["error_message"] = "CABINET_MASTER_KEY_HEX manquant"
        logger.error("Backup média : CABINET_MASTER_KEY_HEX manquant, backup refusé.")
        return status
    except Exception as e:
        status["error_code"] = "ENCRYPTION_FAILED"
        status["error_message"] = "Échec du chiffrement"
        logger.error("Backup média : échec chiffrement (%s).", type(e).__name__)
        return status

    if not encrypted_data:
        status["error_code"] = "EMPTY_ENCRYPTED_OUTPUT"
        status["error_message"] = "Sortie chiffrée vide"
        return status

    final_name = f"media_backup_{timestamp}.zip.enc"
    final_path = dest_dir / final_name
    temp_path = dest_dir / f".tmp_{uuid.uuid4().hex}_{final_name}"
    checksum = hashlib.sha256(encrypted_data).hexdigest()
    try:
        temp_path.write_bytes(encrypted_data)
        if temp_path.stat().st_size == 0:
            raise RuntimeError("temp media archive is empty")
        os.replace(temp_path, final_path)
    except Exception as e:
        status["error_code"] = "WRITE_FAILED"
        status["error_message"] = "Échec écriture de l'archive média"
        logger.error("Backup média : échec écriture (%s).", type(e).__name__)
        return status
    finally:
        if temp_path.exists():
            temp_path.unlink()

    status["status"] = "SUCCESS"
    status["backup_filename"] = final_name
    status["size_bytes"] = final_path.stat().st_size
    status["file_count"] = file_count
    status["checksum"] = checksum
    logger.info(
        "✅ Sauvegarde média chiffrée effectuée : %s (%.2f MB, %d fichiers)",
        final_path, status["size_bytes"] / 1024 / 1024, file_count,
    )
    return status


def backup_media(*, dry_run: bool = False):
    """Zippe puis chiffre le dossier média actif — wrapper CLI historique."""
    from backend.core.media_paths import get_media_root, get_real_media_root, is_rehearsal_environment

    media_dir = get_media_root()
    real_media_dir = get_real_media_root().resolve(strict=False)
    if is_rehearsal_environment() and media_dir.resolve(strict=False) == real_media_dir:
        raise RuntimeError("Unsafe MEDIA_ROOT for rehearsal")

    logger.info("Source media dir: %s", media_dir)
    if not media_dir.exists():
        logger.warning("Dossier média introuvable : %s — rien à sauvegarder.", media_dir)
        return
    if dry_run:
        logger.info("Dry-run: aucune archive media créée.")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result = _build_media_archive(Path(BASE_DIR) / "backups", timestamp)
    if result["status"] != "SUCCESS":
        logger.error("Échec de la sauvegarde média : %s", result.get("error_message"))


if __name__ == "__main__":
    load_backend_env(override=True)
    parser = argparse.ArgumentParser(description="Backup encrypted media directory.")
    parser.add_argument("--dry-run", action="store_true", help="Validate media source without writing a backup.")
    args = parser.parse_args()
    backup_media(dry_run=args.dry_run)
