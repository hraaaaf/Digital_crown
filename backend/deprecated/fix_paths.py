import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend import models

def fix_paths_and_amounts():
    db = SessionLocal()
    try:
        print("Correction des chemins de fichiers et des montants...")
        
        # 1. Reparer les chemins qui commencent par "backend/"
        docs = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.file_path.ilike("backend/%")
        ).all()
        
        for doc in docs:
            doc.file_path = doc.file_path.replace("backend/", "")
            print(f"  Repare: {doc.filename}")

        # 2. On s'assure que les chemins static sont propres
        # (Certains pourraient manquer le '/' au debut ou avoir des doubles)
        all_docs = db.query(models.DocumentArchive).all()
        for doc in all_docs:
            if doc.file_path.startswith("/static"):
                doc.file_path = doc.file_path[1:]
        
        db.commit()
        print("\nChemins repares. Tu peux maintenant ouvrir les fichiers.")
        
    finally:
        db.close()

if __name__ == "__main__":
    fix_paths_and_amounts()
