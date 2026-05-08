"""Script d'inspection des données comptabilité."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend import models
from sqlalchemy import func

db = SessionLocal()

# 1. Combien de documents au total ?
total = db.query(models.DocumentArchive).count()
print(f"\n{'='*60}")
print(f"TOTAL documents en BDD : {total}")
print(f"{'='*60}")

# 2. Répartition par type
all_types = db.query(
    models.DocumentArchive.document_type, 
    func.count(models.DocumentArchive.id)
).group_by(models.DocumentArchive.document_type).all()
print("\nRépartition par type :")
for doc_type, count in all_types:
    print(f"  {doc_type.value if hasattr(doc_type, 'value') else doc_type} : {count}")

# 3. Répartition par statut
all_status = db.query(
    models.DocumentArchive.status, 
    func.count(models.DocumentArchive.id)
).group_by(models.DocumentArchive.status).all()
print("\nRépartition par statut :")
for status, count in all_status:
    print(f"  {status.value if hasattr(status, 'value') else status} : {count}")

# 4. Détail des NOTE_HONORAIRES
notes = db.query(models.DocumentArchive).filter(
    models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES
).all()
print(f"\n--- Détail des {len(notes)} NOTE_HONORAIRES ---")
for d in notes:
    amount = 0
    if d.clinical_data:
        if 'payments' in d.clinical_data:
            amount = sum(float(p.get('montant', 0)) for p in d.clinical_data['payments'])
        elif 'items' in d.clinical_data:
            amount = sum(float(i.get('prix_unitaire', 0)) for i in d.clinical_data['items'])
    
    patient_name = "?"
    if d.patient:
        patient_name = f"{d.patient.nom} {d.patient.prenom}"
    
    print(f"  id={d.id} | patient_id={d.patient_id} ({patient_name})")
    print(f"    title={d.title} | status={d.status.value}")
    print(f"    date={d.created_at} | montant={amount} MAD")
    print(f"    filename={d.original_filename}")
    cd_keys = list(d.clinical_data.keys()) if d.clinical_data else None
    print(f"    clinical_data keys={cd_keys}")
    print()

# 5. Combien de patients ont des notes archivées ?
patients_with_notes = db.query(
    func.count(func.distinct(models.DocumentArchive.patient_id))
).filter(
    models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES
).scalar()
print(f"Patients avec notes archivées : {patients_with_notes}")

# 6. Combien de patients au total ?
total_patients = db.query(models.Patient).count()
print(f"Patients total en BDD : {total_patients}")

db.close()
print(f"\n{'='*60}")
