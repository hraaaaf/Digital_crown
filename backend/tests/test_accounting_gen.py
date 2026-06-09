from datetime import date
from pydantic import BaseModel
from typing import List, Optional
import os

from backend.services.generators.accounting_gen import AccountingGenerator

class MockPatient(BaseModel):
    nom: str = "Test"
    prenom: str = "Patient"
    date_naissance: date = date(1990, 1, 1)

class MockPayment(BaseModel):
    acte: str = "Consultation"
    dent: str = "11"
    mode_reglement: str = "Espèces"
    montant: float = 12000.50

class MockDataNote(BaseModel):
    doc_date: date = date.today()
    payments: List[MockPayment] = [MockPayment()]

class MockItem(BaseModel):
    acte: str = "Couronne"
    dent: str = "21"
    prix_unitaire: float = 12000.50

class MockDataDevis(BaseModel):
    doc_date: date = date.today()
    items: List[MockItem] = [MockItem()]

def test_accounting_gen_note():
    generator = AccountingGenerator(base_output_dir="backend/scratch/tests/documents")
    patient = MockPatient()
    data = MockDataNote()
    
    # Should run without exception
    filepath = generator.generate_note(patient, data, facture_number="F-001")
    
    assert os.path.exists(filepath)
    os.remove(filepath)

def test_accounting_gen_devis():
    generator = AccountingGenerator(base_output_dir="backend/scratch/tests/documents")
    patient = MockPatient()
    data = MockDataDevis()
    
    # Generate devis with enough items to trigger compression logic
    data.items = [MockItem() for _ in range(12)]
    
    filepath = generator.generate_devis(patient, data, document_number="D-001")
    
    assert os.path.exists(filepath)
    os.remove(filepath)
