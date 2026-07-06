"""Seed d'un cabinet de démonstration — dentiste + assistante + config cabinet.

Usage : python -m backend.seed_demo
Idempotent : ne recrée rien si le compte démo existe déjà.
Ne s'exécute jamais automatiquement au démarrage de l'app (script manuel
uniquement — usage : démos commerciales, captures d'écran, vidéos).
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend import models
from backend.security import get_password_hash

DEMO_DENTISTE_EMAIL = "demo.dentiste@digitalcrown.ma"
DEMO_DENTISTE_PASSWORD = "DemoCrown2026!"
DEMO_SECRETAIRE_EMAIL = "demo.assistante@digitalcrown.ma"
DEMO_SECRETAIRE_PASSWORD = "DemoCrown2026!"

DEMO_CABINET_NAME = "Cabinet Dentaire Digital Crown — Démo"
DEMO_DENTISTE_NOM = "Dr. Amine Bensaïd"
DEMO_SECRETAIRE_NOM = "Fatima Zahra Alaoui"


def seed_demo_cabinet():
    db = SessionLocal()
    try:
        existing_dentiste = db.query(models.User).filter(
            models.User.email == DEMO_DENTISTE_EMAIL
        ).first()
        if existing_dentiste:
            print(f"Le cabinet démo existe déjà (dentiste : {DEMO_DENTISTE_EMAIL}).")
            return

        # 1. Dentiste (compte principal du cabinet)
        dentiste = models.User(
            email=DEMO_DENTISTE_EMAIL,
            hashed_password=get_password_hash(DEMO_DENTISTE_PASSWORD),
            role=models.UserRole.DENTISTE,
            nom_complet=DEMO_DENTISTE_NOM,
            is_active=True,
            is_licensed=True,
        )
        db.add(dentiste)
        db.flush()

        # 2. Configuration du cabinet
        cabinet_config = models.CabinetConfig(
            owner_id=dentiste.id,
            nom_cabinet=DEMO_CABINET_NAME,
            nom_praticien=DEMO_DENTISTE_NOM,
            header_lines_fr=[DEMO_DENTISTE_NOM, "Chirurgien-Dentiste"],
            is_initialized=True,
        )
        db.add(cabinet_config)

        # 3. Assistante (sous-compte SECRETAIRE, permissions par défaut)
        secretaire = models.User(
            email=DEMO_SECRETAIRE_EMAIL,
            hashed_password=get_password_hash(DEMO_SECRETAIRE_PASSWORD),
            role=models.UserRole.SECRETAIRE,
            nom_complet=DEMO_SECRETAIRE_NOM,
            employer_id=dentiste.id,
            is_active=True,
            is_licensed=True,
            approval_status="approved",
            permissions={
                "agenda": True, "patients": True, "prescriptions": False,
                "accounting": False, "payments": False, "clinical": False,
                "panoramic": False, "cephalo": False, "settings": False,
            },
        )
        db.add(secretaire)

        db.commit()
        print("SUCCESS: Cabinet démo créé.")
        print(f"  Cabinet    : {DEMO_CABINET_NAME}")
        print(f"  Dentiste   : {DEMO_DENTISTE_EMAIL} / {DEMO_DENTISTE_PASSWORD}")
        print(f"  Assistante : {DEMO_SECRETAIRE_EMAIL} / {DEMO_SECRETAIRE_PASSWORD}")

    except Exception as e:
        print(f"ERROR: Erreur lors du seed démo : {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_cabinet()
