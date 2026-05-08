"""
Script de migration pour ajouter la colonne numero_dossier à la table patients.
Génère également des numéros de dossier pour les patients existants.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database import engine
from backend.models import Patient
from sqlalchemy.orm import Session

def migrate():
    with engine.connect() as connection:
        # Vérifier si la colonne existe déjà
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'patients' AND column_name = 'numero_dossier'
        """))
        
        if result.fetchone():
            print("[OK] La colonne 'numero_dossier' existe déjà.")
            return
        
        # Ajouter la colonne
        print("Ajout de la colonne 'numero_dossier'...")
        connection.execute(text("""
            ALTER TABLE patients 
            ADD COLUMN numero_dossier VARCHAR(20) UNIQUE
        """))
        connection.commit()
        print("[OK] Colonne ajoutée avec succès.")
        
    # Générer des numéros pour les patients existants
    print("Génération des numéros de dossier pour les patients existants...")
    from backend.database import SessionLocal
    db = SessionLocal()
    
    try:
        patients = db.query(Patient).filter(Patient.numero_dossier.is_(None)).all()
        
        for i, patient in enumerate(patients, start=1):
            numero = f"P-{patient.id:06d}"
            patient.numero_dossier = numero
            print(f"  - Patient {patient.nom} {patient.prenom}: {numero}")
        
        db.commit()
        print(f"[OK] {len(patients)} patients mis à jour.")
        
    except Exception as e:
        db.rollback()
        print(f"[ERREUR] {e}")
        raise
    finally:
        db.close()
    
    print("\n[OK] Migration terminée avec succès!")

if __name__ == "__main__":
    migrate()
