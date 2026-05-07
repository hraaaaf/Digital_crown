
import sys
import os

# Ajouter le répertoire racine du projet au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import engine
from sqlalchemy import text

def migrate():
    print("START: Migration manuelle des colonnes CabinetConfig...")
    
    columns_to_add = [
        ("qr_code_enabled", "BOOLEAN DEFAULT FALSE NOT NULL"),
        ("qr_code_type", "VARCHAR(20) DEFAULT 'VCARD' NOT NULL"),
        ("qr_code_value", "VARCHAR(500)"),
        ("qr_code_color", "VARCHAR(7)"),
        ("qr_code_label", "VARCHAR(100)"),
        ("cloture_note_template", "TEXT DEFAULT 'Arrêtée la présente note à la somme de {total_words} TTC ({total_amount} MAD).' NOT NULL"),
        ("cloture_devis_template", "TEXT DEFAULT 'Arrêté le présent devis à la somme de {total_words} TTC ({total_amount} MAD).' NOT NULL")
    ]
    
    with engine.connect() as conn:
        for col_name, col_def in columns_to_add:
            try:
                # Vérifier si la colonne existe
                check_sql = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='cabinet_configs' AND column_name='{col_name}';")
                result = conn.execute(check_sql).fetchone()
                
                if not result:
                    print(f"ADD: Ajout de la colonne {col_name}...")
                    alter_sql = text(f"ALTER TABLE cabinet_configs ADD COLUMN {col_name} {col_def};")
                    conn.execute(alter_sql)
                    conn.commit()
                    print(f"OK: Colonne {col_name} ajoutee.")
                else:
                    print(f"INFO: La colonne {col_name} existe deja.")
            except Exception as e:
                print(f"ERROR: Erreur lors de l'ajout de {col_name}: {e}")
                conn.rollback()

    print("END: Migration terminee.")

if __name__ == "__main__":
    migrate()
