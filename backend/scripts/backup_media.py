"""Sauvegarde chiffrée du dossier média (radios, RVG, documents archivés).

Usage : python -m backend.scripts.backup_media

Réutilise le même chiffrement (Fernet dérivé de CABINET_MASTER_KEY_HEX)
que backup_db.py pour rester cohérent avec la stratégie de sauvegarde DB.
"""
import os
import sys
import datetime
import logging
import zipfile
import io
import argparse

from backend.env_loader import load_backend_env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_backend_env(override=True)

from backend.core.media_paths import get_media_root, get_real_media_root, is_rehearsal_environment
from backend.scripts.backup_db import get_cipher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backup_media")


def backup_media(*, dry_run: bool = False):
    """Zippe puis chiffre le dossier média actif."""
    media_dir = get_media_root()
    real_media_dir = get_real_media_root().resolve(strict=False)
    if is_rehearsal_environment() and media_dir.resolve(strict=False) == real_media_dir:
        raise RuntimeError("Unsafe MEDIA_ROOT for rehearsal")

    logger.info("Source media dir: %s", media_dir)
    if not media_dir.exists():
        logger.warning(f"Dossier média introuvable : {media_dir} — rien à sauvegarder.")
        return
    if dry_run:
        logger.info("Dry-run: aucune archive media créée.")
        return

    backup_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"media_backup_{timestamp}.zip.enc")

    logger.info(f"Compression du dossier média : {media_dir}...")
    buffer = io.BytesIO()
    file_count = 0
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(media_dir):
            for filename in files:
                abs_path = os.path.join(root, filename)
                arcname = os.path.relpath(abs_path, media_dir)
                zf.write(abs_path, arcname)
                file_count += 1

    logger.info(f"Chiffrement de l'archive ({file_count} fichiers)...")
    cipher = get_cipher()
    encrypted_data = cipher.encrypt(buffer.getvalue())

    with open(backup_path, "wb") as f:
        f.write(encrypted_data)

    size_mb = len(encrypted_data) / 1024 / 1024
    logger.info(f"✅ Sauvegarde média chiffrée effectuée : {backup_path} ({size_mb:.2f} MB, {file_count} fichiers)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup encrypted media directory.")
    parser.add_argument("--dry-run", action="store_true", help="Validate media source without writing a backup.")
    args = parser.parse_args()
    backup_media(dry_run=args.dry_run)
