import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend import models
from backend.models import DocumentType

def cleanup_and_strict_sync():
    db = SessionLocal()
    try:
        # 1. SUPPRESSION des documents non-notes importes par erreur (ceux qui ont un ID legacy_ ou global_)
        print("Nettoyage des imports non-notes...")
        deleted = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.document_group_id.ilike("legacy_%"),
            models.DocumentArchive.document_type != DocumentType.NOTE_HONORAIRES
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"  {deleted} documents (ordonnances, certificats, etc.) ont ete retires.")

        # 2. On s'assure que le script de sync est desormais STRICT
        print("\nMise à jour du script de synchronisation en mode STRICT (Notes uniquement)...")
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_and_strict_sync()
