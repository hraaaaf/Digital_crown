import sys
import os
import json

# Rigueur CTO : On force Python à trouver le dossier racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import engine, SessionLocal
from backend import models
from sqlalchemy.orm import Session

def run_seed():
    print("Connexion au moteur principal de la base de donnees...")
    # S'assure que les nouvelles tables existent dans la VRAIE base
    models.Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # --- 1. CATEGORIES CLINIQUES ---
        print("Injection des categories...")
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

        # --- 2. MEDICAMENTS (Marché Marocain - Elite List) ---
        print("Injection du dictionnaire des medicaments (Maroc)...")
        meds_data = [
            # Antibiotiques - Adultes
            ("CLAMOXYL 500mg", "500 mg", "Gélule", 100),
            ("CLAMOXYL 1g", "1 g", "Sachet", 120),
            ("AMOXICILLINE 500mg", "500 mg", "Gélule", 80),
            ("AMOXICILLINE 1g", "1 g", "Comprimé", 80),
            ("AUGMENTIN 1g", "1 g / 125 mg", "Sachet", 150),
            ("AUGMENTIN 1g (Compr)", "1 g / 125 mg", "Comprimé", 90),
            ("ACLAV 1g", "1 g / 125 mg", "Sachet", 100),
            ("RODOGYL", "750 000 UI / 125 mg", "Comprimé", 140),
            ("BISPIRAZOLE", "1.5 MUI / 250 mg", "Comprimé", 130),
            ("BIRODOGYL", "1.5 MUI / 250 mg", "Comprimé", 120),
            ("FLAGYL 500mg", "500 mg", "Comprimé", 70),
            ("DALACIN 300mg", "300 mg", "Gélule", 50),
            ("PYOSTACINE 500mg", "500 mg", "Comprimé", 40),
            
            # Antibiotiques - Enfants
            ("CLAMOXYL 250mg (Enf)", "250 mg", "Sachet", 60),
            ("CLAMOXYL 125mg (Nour)", "125 mg", "Sachet", 60),
            ("AUGMENTIN ENFANT", "100 mg/12.5 mg", "Sirop (Suspension)", 50),
            ("AUGMENTIN NOURRISSON", "100 mg/12.5 mg", "Sirop (Suspension)", 50),
            
            # Antalgiques - Adultes
            ("DOLIPRANE 500mg", "500 mg", "Gélule", 200),
            ("DOLIPRANE 1g", "1 g", "Comprimé", 250),
            ("DOLIPRANE 1g (Sach)", "1 g", "Sachet", 150),
            ("DAFALGAN 500mg", "500 mg", "Gélule", 100),
            ("DAFALGAN 1g", "1 g", "Comprimé", 120),
            ("DOLIPRANE CODEINE", "500 mg / 30 mg", "Comprimé", 80),
            ("DAFALGAN CODEINE", "500 mg / 30 mg", "Comprimé", 80),
            
            # Antalgiques - Enfants
            ("DOLIPRANE 100mg", "100 mg", "Sachet", 70),
            ("DOLIPRANE 150mg", "150 mg", "Sachet", 70),
            ("DOLIPRANE 200mg", "200 mg", "Sachet", 70),
            ("DOLIPRANE 300mg", "300 mg", "Sachet", 70),
            ("DOLIPRANE 100mg (Supp)", "100 mg", "Suppositoire", 50),
            ("DOLIPRANE 150mg (Supp)", "150 mg", "Suppositoire", 50),
            ("DOLIPRANE 200mg (Supp)", "200 mg", "Suppositoire", 50),
            ("DOLIPRANE 300mg (Supp)", "300 mg", "Suppositoire", 50),
            
            # Anti-inflammatoires (AINS)
            ("SURGAM 200mg", "200 mg", "Comprimé", 120),
            ("SURGAM 100mg", "100 mg", "Comprimé", 80),
            ("APRANAX 550mg", "550 mg", "Comprimé", 110),
            ("APRANAX 275mg", "275 mg", "Comprimé", 90),
            ("VOLTARENE 50mg", "50 mg", "Comprimé", 80),
            ("PROFENID 100mg", "100 mg", "Comprimé", 70),
            ("ANTADYS 100mg", "100 mg", "Comprimé", 100),
            ("NUROFEN 400mg", "400 mg", "Comprimé", 100),
            
            # Corticoïdes
            ("SOLUPRED 20mg", "20 mg", "Comprimé orodispersible", 95),
            ("SOLUPRED 5mg", "5 mg", "Comprimé orodispersible", 70),
            ("CELESTENE 2mg", "2 mg", "Comprimé", 60),
            ("CELESTENE Gouttes", "0.05%", "Gouttes", 50),
            
            # Bains de bouche
            ("ELUDRIL", "Standard", "Flacon", 110),
            ("HEXTRIL", "0.1%", "Flacon", 100),
            ("BETADINE BUCCALE", "10%", "Flacon", 90),
            ("PAROEX", "0.12%", "Flacon", 80),
            ("KIN GINGIVAL", "0.12%", "Bain de bouche", 70),
            
            # Divers
            ("DAKTARIN Gel", "2%", "Gel buccal", 40),
            ("ARTHRODONT", "1%", "Pâte gingivale", 60),
            ("PARODONTAX", "Fluor", "Pâte dentifrice", 40),
        ]
        for nom, dosage, forme, usage in meds_data:
            existing = db.query(models.Medication).filter_by(nom=nom).first()
            if not existing:
                db.add(models.Medication(nom=nom, dosage=dosage, forme=forme, usage_count=usage))
            else:
                existing.dosage = dosage
                existing.forme = forme
                existing.usage_count = usage

        db.flush() # Force la validation temporaire pour la suite

        # --- 3. PROTOCOLES INTELLIGENTS ---
        print("Injection des protocoles...")
        protocols_data = [
            (1, 1, "Standard (Sans antibio)", [
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprime secable", "posologie": "1 comprime 3 fois par jour pendant 3 jours"},
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "Apres chaque brossage"}
            ]),
            (2, 1, "Avec Couverture (Option Aclav)", [
                {"nom": "ACLAV", "dosage": "1 g / 125 mg", "forme": "Sachet", "posologie": "1 sachet 3 fois par jour pendant 6 jours"},
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprime secable", "posologie": "1 comprime 3 fois par jour pendant 3 jours"},
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "Apres chaque brossage"}
            ]),
            (3, 2, "Chirurgie Lourde (Corticoides)", [
                {"nom": "COTIPRED", "dosage": "20 mg", "forme": "Comprime effervescent", "posologie": "3 comprimes en prise unique le matin pendant 5 jours"},
                {"nom": "DOLIPRANE", "dosage": "1 g", "forme": "Comprime", "posologie": "1 comprime 3 fois par jour pendant 3 jours"},
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "A commencer le lendemain, apres chaque brossage"}
            ]),
            (4, 3, "Infection Aigue (Standard)", [
                {"nom": "ACLAV", "dosage": "1 g / 125 mg", "forme": "Sachet", "posologie": "1 sachet 3 fois par jour pendant 6 jours"},
                {"nom": "DOLIPRANE", "dosage": "1 g", "forme": "Comprime", "posologie": "1 comprime en cas de douleur (max 3/jour)"}
            ]),
            (5, 3, "Allergie Penicilline", [
                {"nom": "BISPIRAZOLE", "dosage": "1.5 MUI / 250 mg", "forme": "Comprime pellicule", "posologie": "1 comprime 3 fois par jour pendant 7 jours"},
                {"nom": "DOLIPRANE", "dosage": "1 g", "forme": "Comprime", "posologie": "1 comprime en cas de douleur (max 3/jour)"}
            ]),
            (6, 4, "Crise Douloureuse (Acigam)", [
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprime secable", "posologie": "1 comprime matin et soir pendant 3 jours"}
            ]),
            (7, 4, "Alternative (Nurofen)", [
                {"nom": "NUROFEN", "dosage": "400 mg", "forme": "Comprime pellicule", "posologie": "1 comprime 3 fois par jour pendant 3 jours"}
            ]),
            (8, 5, "Protocole Parodontal", [
                {"nom": "BISPIRAZOLE", "dosage": "1.5 MUI / 250 mg", "forme": "Comprime pellicule", "posologie": "1 comprime 3 fois par jour pendant 5 jours"},
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprime secable", "posologie": "1 comprime matin et soir pendant 3 jours"}
            ]),
            (9, 6, "Antalgique Palier 1", [
                {"nom": "ACIGAM", "dosage": "200 mg", "forme": "Comprime secable", "posologie": "1 comprime matin et soir pendant 3 jours"}
            ]),
            (10, 7, "Hygiene & Soins (Kin + Parodontax)", [
                {"nom": "KIN GINGIVAL", "dosage": "0.12%", "forme": "Bain de bouche", "posologie": "1 dose matin et soir apres brossage (15 jours)"},
                {"nom": "PARODONTAX", "dosage": "Fluor", "forme": "Pate dentifrice", "posologie": "Brossage 3 fois par jour (Dents et Gencives)"},
                {"nom": "ELGYDIUM MEDIUM", "dosage": "Standard", "forme": "Brosse a dents", "posologie": "Renouvellement de la brosse recommande"}
            ]),
            (11, 7, "Alternative (Arthrodont)", [
                {"nom": "HEXTRIL", "dosage": "0.1%", "forme": "Bain de bouche", "posologie": "1 bain de bouche 2 a 3 fois par jour"},
                {"nom": "ARTHRODONT", "dosage": "1%", "forme": "Pate gingivale", "posologie": "Brossage et massage gingival 3 fois par jour"},
                {"nom": "ELGYDIUM MEDIUM", "dosage": "Standard", "forme": "Brosse a dents", "posologie": "Renouvellement de la brosse recommande"}
            ])
        ]
        
        for pid, cid, variant, meds in protocols_data:
            if not db.query(models.ClinicalProtocol).filter_by(id=pid).first():
                db.add(models.ClinicalProtocol(id=pid, category_id=cid, variant_name=variant, medications_json=meds))

        db.commit()
        print("SUCCES : Les protocoles ont ete injectes.")

    except Exception as e:
        print(f"❌ Erreur lors de l'injection : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()