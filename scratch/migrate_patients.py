import sys
import os

# Ajout du chemin parent pour importer database
sys.path.append(os.getcwd())

from backend import database, models
from sqlalchemy import text

def migrate():
    db = next(database.get_db())
    try:
        print("Tentative de migration manuelle de la table 'patients'...")
        
        # Ajout de manual_grade
        db.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS manual_grade VARCHAR(20)"))
        
        # Ajout de grade_comment
        db.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS grade_comment TEXT"))
        
        db.commit()
        print("Migration réussie ! Les colonnes 'manual_grade' et 'grade_comment' ont été ajoutées.")
    except Exception as e:
        db.rollback()
        print(f"Erreur lors de la migration : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
