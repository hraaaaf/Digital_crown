
import sys
import os
from sqlalchemy.orm import Session
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from backend.database import SessionLocal
from backend import models
from backend.security import verify_password

def check_mo():
    db = SessionLocal()
    try:
        email = "mo@digitalcrown.com"
        password = "DentisteMo2026!"
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            print(f"ERROR: L'utilisateur {email} n'existe pas dans la base.")
            return
        
        print(f"SUCCESS: Utilisateur {email} trouve (ID: {user.id}).")
        
        if verify_password(password, user.hashed_password):
            print("SUCCESS: Le mot de passe est valide.")
        else:
            print("ERROR: Le mot de passe est INVALIDE.")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_mo()
