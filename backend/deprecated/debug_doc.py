
from backend import database, models
import json

db = database.SessionLocal()
patient = db.query(models.Patient).first()
if not patient:
    print("No patient found")
    exit()

print(f"Testing for Patient ID: {patient.id}")

from backend.services.document_factory import DocumentFactory
from backend.schemas import OrdonnanceData, MedicationSchema

doc_factory = DocumentFactory()

data = OrdonnanceData(
    medications=[
        MedicationSchema(nom="Test Med", dosage="1g", posologie="1x/j")
    ],
    doc_date="2026-04-20"
)

try:
    path = doc_factory.create_ordonnance(patient, data, db, 1)
    print(f"Generated path: {path}")
except Exception as e:
    import traceback
    traceback.print_exc()
