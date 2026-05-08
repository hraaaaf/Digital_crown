import os
import sys
from pathlib import Path

# Add backend to path to import models and database
sys.path.append(os.path.join(os.getcwd()))

from backend.database import SessionLocal
from backend import models

def reconcile():
    db = SessionLocal()
    try:
        # 1. Get all records from database
        db_docs = db.query(models.DocumentArchive).all()
        db_files = {doc.file_path for doc in db_docs}
        print(f"Nombre d'entrees en BDD (document_archives): {len(db_docs)}")
        for doc in db_docs:
            print(f"  DB: ID={doc.id}, Patient={doc.patient_id}, Type={doc.document_type}, Path={doc.file_path}, Title={doc.title}")

        # 2. Scan filesystem (static/archives)
        print("\nScan du systeme de fichiers (static/archives):")
        archives_dir = Path("static/archives")
        if not archives_dir.exists():
            print("  Repertoire static/archives n'existe pas.")
            return

        fs_files = []
        for root, dirs, files in os.walk(archives_dir):
            for file in files:
                if file.endswith(".pdf"):
                    full_path = os.path.join(root, file)
                    fs_files.append(full_path)
                    print(f"  FS: {full_path}")

        # 3. Find orphaned files (in FS but not in DB)
        orphans = [f for f in fs_files if f.replace("/", "\\") not in [db_f.replace("/", "\\") for db_f in db_files]]
        print(f"\nFichiers orphelins (sur disque mais pas en BDD): {len(orphans)}")
        for o in orphans:
            print(f"  ORPHELIN: {o}")

    finally:
        db.close()

if __name__ == "__main__":
    reconcile()
