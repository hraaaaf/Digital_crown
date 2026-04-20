import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend import models
from backend.models import DocumentType, DocumentStatus

def sync_legacy_documents():
    db = SessionLocal()
    count_notes = 0
    count_others = 0
    
    # Chemins sources
    BASE_DIR = Path("backend/static/patients")
    
    if not BASE_DIR.exists():
        print(f"Erreur: {BASE_DIR} n'existe pas.")
        return

    print(f"Demarrage de la synchronisation depuis {BASE_DIR}...")
    
    # Parcourir chaque dossier patient (ex: 70_ESSAADI_Fatima)
    for patient_dir in BASE_DIR.iterdir():
        if not patient_dir.is_dir():
            continue
            
        # Extraire l'ID du patient (premier element avant _)
        try:
            patient_id_str = patient_dir.name.split('_')[0]
            patient_id = int(patient_id_str)
        except (ValueError, IndexError):
            print(f"  ID invalide pour le dossier: {patient_dir.name}")
            continue
            
        # Verifier si le patient existe
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            print(f"  Patient ID {patient_id} non trouve en BDD (Dossier: {patient_dir.name})")
            continue
            
        docs_dir = patient_dir / "Documents"
        if not docs_dir.exists():
            continue
            
        # Parcourir les PDFs du dossier Documents
        for pdf_file in docs_dir.glob("*.pdf"):
            filename = pdf_file.name
            
            # Verifier si deja en BDD par son chemin (eviter doublons)
            # On stocke le chemin relatif "static/patients/..."
            relative_path = f"static/patients/{patient_dir.name}/Documents/{filename}"
            
            existing = db.query(models.DocumentArchive).filter(
                models.DocumentArchive.file_path.ilike(f"%{filename}")
            ).first()
            
            if existing:
                # print(f"    Document deja present: {filename}")
                continue
                
            # --- MODE STRICT : ON IMPORTE UNIQUEMENT LES NOTES ---
            if not filename.startswith("NOTE_"):
                continue
                
            doc_type = DocumentType.NOTE_HONORAIRES
            
            # Extraire la date du nom (DDMMYYYY apres le premier _)
            creation_date = datetime.now()
            parts = filename.split('_')
            if len(parts) > 1 and len(parts[1]) == 8:
                try:
                    d_str = parts[1]
                    creation_date = datetime.strptime(d_str, "%d%m%Y")
                except ValueError:
                    pass

            # Creer l'archive
            # Note: On ne peut pas connaitre le montant exact, donc 0.0
            # Mais cela permet d'afficher la ligne en comptabilite et archives
            new_doc = models.DocumentArchive(
                patient_id=patient_id,
                document_type=doc_type,
                filename=filename,
                original_filename=filename,
                document_group_id=f"legacy_{patient_id}_{filename}",
                version_number=1,
                is_latest_version=True,
                file_hash=f"legacy_{filename}", # Placeholder
                file_size=pdf_file.stat().st_size,
                file_path=relative_path, # Attention: doit correspondre a ce que le backend attend
                title=filename.replace("_", " ").replace(".pdf", ""),
                clinical_data={"is_legacy": True, "total": 0.0},
                status=DocumentStatus.ACTIF,
                created_at=creation_date
            )
            
            db.add(new_doc)
            if doc_type == DocumentType.NOTE_HONORAIRES:
                count_notes += 1
            else:
                count_others += 1
    
    db.commit()

    # --- PARTIE 2 : SCAN DU DOSSIER GLOBAL archive/NOTE ---
    GLOBAL_NOTE_DIR = Path("backend/static/archive/NOTE")
    if GLOBAL_NOTE_DIR.exists():
        print(f"\nScan du dossier global des notes: {GLOBAL_NOTE_DIR}...")
        for year_dir in GLOBAL_NOTE_DIR.iterdir():
            if not year_dir.is_dir(): continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir(): continue
                for pdf_file in month_dir.glob("*.pdf"):
                    filename = pdf_file.name
                    
                    # Verifier si deja en BDD
                    existing = db.query(models.DocumentArchive).filter(
                        models.DocumentArchive.filename == filename
                    ).first()
                    if existing: continue

                    # Identifier le patient (ex: NOTE_02042026_7080_ESSAADI.pdf)
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        nom_patient = parts[3].replace(".pdf", "").upper()
                        # Chercher le patient par nom (approximation)
                        patient = db.query(models.Patient).filter(models.Patient.nom.ilike(f"%{nom_patient}%")).first()
                        if patient:
                            # Importer
                            relative_path = f"backend/static/archive/NOTE/{year_dir.name}/{month_dir.name}/{filename}"
                            new_doc = models.DocumentArchive(
                                patient_id=patient.id,
                                document_type=DocumentType.NOTE_HONORAIRES,
                                filename=filename,
                                original_filename=filename,
                                document_group_id=f"global_{filename}",
                                version_number=1,
                                is_latest_version=True,
                                file_hash=f"global_{filename}",
                                file_size=pdf_file.stat().st_size,
                                file_path=relative_path,
                                title=f"Note d'honoraires - {nom_patient}",
                                clinical_data={"is_legacy": True, "total": 0.0},
                                status=DocumentStatus.ACTIF,
                                created_at=datetime.now() # Date de scan si parsing echoue
                            )
                            db.add(new_doc)
                            count_notes += 1
        db.commit()

    print(f"\nTermine !")
    print(f"Notes d'honoraires importees: {count_notes}")
    print(f"Autres documents importes: {count_others}")
    db.close()

if __name__ == "__main__":
    sync_legacy_documents()
