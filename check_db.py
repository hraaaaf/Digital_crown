
from backend.database import SessionLocal
from backend import models

db = SessionLocal()
try:
    med_count = db.query(models.Medication).count()
    print(f"Total medications in DB: {med_count}")
    if med_count > 0:
        meds = db.query(models.Medication).limit(5).all()
        for m in meds:
            print(f"- {m.nom}")
    
    habit_count = db.query(models.DoctorMedicationHabit).count()
    print(f"Total doctor habits in DB: {habit_count}")
finally:
    db.close()
