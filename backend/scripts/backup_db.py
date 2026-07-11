import os
import sys
import shutil
import datetime
import logging
import subprocess
import base64
import argparse
from urllib.parse import urlparse
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.env_loader import load_backend_env
from backend.core.media_paths import is_rehearsal_environment

# Charger l'env backend pour obtenir CABINET_MASTER_KEY_HEX.
# NE PAS appeler load_backend_env(override=True) au niveau module, et NE PAS importer
# `settings` (backend.config) au niveau module non plus : ce fichier est aussi importé
# comme librairie par backend/services/backup_service.py, dans le process réel déjà
# démarré (env déjà chargé correctement par main.py). Un override=True inconditionnel
# ici écraserait silencieusement la config réelle en place (cf. CLAUDE.md : "ne JAMAIS
# écraser des vars déjà injectées par l'OS/orchestrateur"), et un `settings` importé
# au niveau module figerait sa lecture AVANT le load_backend_env fait sous __main__
# pour l'usage CLI (Settings() lit os.environ en priorité sur son propre env_file —
# l'ordre d'exécution compte). `settings` est donc importé paresseusement dans
# backup_db(), après que l'appelant (CLI __main__, ou main.py pour le process réel)
# ait déjà chargé l'environnement correctement.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backup")


def _mask_database_url(db_url: str) -> str:
    if "://" in db_url and "@" in db_url:
        prefix, rest = db_url.split("://", 1)
        auth, suffix = rest.split("@", 1)
        user = auth.split(":", 1)[0]
        return f"{prefix}://{user}:***@{suffix}"
    return db_url


def _parse_postgres_url(db_url: str) -> tuple[str, str, str | None, str, str]:
    parsed = urlparse(db_url)
    if parsed.scheme != "postgresql":
        raise ValueError(f"Unsupported scheme: {parsed.scheme}")
    host = parsed.hostname or ""
    port = str(parsed.port) if parsed.port else None
    dbname = parsed.path.lstrip("/")
    user = parsed.username or ""
    password = parsed.password or ""
    return user, password, host, port, dbname


def _validate_rehearsal_database(db_url: str) -> None:
    if is_rehearsal_environment() and "digitalcrown_db" in db_url.lower():
        raise RuntimeError("Unsafe DATABASE_URL for rehearsal")


def find_pg_binary(name: str) -> str:
    """Localise pg_dump/psql : PATH d'abord, sinon scan des installs Windows standards.

    Sur Windows, l'installeur PostgreSQL n'ajoute pas toujours son dossier bin
    au PATH système — pg_dump/psql existent sur le disque mais restent
    introuvables par subprocess.run([name, ...]) sans ce fallback.
    """
    found = shutil.which(name)
    if found:
        return found

    import glob
    candidates = sorted(
        glob.glob(f"C:/Program Files/PostgreSQL/*/bin/{name}.exe"),
        reverse=True,  # version la plus récente en premier
    )
    if candidates:
        return candidates[0]

    return name  # fallback : laisser subprocess échouer avec une erreur claire

def get_cipher():
    master_key_hex = os.getenv("CABINET_MASTER_KEY_HEX")
    if not master_key_hex:
        logger.error("CABINET_MASTER_KEY_HEX introuvable dans .env. Le backup DOIT être chiffré.")
        sys.exit(1)
        
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"digitalcrown_backup_salt_2026", # Sel constant pour la dérivation
        iterations=100000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(bytes.fromhex(master_key_hex)))
    return Fernet(derived_key)

def backup_db(*, dry_run: bool = False):
    """
    Script de sauvegarde automatisée et CHIFFRÉE de la base de données.
    Supporte SQLite et PostgreSQL.
    """
    from backend.config import settings
    db_url = settings.DATABASE_URL
    _validate_rehearsal_database(db_url)
    logger.info("Target database: %s", _mask_database_url(db_url))
    backup_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cipher = get_cipher()
    
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "").replace("./", f"{BASE_DIR}/")
        if dry_run:
            logger.info("Dry-run SQLite source: %s", db_path)
            return
        if os.path.exists(db_path):
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db.enc")
            logger.info(f"Début sauvegarde SQLite chiffrée de {db_path}...")
            with open(db_path, "rb") as f:
                data = f.read()
            encrypted_data = cipher.encrypt(data)
            with open(backup_path, "wb") as f:
                f.write(encrypted_data)
            logger.info(f"✅ Sauvegarde SQLite chiffrée effectuée : {backup_path}")
        else:
            logger.error(f"Fichier BDD introuvable : {db_path}")
            
    elif db_url.startswith("postgresql"):
        # PostgreSQL : pg_dump requis
        try:
            user, password, host, port, dbname = _parse_postgres_url(db_url)
        except Exception as e:
            logger.error(f"Erreur lors du parsing de DATABASE_URL : {e}")
            sys.exit(1)

        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.sql.enc")
        logger.info(f"Début sauvegarde PostgreSQL chiffrée de {dbname}...")
        if dry_run:
            logger.info("Dry-run PostgreSQL target: db=%s host=%s port=%s user=%s", dbname, host, port or "default", user)
            return

        env = os.environ.copy()
        env["PGPASSWORD"] = password

        pg_dump_cmd = [find_pg_binary("pg_dump"), "-U", user, "-h", host]
        if port:
            pg_dump_cmd += ["-p", port]
        pg_dump_cmd += ["-d", dbname, "-F", "p", "--clean"]

        try:
            process = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                check=True
            )
            dump_data = process.stdout
            encrypted_data = cipher.encrypt(dump_data)

            with open(backup_path, "wb") as f:
                f.write(encrypted_data)

            logger.info(f"✅ Sauvegarde PostgreSQL chiffrée effectuée avec succès : {backup_path}")
            logger.info(f"Taille finale : {len(encrypted_data) / 1024 / 1024:.2f} MB")

        except subprocess.CalledProcessError as e:
            # errors="replace" : le stderr de pg_dump sous Windows peut être dans
            # l'encodage local (ex: cp1252) plutôt qu'UTF-8 -- ne jamais planter
            # sur le decode, sinon l'erreur réelle de pg_dump est masquée.
            logger.error(f"❌ ERREUR pg_dump: {e.stderr.decode(errors='replace')}")
            sys.exit(1)

if __name__ == "__main__":
    # Chargement explicite uniquement pour l'usage CLI direct (pas pour l'import
    # comme librairie, cf. commentaire en tête de fichier) : get_cipher() lit
    # CABINET_MASTER_KEY_HEX via os.getenv(), qui a besoin que load_backend_env
    # ait effectivement peuplé os.environ (contrairement à `settings`, qui lit son
    # propre env_file indépendamment via pydantic-settings).
    load_backend_env(override=True)
    parser = argparse.ArgumentParser(description="Backup encrypted database.")
    parser.add_argument("--dry-run", action="store_true", help="Validate backup target without running pg_dump or writing files.")
    args = parser.parse_args()
    backup_db(dry_run=args.dry_run)
