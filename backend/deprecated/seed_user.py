import sys
import os

# Rigueur CTO : On force Python à trouver le dossier racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend import models
from backend.security import get_password_hash

def seed_admin_user():
    db = SessionLocal()
    try:
        admin_email = "admin@digitalcrown.com"
        admin_password = "admin"
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(models.User).filter(models.User.email == admin_email).first()
        if existing_user:
            print(f"L'utilisateur {admin_email} existe deja.")
            return
        
        # Création de l'admin
        new_admin = models.User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            role=models.UserRole.ADMIN,
            nom_complet="Administrateur Digital Crown"
        )
        
        db.add(new_admin)
        db.commit()
        print(f"SUCCESS: Utilisateur admin cree : {admin_email} / {admin_password}")
        
    except Exception as e:
        print(f"ERROR: Erreur lors du seeding de l'utilisateur : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()
