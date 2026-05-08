import sys
import os
from sqlalchemy import create_engine, text

# URL de connexion
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@localhost/digitalcrown_db"

def migrate():
    print("🚀 Début de la migration manuelle...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("⏳ Tentative d'ajout de la colonne 'assurance' à la table 'patients'...")
            conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS assurance VARCHAR(50);"))
            conn.commit()
            print("✅ Succès : La colonne 'assurance' a été ajoutée.")
        except Exception as e:
            print(f"❌ Erreur : {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
