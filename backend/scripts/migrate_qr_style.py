import os
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    if not DATABASE_URL:
        print("DATABASE_URL non trouvée dans le .env")
        return

    print(f"Connexion à la base de données : {DATABASE_URL.split('@')[-1]}")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='cabinet_configs' AND column_name='qr_code_style';
        """)
        
        if cur.fetchone():
            print("OK: La colonne 'qr_code_style' existe déjà.")
        else:
            print("AJOUT: Ajout de la colonne 'qr_code_style' à 'cabinet_configs'...")
            cur.execute("ALTER TABLE cabinet_configs ADD COLUMN qr_code_style VARCHAR(20) DEFAULT 'dots' NOT NULL;")
            conn.commit()
            print("SUCCESS: Migration terminée avec succès !")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: Erreur lors de la migration : {e}")

if __name__ == "__main__":
    migrate()
