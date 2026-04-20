import os
import sys
from collections import defaultdict
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend import models
from backend.models import DocumentType

def cleanup_logical_duplicates():
    db = SessionLocal()
    try:
        print("Recherche de doublons LOGIQUES (Meme patient, meme jour, meme montant)...")
        
        # On recupere toutes les notes d'honoraires
        notes = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.document_type == DocumentType.NOTE_HONORAIRES
        ).all()
        
        # On groupe par (patient_id, date_jour, montant)
        groups = defaultdict(list)
        
        for n in notes:
            # Extraire le montant du clinical_data
            amount = 0.0
            if n.clinical_data:
                amount = n.clinical_data.get('total', 0.0)
            
            # Cle : Patient + Date (YYYY-MM-DD) + Montant
            date_str = n.created_at.strftime("%Y-%m-%d")
            key = (n.patient_id, date_str, amount)
            groups[key].append(n)
        
        deleted_count = 0
        for key, items in groups.items():
            if len(items) > 1:
                # On a un doublon de contenu ! Pour le meme patient, le meme jour, le meme montant.
                # On garde le premier (id le plus petit)
                items.sort(key=lambda x: x.id)
                keep = items[0]
                to_delete = items[1:]
                
                print(f"  [DOUBLON] Patient {key[0]} | Date {key[1]} | Montant {key[2]} MAD")
                print(f"    Garde: ID {keep.id} ({keep.original_filename})")
                for d in to_delete:
                    print(f"    Supprime: ID {d.id} ({d.original_filename})")
                    db.delete(d)
                    deleted_count += 1
        
        db.commit()
        print(f"\nNettoyage termine ! {deleted_count} doublons logiques supprimes.")
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_logical_duplicates()
