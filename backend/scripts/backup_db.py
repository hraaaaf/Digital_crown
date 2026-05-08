import os
import shutil
import datetime
import logging
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backup")

def backup_db():
    """
    Script de sauvegarde automatique de la base de donnees.
    Adapte pour SQLite par defaut.
    """
    db_url = settings.DATABASE_URL
    backup_dir = os.path.join(os.getcwd(), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if db_url.startswith("sqlite"):
        # SQLite : On copie simplement le fichier
        db_path = db_url.replace("sqlite:///", "")
        if os.path.exists(db_path):
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
            shutil.copy2(db_path, backup_path)
            logger.info(f"Sauvegarde SQLite effectuee : {backup_path}")
            
            # Nettoyage : Garder seulement les 30 derniers jours
            # (Optionnel : implementer rotation)
        else:
            logger.error(f"Fichier BDD introuvable : {db_path}")
            
    elif db_url.startswith("postgresql"):
        # PostgreSQL : pg_dump requis
        # Exemple de commande (non executee ici sans certitude sur l'environnement)
        # os.system(f"pg_dump {db_url} > {backup_dir}/backup_{timestamp}.sql")
        logger.warning("Sauvegarde PostgreSQL : pg_dump requis dans l'environnement.")
    
if __name__ == "__main__":
    backup_db()
