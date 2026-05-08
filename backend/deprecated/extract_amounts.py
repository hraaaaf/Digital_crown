import os
import sys
import re
from pathlib import Path
import PyPDF2

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend import models
from backend.models import DocumentType

def extract_amount_from_pdf(pdf_path):
    """Extrait le montant TOTAL d'un PDF de note d'honoraires."""
    try:
        if not os.path.exists(pdf_path):
            # Essayer avec le prefixe backend/ si pas trouve
            alt_path = os.path.join("backend", pdf_path)
            if os.path.exists(alt_path):
                pdf_path = alt_path
            else:
                return None

        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            # Strategie 1 : Chercher "TOTAL" suivi d'un nombre
            # Exemple: TOTAL 1 500.00 ou TOTAL 400.00
            match = re.search(r"TOTAL\s*([\d\s,.]+)", text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).strip()
                # Nettoyer les espaces (ex: 1 500 -> 1500)
                amount_str = amount_str.replace(" ", "").replace(",", "")
                try:
                    return float(amount_str)
                except ValueError:
                    pass
            
            # Strategie 2 : Chercher dans la phrase de cloture
            # Exemple: "la somme de Quatre cents Dirhams" -> Plus dur, 
            # mais on peut chercher un nombre isole a la fin du tableau
            # Chercher le dernier nombre avant "Dirhams"
            matches = re.findall(r"(\d+[\s,.]\d{2})\s*Dirhams", text)
            if matches:
                return float(matches[-1].replace(" ", "").replace(",", ""))

    except Exception as e:
        print(f"      Erreur lecture {pdf_path}: {e}")
    return None

def process_all_notes():
    db = SessionLocal()
    try:
        # Trouver les notes qui ont un montant de 0 ou qui sont marquées legacy
        notes = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.document_type == DocumentType.NOTE_HONORAIRES
        ).all()
        
        print(f"Analyse de {len(notes)} notes d'honoraires...")
        updated_count = 0
        
        for doc in notes:
            # On tente l'extraction
            amount = extract_amount_from_pdf(doc.file_path)
            
            if amount is not None and amount > 0:
                # Mettre à jour clinical_data
                data = doc.clinical_data or {}
                
                # On simule une structure payments pour que la comptabilite la lise
                data['payments'] = [{"acte": "Note Importee", "montant": amount}]
                data['total'] = amount
                data['is_legacy'] = True
                
                # Marquer l'objet comme modifie pour SQLAlchemy
                doc.clinical_data = data
                models.flag_modified(doc, "clinical_data")
                
                print(f"  [SUCCES] ID {doc.id} ({doc.original_filename}) -> {amount} MAD")
                updated_count += 1
            else:
                print(f"  [ECHEC] ID {doc.id} ({doc.original_filename}) -> Montant non trouve")
        
        db.commit()
        print(f"\nTermine ! {updated_count} notes ont ete mises a jour avec leurs vrais montants.")
        
    finally:
        db.close()

if __name__ == "__main__":
    from sqlalchemy.orm.attributes import flag_modified
    # On monkeypatch car models.flag_modified n'existe peut-etre pas direct
    models.flag_modified = flag_modified
    process_all_notes()
