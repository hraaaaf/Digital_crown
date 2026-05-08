
import sys
import os
import decimal
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Patient, User, CabinetConfig
from backend.services.generators.accounting_gen import AccountingGenerator

def test_cloture_position():
    db = SessionLocal()
    try:
        # 1. Récupérer le patient test
        patient = db.query(Patient).filter(Patient.nom == "DUPONT").first()
        if not patient:
            print("Patient DUPONT non trouvé. Création...")
            from datetime import date
            patient = Patient(nom="DUPONT", prenom="Jean", date_naissance=date(1990, 5, 15), sexe="M", telephone="0600000000")
            db.add(patient)
            db.commit()
            db.refresh(patient)
            
        # 2. Récupérer l'utilisateur pour le branding
        user = db.query(User).first()
        user_id = user.id if user else 1
        
        # 3. Préparer les données de la note
        class MockPayment:
            def __init__(self, acte, montant, dent):
                self.acte = acte
                self.montant = montant
                self.dent = dent
                self.mode_reglement = "Espèces"

        class MockData:
            def __init__(self):
                self.payments = [
                    MockPayment("Examen clinique et détartrage complet", 400.0, "Multi"),
                    MockPayment("Pose de couronne zircone sur 46", 3500.0, "46"),
                    MockPayment("Traitement canalaire dent 46", 1200.0, "46")
                ]
                from datetime import date
                self.doc_date = date.today()

        data = MockData()
        
        # 4. Générer la note avec le nouveau moteur
        gen = AccountingGenerator()
        save_path = gen.generate_note(
            patient=patient,
            data=data,
            facture_number="TEST-2026-001",
            db=db,
            user_id=user_id
        )
        
        print(f"SUCCÈS : Note de test générée avec la phrase de clôture épinglée.")
        print(f"Chemin du fichier : c:/Users/lenovo/Documents/Cabinet/DigitalCrown/{save_path}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_cloture_position()
