"""Restauration d'une sauvegarde DB chiffrée produite par backup_db.py.

Usage :
  python -m backend.scripts.restore_db <backup_path> --yes
  python -m backend.scripts.restore_db <backup_path> --yes --target-db <nom_db_jetable>

--target-db permet de restaurer sur une base PostgreSQL DIFFÉRENTE de
DATABASE_URL (même host/user/password, nom de base remplacé) — utile pour
valider un restore sur une base jetable sans jamais toucher la vraie DB.

ATTENTION : DESTRUCTIF sur la base ciblée. Toujours faire un backup_db.py de
l'état actuel AVANT de restaurer sur la vraie DB, et confirmer explicitement
(--yes).
"""
import os
import sys
import logging
import subprocess

from backend.env_loader import load_backend_env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_backend_env(override=True)

from backend.config import settings
from backend.scripts.backup_db import get_cipher, find_pg_binary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("restore")


def restore_db(backup_path: str, confirm: bool = False, target_db: str = None):
    if not os.path.isfile(backup_path):
        logger.error(f"Fichier de sauvegarde introuvable : {backup_path}")
        sys.exit(1)

    if not confirm:
        logger.error(
            "Restore refusé sans confirmation explicite. Relancez avec --yes "
            "après avoir vérifié que la cible est bien celle voulue."
        )
        sys.exit(1)

    db_url = settings.DATABASE_URL
    cipher = get_cipher()

    logger.info(f"Déchiffrement de {backup_path}...")
    with open(backup_path, "rb") as f:
        decrypted_data = cipher.decrypt(f.read())

    if db_url.startswith("sqlite"):
        if target_db:
            logger.error("--target-db non supporté pour SQLite (fichier unique).")
            sys.exit(1)
        db_path = db_url.replace("sqlite:///", "").replace("./", f"{BASE_DIR}/")
        logger.warning(f"Écrasement du fichier SQLite : {db_path}")
        with open(db_path, "wb") as f:
            f.write(decrypted_data)
        logger.info("✅ Restore SQLite terminé.")

    elif db_url.startswith("postgresql"):
        try:
            auth_part, host_part = db_url.replace("postgresql://", "").split("@")
            user, password = auth_part.split(":")
            host_db = host_part.split("/")
            host = host_db[0]
            dbname = target_db or host_db[1].split("?")[0]
        except Exception as e:
            logger.error(f"Erreur lors du parsing de DATABASE_URL : {e}")
            sys.exit(1)

        env = os.environ.copy()
        env["PGPASSWORD"] = password

        logger.warning(f"Écrasement de la base PostgreSQL : {dbname} (--clean dans le dump gère le DROP)")
        try:
            process = subprocess.run(
                [find_pg_binary("psql"), "-U", user, "-h", host, "-d", dbname],
                input=decrypted_data,
                env=env,
                capture_output=True,
                check=True,
            )
            logger.info("✅ Restore PostgreSQL terminé.")
            if process.stderr:
                logger.info(process.stderr.decode(errors="replace"))
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ ERREUR psql : {e.stderr.decode(errors='replace')}")
            sys.exit(1)
    else:
        logger.error(f"DATABASE_URL non supporté pour restore : {db_url}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.scripts.restore_db <backup_path> --yes [--target-db <nom_db>]")
        sys.exit(1)
    path = sys.argv[1]
    confirmed = "--yes" in sys.argv
    target = None
    if "--target-db" in sys.argv:
        idx = sys.argv.index("--target-db")
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    restore_db(path, confirm=confirmed, target_db=target)
