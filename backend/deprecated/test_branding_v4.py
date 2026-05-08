
import sys
import os
from datetime import datetime, date
from typing import Dict, Any

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import models
from backend.services.generators.ordonnance_gen import OrdonnanceGenerator
from backend.services.generators.certificat_gen import CertificatGenerator
from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.template_engine import TemplateEngine

class DummyPatient:
    def __init__(self):
        self.nom = "BENMOUSSA"
        self.prenom = "Achraf"
        self.date_naissance = date(1990, 5, 15)
        self.sexe = "Homme"

class DummyMed:
    def __init__(self, nom, dosage, posologie, forme):
        self.nom = nom
        self.dosage = dosage
        self.posologie = posologie
        self.forme = forme

class DummyOrdonnanceData:
    def __init__(self):
        self.medications = [
            DummyMed("Amoxicilline", "500mg", "1 gélule 3 fois par jour pendant 7 jours", "Gélules"),
            DummyMed("Doliprane", "1000mg", "1 comprimé en cas de douleur", "Comprimés")
        ]
        self.doc_date = date.today()

class DummyCertificatData:
    def __init__(self):
        self.is_work_stop = True
        self.days = 3
        self.start_date = date.today()
        self.reason = "Grippe saisonnière"
        self.doc_date = date.today()

class DummyPayment:
    def __init__(self, acte, montant, mode="Espèces"):
        self.acte = acte
        self.montant = montant
        self.mode_reglement = mode
        self.dents = [11, 12]

class DummyNoteData:
    def __init__(self):
        self.payments = [
            DummyPayment("Consultation", 300.0),
            DummyPayment("Détartrage", 500.0)
        ]
        self.doc_date = date.today()

def test_document_generation():
    print("🚀 Démarrage des Tests de Génération Documentaire v4.6...")
    
    patient = DummyPatient()
    
    # 1. Test Ordonnance
    print("\n📦 Test Ordonnance...")
    ord_gen = OrdonnanceGenerator()
    ord_data = DummyOrdonnanceData()
    path = ord_gen.generate(patient, ord_data)
    print(f"[OK] Ordonnance générée : {path}")
    
    # 2. Test Certificat
    print("\n📦 Test Certificat...")
    cert_gen = CertificatGenerator()
    cert_data = DummyCertificatData()
    path = cert_gen.generate(patient, cert_data)
    print(f"[OK] Certificat généré : {path}")
    
    # 3. Test Note d'honoraires
    print("\n📦 Test Note d'honoraires...")
    acc_gen = AccountingGenerator()
    note_data = DummyNoteData()
    path = acc_gen.generate_note(patient, note_data, facture_number="2026-001")
    print(f"[OK] Note générée : {path}")
    
    print("\n✅ Tous les documents ont été générés avec succès.")
    print("Veuillez vérifier visuellement les PDF pour confirmer le branding Elite.")

if __name__ == "__main__":
    test_document_generation()
