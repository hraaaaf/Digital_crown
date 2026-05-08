import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal, pwd_context
from backend import models

def repair_user():
    db = SessionLocal()
    try:
        # 1. On cherche l'utilisateur actuel
        user = db.query(models.User).filter(models.User.id == 1).first()
        if user:
            print(f"User found: {user.email}")
            # On remet l'email standard pour le praticien
            user.email = "admin@digitalcrown.com"
            # On s'assure que le mot de passe est 'admin' pour le dépannage (à changer après)
            user.hashed_password = pwd_context.hash("admin")
            user.nom_complet = "Dr. Benmoussa Achraf"
            db.commit()
            print("SUCCESS: Compte restaure vers admin@digitalcrown.com / admin")
        else:
            # Si aucun user ID 1, on le crée proprement
            new_admin = models.User(
                email="admin@digitalcrown.com",
                hashed_password=pwd_context.hash("admin"),
                role=models.UserRole.ADMIN,
                nom_complet="Dr. Benmoussa Achraf"
            )
            db.add(new_admin)
            db.commit()
            print("SUCCESS: Nouveau compte admin cree.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    repair_user()
