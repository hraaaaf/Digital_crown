from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv('c:/Users/lenovo/Documents/Cabinet/DigitalCrown/backend/.env')

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("DATABASE_URL non trouvée dans le .env")
    exit(1)

# Nettoyer l'URL si nécessaire (client_encoding=utf8 peut parfois poser problème à SQLAlchemy direct)
if "?client_encoding=utf8" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]

try:
    # Utiliser l'URL directement dans create_engine
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # Exécution de l'update global
        # On met tout le monde en SILVER
        result = connection.execute(text("UPDATE patients SET manual_grade = 'SILVER'"))
        connection.commit()
        print(f"Mise à jour réussie : {result.rowcount} patients ont été passés en grade SILVER.")
except Exception as e:
    print(f"Erreur lors de la mise à jour : {e}")
