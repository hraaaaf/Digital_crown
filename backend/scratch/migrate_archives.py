import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

# Charger les modèles et config
import sys
sys.path.append('c:/Users/lenovo/Documents/Cabinet/DigitalCrown')
from backend import models

# Load env
load_dotenv('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')
if "?client_encoding=utf8" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

BASE_DIR = Path('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/backend')
ARCHIVE_BASE_DIR = BASE_DIR / "static" / "archives"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

def get_safe_name(name):
    if not name: return "Inconnu"
    return "".join([c if c.isalnum() else "_" for c in name]).strip("_")

def migrate():
    docs = db.query(models.DocumentArchive).all()
    print(f"Migration de {len(docs)} documents...")
    
    moved_count = 0
    error_count = 0
    
    for doc in docs:
        try:
            # 1. Chemin actuel (relatif stocké en BDD)
            # doc.file_path est stocké comme 'static/archives/...'
            old_rel_path = doc.file_path
            old_abs_path = BASE_DIR / old_rel_path
            
            # 2. Calculer le nouveau chemin
            patient = db.query(models.Patient).filter(models.Patient.id == doc.patient_id).first()
            cabinet_id = patient.employer_id if patient else 0
            config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == cabinet_id).first()
            cabinet_name = config.nom_cabinet if config and config.nom_cabinet else f"Cabinet_{cabinet_id}"
            safe_cabinet = get_safe_name(cabinet_name)
            
            # Utiliser la date de création du document
            dt = doc.created_at or datetime.now()
            
            new_rel_dir = Path("static/archives") / safe_cabinet / str(dt.year) / f"{dt.month:02d}" / doc.document_type.value
            new_abs_dir = BASE_DIR / new_rel_dir
            new_abs_dir.mkdir(parents=True, exist_ok=True)
            
            new_abs_path = new_abs_dir / doc.filename
            new_rel_path = str(new_rel_dir / doc.filename).replace("\\", "/")
            
            # 3. Déplacer si nécessaire
            if str(old_abs_path).replace("\\", "/") != str(new_abs_path).replace("\\", "/"):
                if old_abs_path.exists():
                    # Eviter d'écraser si le fichier existe déjà au nouvel endroit (cas rare de collision)
                    if not new_abs_path.exists():
                        shutil.move(old_abs_path, new_abs_path)
                    else:
                        print(f"  [AVERTISSEMENT] Destination existe déjà: {new_abs_path.name}")
                    
                    # Mettre à jour la BDD
                    doc.file_path = new_rel_path
                    moved_count += 1
                else:
                    # Fichier source manquant - on vérifie si il est déjà au bon endroit par hasard
                    if new_abs_path.exists():
                        doc.file_path = new_rel_path
                        moved_count += 1
                    else:
                        print(f"  [ERREUR] Fichier introuvable: {old_abs_path}")
                        error_count += 1
                        
        except Exception as e:
            print(f"  [ERREUR] Document {doc.id}: {e}")
            error_count += 1
            
    db.commit()
    print(f"Migration terminée. Déplacés/Mis à jour: {moved_count}, Erreurs: {error_count}")

    # Nettoyage des dossiers vides dans static/archives
    print("Nettoyage des dossiers vides...")
    for root, dirs, files in os.walk(ARCHIVE_BASE_DIR, topdown=False):
        for name in dirs:
            dir_path = os.path.join(root, name)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

if __name__ == "__main__":
    migrate()
