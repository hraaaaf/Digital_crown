import sys
import os
import json

# Rigueur CTO : On force Python à trouver le dossier racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import engine, SessionLocal
from backend import models
from sqlalchemy.orm import Session

def run_seed():
    print("📡 Connexion au moteur principal de la base de données...")
    # S'assure que les nouvelles tables existent dans la VRAIE base
    models.Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # --- 1. CATÉGORIES CLINIQUES ---
        print("⏳ Injection des catégories...")
        categories_data = [
            (1, "Extraction Simple / Chirurgie Mineure"),
            (2, "Extraction Dents de Sagesse / Chirurgie Complexe"),
            (3, "Abcès Dentaire / Cellulite"),
            (4, "Pulpite Aiguë / Traitement Endodontique"),
            (5, "Chirurgie Parodontale / Implantaire"),
            (6, "Douleur Aiguë (sans infection majeure)"),
            (7, "Gingivite / Soins Parodontaux")
        ]
        for cid, label in categories_data:
            if not db.query(models.ClinicalCategory).filter_by(id=cid).first():
                db.add(models.ClinicalCategory(id=cid, label=label))

        # --- 2. MÉDICAMENTS ---
        print("⏳ Injection du dictionnaire des médicaments...")
        meds_data = [
            ("ACIGAM", "200 mg", "Comprimé sécable", 50),
            ("BISPIRAZOLE", "1.5 MUI / 250 mg", "Comprimé pelliculé", 50),
            ("COTIPRED", "20 mg", "Comprimé effervescent", 50),
            ("ACLAV", "1 g / 125 mg", "Sachet", 50),
            ("DOLIPRANE", "1 g", "Comprimé", 50),
            ("KIN GINGIVAL", "0.12%", "Bain de bouche", 50),
            ("PARODONTAX", "Fluor", "Pâte dentifrice", 50),
            ("ELGYDIUM MEDIUM", "Standard", "Brosse à dents", 50),
            ("AUGMENTIN", "1 g / 125 mg", "Sachet", 10),
            ("KLAMOKS", "1 g / 125 mg", "Sachet", 5),
            ("BIRODOGYL", "1.5 MUI / 250 mg", "Comprimé pelliculé", 10),
            ("SOLUPRED", "20 mg", "Comprimé effervescent", 10),
            ("ANTADYS", "100 mg", "Comprimé", 5),
            ("NUROFEN", "400 mg", "Comprimé pelliculé", 10),
            ("HEXTRIL", "0.1%", "Bain de bouche", 5),
            ("ARTHRODONT", "1%", "Pâte gingivale", 10)
        ]
        for nom, dosage, forme, usage in meds_data:
            if not db.query(models.Medication).filter_by(nom=nom).first():
                db.add(models.Medication(nom=nom, dosage=dosage, forme=forme, usage_count=usage))

        db.flush() # Force la validation temporaire pour la suite

        # --- 3. PROTOCOLES INTELLIGENTS ---
        print("⏳ Injection des protocoles...")
        protocols_data = [
            (1, 1, "Standard (Sans antibio)", [
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprimé sécable", "posologie": "1 comprimé 3 fois par jour pendant 3 jours"},
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "Après chaque brossage"}
            ]),
            (2, 1, "Avec Couverture (Option Aclav)", [
                {"nom": "ACLAV", "dosage": "1 g / 125 mg", "forme": "Sachet", "posologie": "1 sachet 3 fois par jour pendant 6 jours"},
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprimé sécable", "posologie": "1 comprimé 3 fois par jour pendant 3 jours"},
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "Après chaque brossage"}
            ]),
            (3, 2, "Chirurgie Lourde (Corticoïdes)", [
                {"nom": "COTIPRED", "dosage": "20 mg", "forme": "Comprimé effervescent", "posologie": "3 comprimés en prise unique le matin pendant 5 jours"},
                {"nom": "DOLIPRANE", "dosage": "1 g", "forme": "Comprimé", "posologie": "1 comprimé 3 fois par jour pendant 3 jours"},
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "À commencer le lendemain, après chaque brossage"}
            ]),
            (4, 3, "Infection Aiguë (Standard)", [
                {"nom": "ACLAV", "dosage": "1 g / 125 mg", "forme": "Sachet", "posologie": "1 sachet 3 fois par jour pendant 6 jours"},
                {"nom": "DOLIPRANE", "dosage": "1 g", "forme": "Comprimé", "posologie": "1 comprimé en cas de douleur (max 3/jour)"}
            ]),
            (5, 3, "Allergie Pénicilline", [
                {"nom": "BISPIRAZOLE", "dosage": "1.5 MUI / 250 mg", "forme": "Comprimé pelliculé", "posologie": "1 comprimé 3 fois par jour pendant 7 jours"},
                {"nom": "DOLIPRANE", "dosage": "1 g", "forme": "Comprimé", "posologie": "1 comprimé en cas de douleur (max 3/jour)"}
            ]),
            (6, 4, "Crise Douloureuse (Acigam)", [
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprimé sécable", "posologie": "1 comprimé matin et soir pendant 3 jours"}
            ]),
            (7, 4, "Alternative (Nurofen)", [
                {"nom": "NUROFEN", "dosage": "400 mg", "forme": "Comprimé pelliculé", "posologie": "1 comprimé 3 fois par jour pendant 3 jours"}
            ]),
            (8, 5, "Protocole Parodontal", [
                {"nom": "BISPIRAZOLE", "dosage": "1.5 MUI / 250 mg", "forme": "Comprimé pelliculé", "posologie": "1 comprimé 3 fois par jour pendant 5 jours"},
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprimé sécable", "posologie": "1 comprimé matin et soir pendant 3 jours"}
            ]),
            (9, 6, "Antalgique Palier 1", [
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprimé sécable", "posologie": "1 comprimé matin et soir pendant 3 jours"}
            ]),
            (10, 7, "Hygiène & Soins (Kin + Parodontax)", [
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "1 dose matin et soir après brossage (15 jours)"},
                {"nom": "PARODONTAX", "dosage": "Fluor", "forme": "Pâte dentifrice", "posologie": "Brossage 3 fois par jour (Dents et Gencives)"},
                {"nom": "ELGYDIUM MEDIUM", "dosage": "Standard", "forme": "Brosse à dents", "posologie": "Renouvellement de la brosse recommandé"}
            ]),
            (11, 7, "Alternative (Arthrodont)", [
                {"nom": "HEXTRIL", "dosage": "0.1%", "forme": "Bain de bouche", "posologie": "1 bain de bouche 2 à 3 fois par jour"},
                {"nom": "ARTHRODONT", "dosage": "1%", "forme": "Pâte gingivale", "posologie": "Brossage et massage gingival 3 fois par jour"},
                {"nom": "ELGYDIUM MEDIUM", "dosage": "Standard", "forme": "Brosse à dents", "posologie": "Renouvellement de la brosse recommandé"}
            ])
        ]
        
        for pid, cid, variant, meds in protocols_data:
            if not db.query(models.ClinicalProtocol).filter_by(id=pid).first():
                db.add(models.ClinicalProtocol(id=pid, category_id=cid, variant_name=variant, medications_json=meds))

        db.commit()
        print("✅ SUCCÈS ABSOLU : Les protocoles ont été injectés dans la base de données officielle de FastAPI.")

    except Exception as e:
        print(f"❌ Erreur lors de l'injection : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()