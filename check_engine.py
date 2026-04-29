import sys
import os

# Add the backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".")))

from backend.services.sota_vision_service import sota_vision_engine

print(f"SOTA Engine Ready: {sota_vision_engine.is_ready}")
if not sota_vision_engine.is_ready:
    print("Engine NOT ready. Check logs.")
else:
    print("Engine is ready.")
