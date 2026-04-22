
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database import engine

def migrate():
    columns_to_add = [
        ("cloture_note_template", "TEXT DEFAULT 'Arrêtée la présente note à la somme de {total_words} TTC ({total_amount} MAD).'"),
        ("cloture_devis_template", "TEXT DEFAULT 'Arrêté le présent devis à la somme de {total_words} TTC ({total_amount} MAD).'")
    ]
    
    with engine.connect() as connection:
        for col_name, col_def in columns_to_add:
            # Vérifier si la colonne existe déjà
            result = connection.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'cabinet_configs' AND column_name = '{col_name}'
            """))
            
            if result.fetchone():
                print(f"[SKIP] La colonne '{col_name}' existe déjà.")
            else:
                print(f"Ajout de la colonne '{col_name}'...")
                connection.execute(text(f"ALTER TABLE cabinet_configs ADD COLUMN {col_name} {col_def}"))
                connection.commit()
                print(f"[OK] Colonne '{col_name}' ajoutée.")

    print("\n[OK] Migration terminée avec succès!")

if __name__ == "__main__":
    migrate()
