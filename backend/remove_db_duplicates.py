import os
import sys
from collections import defaultdict

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend import models

def remove_duplicates():
    db = SessionLocal()
    try:
        print("Recherche de doublons reels en base de donnees...")
        
        # On groupe les documents par (patient_id, nom_du_fichier)
        docs = db.query(models.DocumentArchive).all()
        groups = defaultdict(list)
        
        for d in docs:
            # Cle unique: ID Patient + Nom du fichier
            key = (d.patient_id, d.original_filename)
            groups[key].append(d)
        
        deleted_count = 0
        for key, items in groups.items():
            if len(items) > 1:
                # On trie par date de creation et on garde le premier (le plus ancien ou le plus complet)
                items.sort(key=lambda x: x.created_at)
                keep = items[0]
                to_delete = items[1:]
                
                print(f"  Doublon trouve pour Patient {key[0]} : {key[1]} ({len(items)} exemplaires)")
                for d in to_delete:
                    db.delete(d)
                    deleted_count += 1
        
        db.commit()
        print(f"\nNettoyage termine ! {deleted_count} doublons supprimes de la base de donnees.")
        print("La comptabilite est desormais a jour et sans doublons.")
        
    finally:
        db.close()

if __name__ == "__main__":
    remove_duplicates()
