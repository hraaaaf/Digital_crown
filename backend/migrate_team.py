"""
Migration : Ajout des colonnes employer_id et is_active à la table users.
Exécuter une seule fois : python backend/migrate_team.py
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from backend.database import engine

def migrate():
    with engine.connect() as conn:
        # 1. Ajout de is_active (defaut True pour tous les comptes existants)
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL"))
            print("[OK] Colonne 'is_active' ajoutee.")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("[INFO] Colonne 'is_active' existe deja.")
            else:
                print(f"[WARN] is_active : {e}")

        # 2. Ajout de employer_id (FK vers users.id)
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN employer_id INTEGER REFERENCES users(id) ON DELETE CASCADE"))
            print("[OK] Colonne 'employer_id' ajoutee.")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("[INFO] Colonne 'employer_id' existe deja.")
            else:
                print(f"[WARN] employer_id : {e}")

        conn.commit()
        print("[DONE] Migration terminee.")

if __name__ == "__main__":
    migrate()
