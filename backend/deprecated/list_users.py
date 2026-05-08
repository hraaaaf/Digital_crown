import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.database import SessionLocal
from backend import models

db = SessionLocal()
try:
    users = db.query(models.User).all()
    print("\n=== LISTE DES UTILISATEURS ===")
    for user in users:
        print(f"ID: {user.id} | Email: {user.email} | Nom: {user.nom_complet} | Role: {user.role}")
    print("==============================\n")
finally:
    db.close()
