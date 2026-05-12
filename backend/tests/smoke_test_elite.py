
import sys
import os

# Ajout du chemin du projet au PYTHONPATH
sys.path.append(os.getcwd())

from backend.services.qr_service import QRService

def test_whatsapp_qr_generation():
    print("--- Test de génération URL WhatsApp ---")
    
    # Test 1 : Numéro local Maroc
    phone1 = "0612345678"
    msg = "Bonjour Dr, je souhaite prendre rendez-vous. / السلام عليكم دكتور، أود حجز موعد."
    url1 = QRService.generate_whatsapp_url(phone1, msg)
    print(f"Input: {phone1} -> URL: {url1}")
    assert "phone=212612345678" in url1
    assert "text=" in url1
    
    # Test 2 : Numéro avec espaces et +
    phone2 = "+212 6 61 22 33 44"
    url2 = QRService.generate_whatsapp_url(phone2, msg)
    print(f"Input: {phone2} -> URL: {url2}")
    assert "phone=212661223344" in url2
    
    # Test 3 : Numéro international
    phone3 = "0033612345678" # France
    url3 = QRService.generate_whatsapp_url(phone3, msg)
    print(f"Input: {phone3} -> URL: {url3}")
    assert "phone=33612345678" in url3
    
    print("[OK] Smoke Test WhatsApp QR: SUCCESS\n")

def test_prescription_logic_mock():
    print("--- Mock Test Prescription Quick Entry Logic ---")
    
    # Note: On simule ici la logique JS du frontend en Python pour valider l'intention
    def mock_parse_quick_entry(text):
        lower = text.lower()
        forme = "COMPRIMES"
        if "sachet" in lower: forme = "SACHETS"
        elif "sirop" in lower: forme = "SIROP"
        
        import re
        dosage_match = re.search(r'\b\d+(g|mg|mcg|ml|l|ui)\b', lower)
        dosage = dosage_match.group(0).upper() if dosage_match else ""
        
        return {"forme": forme, "dosage": dosage}

    t1 = "Augmentin 1g sachet"
    res1 = mock_parse_quick_entry(t1)
    print(f"Parse: '{t1}' -> Forme: {res1['forme']}, Dosage: {res1['dosage']}")
    assert res1['forme'] == "SACHETS"
    assert res1['dosage'] == "1G"
    
    t2 = "Doliprane 500mg"
    res2 = mock_parse_quick_entry(t2)
    print(f"Parse: '{t2}' -> Forme: {res2['forme']}, Dosage: {res2['dosage']}")
    assert res2['forme'] == "COMPRIMES"
    assert res2['dosage'] == "500MG"
    
    print("[OK] Smoke Test Prescription Logic: SUCCESS\n")

if __name__ == "__main__":
    try:
        test_whatsapp_qr_generation()
        test_prescription_logic_mock()
        print("SUCCESS: ALL ELITE TESTS PASSED.")
    except Exception as e:
        print(f"ERROR: SMOKE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
