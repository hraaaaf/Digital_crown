"""Legacy compatibility gate: prohibit PyTorch fallback entirely."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "backend/services/vision_service.py").read_text(encoding="utf-8")
tree = ast.parse(source)
assert "torch" not in source.lower()
assert "ceph_weights" not in source
assert "_initialize_legacy_engine" not in source
assert any(isinstance(node, ast.ClassDef) and node.name == "VisionEngine" for node in tree.body)
assert 'mode = "FAILED"' in source
print("SRPOSE38_ONLY_GATE=OK")
