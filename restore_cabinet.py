import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# On ajoute le dossier parent au path pour pouvoir importer backend
sys.path.append(os.getcwd())

# On cherche la database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost/digitalcrown_db?client_encoding=utf8")
print(f"Using database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def manual_migration():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN specialty_ids JSONB DEFAULT '[]'"))
            conn.commit()
            print("Added specialty_ids column manually.")
        except Exception as e:
            print(f"Specialty_ids column might already exist or error: {e}")
        
        try:
            conn.execute(text("ALTER TABLE cabinet_configs ADD COLUMN nom_praticien_ar VARCHAR DEFAULT ''"))
            conn.commit()
            print("Added nom_praticien_ar column manually.")
        except Exception as e:
            print(f"Nom_praticien_ar column might already exist or error: {e}")

manual_migration()

try:
    from backend.models import CabinetConfig
    # On rafraîchit la session pour voir les nouvelles colonnes
    db.expire_all()
    
    config = db.query(CabinetConfig).first()
    
    if not config:
        print("CabinetConfig not found!")
        sys.exit(1)

    print(f"Restoring cabinet {config.id}...")
    
    config.nom_praticien = "Benmoussa Achraf"
    config.nom_praticien_ar = "بنموسى أشرف"
    config.footer_address = "156, 1er étage, Secteur 3, Lotissement Zerdal Gharbia, Sidi Bouknadel, Salé"
    config.footer_phones = "📞 0537822333 | 💬 0648275852"
    config.ice = "001819709000006"
    config.inpe = "104164231"
    config.if_ = "14496345"
    
    # En-tête bilingue 5 lignes
    config.header_lines_fr = [
        "Dr. Benmoussa Achraf",
        "Chirurgien Dentiste",
        "Soins - Prothèse",
        "Chirurgie - Parodontologie",
        "Blanchiment - Orthodontie"
    ]
    
    config.header_lines_ar = [
        "بنموسى أشرف .د",
        "طبيب جراح للأسنان",
        "علاج - تعويض الأسنان",
        "جراحة - أمراض اللثة",
        "تبييض - تقويم الأسنان"
    ]
    
    config.specialty_ids = ["soins", "prothese", "chirurgie", "paro", "blanchiment", "ortho"]
    
    config.contacts_json = {
        "fixe": {"enabled": True, "value": "0537822333"},
        "whatsapp": {"enabled": True, "value": "0648275852"},
        "mobile": {"enabled": False, "value": ""},
        "instagram": {"enabled": False, "value": ""}
    }
    
    # On s'assure que les marges sont correctes
    config.margin_top = 3.6
    config.margin_bottom = 3.2
    
    db.commit()
    print("RESTORED SUCCESSFUL")
except Exception as e:
    print(f"Error during restore: {e}")
    db.rollback()
finally:
    db.close()
