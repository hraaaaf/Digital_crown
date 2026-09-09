import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET_MODULE = "backend.services.clinical_coherence"
EXPECTED_RUNTIME_CONSUMERS = {
    "backend/routers/documents.py",
    "backend/services/elite_manager.py",
}


def _imports_target(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == TARGET_MODULE:
            return True
        if isinstance(node, ast.Import):
            if any(alias.name == TARGET_MODULE for alias in node.names):
                return True
    return False


def test_clinical_coherence_runtime_consumers_are_explicit_and_bounded():
    consumers = set()

    for path in (ROOT / "backend").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        if relative == "backend/services/clinical_coherence.py" or relative.startswith("backend/tests/"):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if _imports_target(source):
            consumers.add(relative)

    assert consumers == EXPECTED_RUNTIME_CONSUMERS, consumers
