import shutil
import sys
import os
sys.path.append(os.getcwd())
from backend.database import engine
from sqlalchemy import text

source_img = r'C:\Users\lenovo\.gemini\antigravity-ide\brain\b446072a-f488-450f-b8ff-f2f74d15a8c8\media__1780306560156.png'
dest_dir = r'c:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\static\uploads\clinics\ebd0d193b8434997'
dest_img = os.path.join(dest_dir, 'logo_with_text.png')

# Copy the file
shutil.copy2(source_img, dest_img)
print(f'Copied to {dest_img}')

# Update database
with engine.connect() as conn:
    conn.execute(text("UPDATE cabinet_configs SET logo_path = :path"), {'path': dest_img})
    conn.commit()
    print('Database updated successfully!')

# Generate a test PDF to verify
from backend.database import SessionLocal
from backend.models import Patient
from backend.routers.documents import doc_factory
from backend.schemas import OrdonnanceData

db = SessionLocal()
patient = db.query(Patient).first()
data = OrdonnanceData(doc_date='2026-06-01', medications=[])
try:
    pdf = doc_factory.create_ordonnance(patient, data, db, 1)
    print(f'Test PDF generated: {pdf}')
except Exception as e:
    print('PDF Generation Error:', e)
