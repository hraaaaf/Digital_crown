import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import sys

sys.path.append('c:/Users/lenovo/Documents/Cabinet/DigitalCrown')
from backend import models

load_dotenv('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/backend/.env')
DATABASE_URL = os.getenv('DATABASE_URL')
if "?client_encoding=utf8" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

BASE_DIR = Path('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/backend')
DOCS_DIR = BASE_DIR / "static" / "documents"
ARCHIVE_BASE_DIR = BASE_DIR / "static" / "archives"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

def get_safe_name(name):
    if not name: return "Inconnu"
    return "".join([c if c.isalnum() else "_" for c in name]).strip("_")

def cleanup_legacy_docs():
    print("Vérification des fichiers orphelins dans static/documents...")
    
    # 1. Panoramic PDFs
    pan_dir = DOCS_DIR / "panoramic"
    if pan_dir.exists():
        for f in pan_dir.glob("*.pdf"):
            # Essayer de trouver le patient par le nom dans le fichier ? 
            # Les bilans n'ont pas forcément le nom du patient dans le filename
            # On va essayer de trouver l'analyse en base
            filename = f.name
            # Ces fichiers sont souvent liés à PanoramicAnalysis (image_path)
            # Mais ici c'est le PDF.
            # On va les mettre dans un dossier "Unsorted" par cabinet par défaut si on trouve pas
            # Ou simplement les laisser si on peut pas les attribuer.
            pass

    # 2. Files in static/documents/2026/05/...
    # Ces fichiers sont normalement des doublons de DocumentArchive.
    # Si ils existent dans DocumentArchive, on peut les supprimer ou les déplacer.
    # Le plus sûr est de les laisser mais de s'assurer que static/archives est PROPRE.
    
    print("Nettoyage des fichiers panoramiques racines vers archives...")
    # On a vu 4 fichiers dans static/documents/panoramic
    # bilan_panoramique_20260512_003755.pdf etc.
    
    for f in (DOCS_DIR / "panoramic").glob("bilan_panoramique_*.pdf"):
        # On va les mettre dans le cabinet par défaut (ID 1) pour l'instant si on trouve pas mieux
        # Car on ne peut pas facilement savoir quel patient c'est juste par le timestamp
        dt = datetime.fromtimestamp(f.stat().st_mtime)
        
        # On prend le premier cabinet pour le test ou on cherche l'analyse correspondante
        safe_cabinet = "Cabinet_Elite" # Valeur par défaut pour le rangement
        
        dest_dir = ARCHIVE_BASE_DIR / safe_cabinet / str(dt.year) / f"{dt.month:02d}" / "PANORAMIQUE"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(f, dest_dir / f.name)
        print(f"  Déplacé: {f.name} -> {dest_dir}")

if __name__ == "__main__":
    cleanup_legacy_docs()
