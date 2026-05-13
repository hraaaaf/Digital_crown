
import sys
import os
from datetime import datetime, timedelta, date
import random
import uuid

# Ajout de la racine du projet pour l'import des modules backend
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from backend.database import SessionLocal

from backend import models
from backend.security import get_password_hash

def seed_demo_mo():
    db = SessionLocal()
    try:
        # 1. Vérifier/Créer l'utilisateur "Mo"
        email_mo = "mo@digitalcrown.com"
        mo = db.query(models.User).filter(models.User.email == email_mo).first()
        
        if not mo:
            print(f"Création de l'utilisateur {email_mo}...")
            mo = models.User(
                email=email_mo,
                hashed_password=get_password_hash("DentisteMo2026!"),
                nom_complet="Dr. Mohamed El Idrissi",
                role=models.UserRole.DENTISTE,
                is_active=True,
                is_licensed=True, # Licence Elite offerte pour la démo !
                license_expires_at=datetime.now() + timedelta(days=365)
            )
            db.add(mo)
            db.commit()
            db.refresh(mo)
        
        # 2. Créer son CabinetConfig s'il n'existe pas
        config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == mo.id).first()
        if not config:
            print("Configuration du cabinet de démo...")
            config = models.CabinetConfig(
                owner_id=mo.id,
                nom_cabinet="Clinique Dentaire Elite Gauthier",
                footer_address="Angle Rue Taha Houcine et Rue de la Liberté, Quartier Gauthier, Casablanca",
                footer_phones="+212 5 22 45 67 89",
                primary_color="#0F172A", # Dark Navy Elite
                secondary_color="#D4AF37", # Gold Elite pour le Maroc
                margin_top=4.8,
                margin_bottom=4.5
            )

            db.add(config)
            db.commit()

        # 3. Supprimer les anciennes données de démo pour repartir à zéro (uniquement pour Mo)
        # On ne touche SURTOUT PAS aux données de l'admin.
        old_patients = db.query(models.Patient).filter(models.Patient.employer_id == mo.id).all()
        for p in old_patients:
            db.delete(p)
        db.commit()
        print(f"Nettoyage effectué pour {email_mo}.")

        # 4. Injecter 30 Patients MAROCAINS
        noms = ["Alami", "Bennani", "Tazi", "Mansouri", "Chraibi", "Filali", "Amrani", "Kabbaj", "Guessous", "Berrada", "Serghini", "Mernissi", "Belkhayat", "Lahlou", "Alaoui", "Skali", "Benjelloun", "Tahiri", "Ouazzani", "Idrissi"]
        prenoms_m = ["Mohamed", "Amine", "Youssef", "Omar", "Hamza", "Mehdi", "Younes", "Anas", "Rayane", "Adam", "Karim", "Hassan", "Ahmed", "Ismail", "Reda"]
        prenoms_f = ["Yasmine", "Kenza", "Sara", "Ghita", "Salma", "Ines", "Leyla", "Malak", "Lina", "Sofia", "Nour", "Rim", "Meriem", "Zineb", "Khadija"]
        quartiers = ["Maarif", "Gauthier", "Bourgogne", "Ain Diab", "Oasis", "Hay Riad", "Agdal", "Palmier"]
        
        patients = []
        for i in range(30):
            p_nom = random.choice(noms)
            sexe = random.choice(["M", "F"])
            p_prenom = random.choice(prenoms_m if sexe == "M" else prenoms_f)
            
            p = models.Patient(
                nom=p_nom,
                prenom=p_prenom,
                email=f"{p_prenom.lower()}.{p_nom.lower()}{i}@mail.ma",
                telephone=f"06{random.randint(60000000, 69999999)}", # Format mobile marocain
                date_naissance=date(random.randint(1950, 2015), random.randint(1, 12), random.randint(1, 28)),
                adresse=f"{random.randint(1, 200)} Rue du {random.choice(quartiers)}, Casablanca",
                sexe=sexe,
                employer_id=mo.id # Isolation !
            )


            db.add(p)
            patients.append(p)
        
        db.commit()
        for p in patients: db.refresh(p)
        print(f"30 patients injectés pour Dr. Mo.")

        # 5. Injecter des Actes pour peupler les stats
        print("Injection de l'historique de soins...")
        actes_possibles = [
            ("Détartrage", models.ActeType.SOIN, 43.38),
            ("Extraction dent de sagesse", models.ActeType.SOIN, 125.00),
            ("Pose de couronne céramique", models.ActeType.PROTHESE, 550.00),
            ("Bilan Parodontal", models.ActeType.SOIN, 80.00),
            ("Traitement de carie", models.ActeType.SOIN, 65.00),
            ("Implant Titane", models.ActeType.PROTHESE, 950.00)
        ]

        for p in patients:
            # 3 à 8 actes par patient pour avoir du volume
            for _ in range(random.randint(3, 8)):
                libelle, a_type, prix = random.choice(actes_possibles)
                acte = models.Acte(
                    patient_id=p.id,
                    praticien_id=mo.id,
                    type_acte=a_type,
                    libelle=libelle,
                    montant=prix,
                    date_debut=datetime.now() - timedelta(days=random.randint(1, 365)),
                    statut_paiement=random.choice([models.PaiementStatut.PAYE, models.PaiementStatut.PAYE, models.PaiementStatut.EN_ATTENTE]),
                    is_accounted=True,
                    is_collected=random.choice([True, True, False])
                )
                db.add(acte)
        db.commit()

        # 6. Remplir l'Agenda (4 semaines)
        print("Remplissage de l'agenda de démo...")
        start_date = datetime.now() - timedelta(days=7) # Une semaine dans le passé
        for day_offset in range(35): # 5 semaines au total
            current_day = start_date + timedelta(days=day_offset)
            if current_day.weekday() >= 5: continue # Pas de weekend en démo
            
            # 5 à 10 RDV par jour
            for hour in range(9, 18):
                if hour == 13: continue # Pause déj
                if random.random() > 0.3: # 70% de taux d'occupation
                    patient = random.choice(patients)
                    rdv = models.Appointment(
                        patient_id=patient.id,
                        employer_id=mo.id, # Multi-tenant isolation
                        datetime_start=current_day.replace(hour=hour, minute=random.choice([0, 30]), second=0),
                        duration_minutes=30,
                        motif=random.choice(["Contrôle", "Soin", "Urgence", "Bilan", "Chirurgie"]),
                        status=models.AppointmentStatus.TERMINE if current_day < datetime.now() else models.AppointmentStatus.PREVU,
                    )

                    db.add(rdv)
        
        db.commit()
        print("Agenda marketing finalisé.")
        print("\nSUCCÈS : L'univers de Dr. Mo est prêt pour les démos !")

    except Exception as e:
        db.rollback()
        print(f"ERREUR lors du seeding : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_mo()
