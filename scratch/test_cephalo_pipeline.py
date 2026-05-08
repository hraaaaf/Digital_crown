import os
import sys
from datetime import datetime

# Ajout du dossier racine au path pour les imports
sys.path.append(os.getcwd())

from backend import schemas

from backend.services.vision_service import vision_engine
from backend.services.cephalo_engine import cephalo_engine

test_file = r"c:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\ai_models\cephld_cca\data\test\0img\100.png"

print(f"Testing file: {test_file}")
print(f"Exists: {os.path.exists(test_file)}")
print(f"Size: {os.path.getsize(test_file)} bytes")

try:
    result = vision_engine.predict_landmarks(test_file)
    print("Vision Success!")
    print(f"Landmarks detected: {len(result['landmarks'])}")
    
    # Test geometry
    points_dict = {p['id']: (p['x'], p['y']) for p in result['landmarks']}
    
    print("\nCheck Tooth Alignment:")
    for tid in ['U1_incisal', 'U1_apex', 'L1_incisal', 'L1_apex']:
        p = next((x for x in result['landmarks'] if x['id'] == tid), None)
        if p:
            print(f"  {tid:12}: {p['x']:8} , {p['y']:8}")
    
    from backend.services.calibration_service import calibration_service
    ratio = calibration_service.detect_mm_per_pixel(test_file)
    print(f"Auto-Calibration: {ratio if ratio else 'FAILED (using 0.1)'} mm/px")

    metrics = cephalo_engine.calculate_metrics(points_dict, custom_mm_ratio=ratio if ratio else 0.1)
    print("Geometry Success!")
    
    # Accès typé via Pydantic
    dentaire = metrics.metrics.analyse_dentaire
    osseuse = metrics.metrics.analyse_osseuse
    
    esthetique = metrics.metrics.analyse_esthetique
    
    count = 0
    for name, measure in dentaire:
        if isinstance(measure, schemas.MeasureData): count += 1
    for name, measure in osseuse:
        if isinstance(measure, schemas.MeasureData): count += 1
    for name, measure in esthetique:
        if isinstance(measure, schemas.MeasureData): count += 1
        
    print(f"Metrics count: {count}")

    # --- TEST GÉNÉRATION PDF (STEP 3) ---
    print("\n--- Testing PDF Generation (Step 3) ---")
    from backend.services.document_factory import DocumentFactory
    from unittest.mock import MagicMock
    
    # Mock des objets pour éviter la DB
    mock_db = MagicMock()
    mock_patient = MagicMock()
    mock_patient.nom = "TEST"
    mock_patient.prenom = "Patient"
    mock_patient.date_naissance = datetime(2015, 1, 1)
    mock_patient.id = 999
    
    # On mock l'analyse pour qu'elle ressemble à un objet SQLAlchemy
    image_path_test = "backend/ai_models/cephld_cca/data/test/0img/100.png"
    mock_analysis = MagicMock()
    mock_analysis.results = metrics.model_dump()
    mock_analysis.image_path = image_path_test
    
    doc_factory = DocumentFactory()
    
    # On mock _get_cabinet_config pour éviter l'appel DB
    doc_factory._get_cabinet_config = MagicMock(return_value=None)
    
    pdf_path = doc_factory.create_cephalo_report(mock_patient, mock_analysis, db=mock_db, user_id=1)
    print(f"PDF Success! Path: {pdf_path}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
