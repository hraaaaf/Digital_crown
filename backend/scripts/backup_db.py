import os
import sys
import shutil
import datetime
import logging
import subprocess
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Charger .env pour obtenir CABINET_MASTER_KEY_HEX
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backup")

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

def backup_db():
    """
    Script de sauvegarde automatisée et CHIFFRÉE de la base de données.
    Supporte SQLite et PostgreSQL.
    """
    db_url = settings.DATABASE_URL
    backup_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cipher = get_cipher()
    
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite:///", "").replace("./", f"{BASE_DIR}/")
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
            auth_part, host_part = db_url.replace("postgresql://", "").split("@")
            user, password = auth_part.split(":")
            host_db = host_part.split("/")
            host = host_db[0]
            dbname = host_db[1].split("?")[0]
        except Exception as e:
            logger.error(f"Erreur lors du parsing de DATABASE_URL : {e}")
            sys.exit(1)
            
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.sql.enc")
        logger.info(f"Début sauvegarde PostgreSQL chiffrée de {dbname}...")
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        try:
            process = subprocess.run(
                ["pg_dump", "-U", user, "-h", host, "-d", dbname, "-F", "p", "--clean"],
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
            logger.error(f"❌ ERREUR pg_dump: {e.stderr.decode()}")
            sys.exit(1)

if __name__ == "__main__":
    backup_db()
