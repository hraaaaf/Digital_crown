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

from backend.env_loader import load_backend_env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_backend_env(override=True)

from backend.core.paths import AppPaths
from backend.scripts.backup_db import get_cipher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backup_media")


def backup_media():
    """Zippe puis chiffre le dossier média (%APPDATA%/DigitalCrown/media)."""
    media_dir = AppPaths.get_user_data_dir() / "media"
    if not media_dir.exists():
        logger.warning(f"Dossier média introuvable : {media_dir} — rien à sauvegarder.")
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
    backup_media()
