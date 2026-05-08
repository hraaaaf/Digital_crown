
import os
import sys

# Ajouter le chemin racine au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.panoramic_service import panoramic_engine as old_engine
from backend.services.sota_panoramic_service import panoramic_engine as sota_engine
import asyncio

async def test():
    print("--- Test Panoramic Engines ---")
    
    print("\n1. Testing Old Engine (best.onnx)...")
    await old_engine.initialize()
    print(f"Old Engine Ready: {old_engine.is_ready}")
    if old_engine.session:
        print(f"Old Engine Input: {old_engine.session.get_inputs()[0].shape}")
        print(f"Old Engine Output: {old_engine.session.get_outputs()[0].shape}")

    print("\n2. Testing SOTA Engine (panoramic_model.onnx)...")
    # SOTA engine self-initializes in __init__
    print(f"SOTA Engine Session: {sota_engine.session is not None}")
    if sota_engine.session:
        print(f"SOTA Engine Input: {sota_engine.session.get_inputs()[0].shape}")
        print(f"SOTA Engine Output: {sota_engine.session.get_outputs()[0].shape}")

if __name__ == "__main__":
    asyncio.run(test())
