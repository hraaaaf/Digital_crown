
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
DB_URL = "postgresql://postgres:admin@localhost/digitalcrown_db"

def update():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Trouver la config du cabinet
        # On suppose qu'il n'y en a qu'une ou on prend la première
        res = session.execute(text("SELECT id FROM cabinet_configs LIMIT 1")).fetchone()
        if not res:
            print("Aucune configuration trouvée.")
            return
        
        config_id = res[0]
        
        # 2. Nouvelles données extraites de l'image
        nom_fr = "Dr. Benmoussa Achraf"
        nom_ar = "د. أشرف بنموسى"
        adresse = "156, 1er étage, Secteur 3, Lotissement Zerdal Gharbia, Sidi Bouknadel, Salé"
        telephones = "05 37 82 23 33 | 06 48 27 58 52"
        
        header_fr = [
            "Chirurgien Dentiste",
            "Soins - Prothèse",
            "Chirurgie - Parodontologie",
            "Blanchiment - Orthodontie"
        ]
        
        header_ar = [
            "طبيب جراح للأسنان",
            "علاج - تعويض الأسنان",
            "جراحة - أمراض اللثة",
            "تبييض - تقويم الأسنان"
        ]
        
        # 3. Mise à jour (on utilise JSONB pour les listes si c'est le cas, ou un formatage spécifique)
        # Note: header_lines est stocké en JSONB dans PostgreSQL
        import json
        
        sql = text("""
            UPDATE cabinet_configs 
            SET nom_praticien = :nom_fr,
                nom_praticien_ar = :nom_ar,
                adresse = :adresse,
                telephone = :telephones,
                header_lines_fr = :h_fr,
                header_lines_ar = :h_ar,
                letterhead_path = NULL,
                watermark_enabled = TRUE,
                selected_template = 'classic'
            WHERE id = :id
        """)
        
        session.execute(sql, {
            "nom_fr": nom_fr,
            "nom_ar": nom_ar,
            "adresse": adresse,
            "telephones": telephones,
            "h_fr": json.dumps(header_fr),
            "h_ar": json.dumps(header_ar),
            "id": config_id
        })
        
        session.commit()
        print(f"✅ Configuration mise à jour avec succès pour {nom_fr}")
        print("🚀 Le mode papier en-tête a été désactivé au profit du mode Wizard (Auto).")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur : {e}")
    finally:
        session.close()

if __name__ == "__main__":
    update()
