
import sys
import os
import decimal
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Patient, User
from backend.services.generators.accounting_gen import AccountingGenerator

def force_test_invoice():
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.nom == "DUPONT").first()
        user = db.query(User).first()
        user_id = user.id if user else 1
        
        class MockPayment:
            def __init__(self, acte, montant, dent):
                self.acte = acte
                self.montant = montant
                self.dent = dent
                self.mode_reglement = "Espèces"
        class MockData:
            def __init__(self):
                self.payments = [MockPayment("Couronne Zircone sur 46", 3500.0, "46"), MockPayment("Endo", 1000.0, "46")]
                from datetime import date
                self.doc_date = date.today()

        gen = AccountingGenerator()
        # On hack temporairement la sortie
        old_dir = gen.base_output_dir
        gen.base_output_dir = "."
        
        save_path = gen.generate_note(patient, MockData(), facture_number="WIN-FIX", db=db, user_id=user_id)
        
        # On le renomme proprement à la racine si besoin
        # Mais le script gère déjà le renommage dans generate_note
        print(f"FICHIER GÉNÉRÉ : {save_path}")
        
    finally:
        db.close()

if __name__ == "__main__":
    force_test_invoice()
