#!/usr/bin/env python3
"""Bootstrap un nouveau cabinet avec admin cabinet (propriétaire/owner).

Rôle : DENTISTE (propriétaire dentiste du cabinet, jamais SUPERADMIN global)

Sécurité :
- Refuse si DB = digitalcrown_db
- Refuse si ENVIRONMENT n'est pas safe (rehearsal/test)
- Utilise modèles/services officiels
- Utilise hashing officiel (pas de bypass)
- Idempotent
- Ne logge jamais les passwords en clair
- Jamais SUPERADMIN global pour cabinet client
"""
import os
import sys
import uuid
from datetime import datetime

# Vérifications de sécurité AVANT les imports
db_url = os.environ.get('DATABASE_URL', '')
if 'digitalcrown_db' in db_url:
    print("ERROR: DATABASE_URL pointe vers digitalcrown_db (vraie base cabinet)")
    print("BLOCKED: Utiliser une DB isolée pour bootstrap")
    sys.exit(1)

env = os.environ.get('ENVIRONMENT', '')
if env not in ('e2e_install_rehearsal', 'install_rehearsal', 'test', 'development'):
    print(f"ERROR: ENVIRONMENT={env} n'est pas autorisé pour bootstrap")
    print("BLOCKED: Utiliser ENVIRONMENT=rehearsal ou test")
    sys.exit(1)

# Imports
from backend.models import CabinetConfig, User
from backend.security import get_password_hash
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker

# Créer session
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
db = Session()

# Vérifier que cabinet ne existe pas (idempotent)
existing_cabinets = db.query(CabinetConfig).count()
if existing_cabinets > 0:
    print(f"INFO: {existing_cabinets} cabinet(s) existent déjà en DB rehearsal")
    db.close()
    sys.exit(0)

# Créer owner/propriétaire cabinet (DENTISTE, jamais ADMIN global)
# NOTE: domaine .local est un TLD réservé (RFC 6762 mDNS) rejeté par le validateur
# email Pydantic (email-validator) indépendamment du DNS. Utiliser un TLD non réservé,
# comme le font les fixtures de test réelles (backend/tests/conftest.py -> @cabinet.ma)
owner_email = 'owner.e2e@e2e-rehearsal.ma'
owner_password = 'E2E_Test_Pass_Rehearsal_2026'  # Généré, jamais loggé en clair

try:
    owner_user = User(
        email=owner_email,
        hashed_password=get_password_hash(owner_password),
        role='DENTISTE',  # Cabinet owner dentiste, pas SUPERADMIN global
        is_active=True,
        # is_licensed=True : simule un cabinet avec licence active. En prod,
        # ce champ est piloté par Firebase (jamais modifié ici) ; en rehearsal
        # isolé (Firebase injoignable), on seed directement l'état local pour
        # représenter un cabinet légitimement licencié — aucune logique de
        # validation de licence n'est modifiée.
        is_licensed=True,
    )
    db.add(owner_user)
    db.flush()
    print(f"Cabinet owner créé: {owner_email} (rôle: DENTISTE propriétaire)")
except Exception as e:
    print(f"ERROR: Impossible créer user: {str(e)[:100]}")
    db.rollback()
    db.close()
    sys.exit(1)

# Créer cabinet lié au owner
try:
    cabinet = CabinetConfig(
        owner_id=owner_user.id,
        public_id=str(uuid.uuid4())[:8],
        is_initialized=True
    )
    db.add(cabinet)
    db.commit()
    print(f"Cabinet créé et lié à owner: {cabinet.id}")
except Exception as e:
    print(f"ERROR: Impossible créer cabinet: {str(e)[:100]}")
    db.rollback()
    db.close()
    sys.exit(1)

# Résumé sécurisé (ne pas afficher password)
print("\n--- Bootstrap complété ---")
print(f"Email: {owner_email}")
print(f"Rôle: DENTISTE (propriétaire cabinet, pas SUPERADMIN global)")
print(f"Cabinet ID: {cabinet.id}")
print(f"User ID: {owner_user.id}")
print(f"Actif: {owner_user.is_active}")
print("\nPassword stocké en hash sécurisé (non affiché)")
print("\nNOTE: Le superadmin global reste benmoussa.achraf@gmail.com sur digitalcrown_db")

db.close()
