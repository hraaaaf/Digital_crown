import sys
import os
import cv2
import numpy as np

# Add the backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".")))

from backend.services.sota_vision_service import sota_vision_engine
from backend.services.cephalo_engine import cephalo_engine

def test_full_pipeline():
    # Create a dummy image
    img = np.zeros((1024, 1024, 3), dtype=np.uint8)
    dummy_path = "dummy_radio.jpg"
    cv2.imwrite(dummy_path, img)
    
    try:
        print("Testing SOTA prediction...")
        res = sota_vision_engine.predict_landmarks(dummy_path)
        print("SOTA prediction successful.")
        
        pts = res["landmarks"]
        points_dict = {p['id']: (p['x'], p['y']) for p in pts}
        
        print("Testing CephaloEngine metrics calculation...")
        metrics = cephalo_engine.calculate_metrics(points_dict, custom_mm_ratio=0.1)
        print("CephaloEngine calculation successful.")
        
        print("Pipeline works!")
    except Exception as e:
        print(f"PIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

if __name__ == "__main__":
    test_full_pipeline()
