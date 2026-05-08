import os
import sys
import decimal

# Set up paths
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.document_factory import DocumentFactory
from backend.models import CabinetConfig

def test_amount_to_words():
    gen = AccountingGenerator()
    
    test_cases = [
        (0.00, "Zéro Dirham"),
        (1.00, "Un Dirham"),
        (2.00, "Deux Dirhams"),
        (15.50, "Quinze Dirhams et cinquante Centimes"),
        (0.75, "Zéro Dirham et soixante-quinze Centimes"),
        (100.00, "Cent Dirhams"),
        (101.00, "Cent un Dirhams"),
        (1000.00, "Mille Dirhams"),
        (1250.75, "Mille deux cent cinquante Dirhams et soixante-quinze Centimes"),
    ]
    
    print("\n--- Testing _amount_to_words ---")
    for amount, expected in test_cases:
        result = gen._amount_to_words(amount)
        status = "✅ PASS" if result == expected else f"❌ FAIL (Got: {result})"
        print(f"{amount:8.2f} MAD => {result:50} {status}")

def test_format_medications():
    class MockMed:
        def __init__(self, nom, dosage, posologie):
            self.nom = nom
            self.dosage = dosage
            self.posologie = posologie

    meds = [
        MockMed("PARACETAMOL", "500mg", "3x/jour"),
        MockMed("AMOXICILLINE", "1g", " matin et soir")
    ]
    
    html = DocumentFactory._format_medications(meds)
    print("\n--- Testing _format_medications ---")
    print(html)
    
    # Check for ReportLab compatibility
    if "<br/>" in html and "<ul>" not in html:
        print("✅ ReportLab compatible format detected.")
    else:
        print("❌ Malformed or incompatible HTML detected.")

def test_footer_contacts():
    from backend.services.base_template import BaseTemplate
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import tempfile
    
    print("\n--- Testing Footer Contacts Data Logic ---")
    
    config = CabinetConfig(
        contacts_json={
            "fixe": {"enabled": True, "value": "0522000000"},
            "mobile": {"enabled": True, "value": "0661000000"},
            "whatsapp": {"enabled": False, "value": "0662000000"},
            "instagram": {"enabled": True, "value": "@dr_cabinet"}
        }
    )
    
    # We simulate what _draw_footer does internally
    contacts_to_show = []
    c_json = config.contacts_json
    labels = {"fixe": "Tel", "mobile": "Mob", "whatsapp": "WA", "instagram": "IG"}
    for key in ["fixe", "mobile", "whatsapp", "instagram"]:
        info = c_json.get(key)
        if isinstance(info, dict) and info.get("enabled") and info.get("value"):
            contacts_to_show.append(f"{labels[key]}: {info['value'].strip()}")
    
    contact_str = " | ".join(contacts_to_show)
    print(f"Generated String: {contact_str}")
    
    expected = "Tel: 0522000000 | Mob: 0661000000 | IG: @dr_cabinet"
    if contact_str == expected:
        print("✅ Contact string logic PASS")
    else:
        print(f"❌ Contact string logic FAIL (Got: {contact_str})")

if __name__ == "__main__":
    try:
        test_amount_to_words()
        test_format_medications()
        test_footer_contacts()
        print("\n🎉 ALL TESTS COMPLETED")
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR DURING TESTS: {e}")
        import traceback
        traceback.print_exc()
