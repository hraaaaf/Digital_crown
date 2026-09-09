"""Architecture guard: legacy cephalo_engine must stay quarantined behind cephalo_safe_engine."""
from pathlib import Path
import ast

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
ALLOWED_RUNTIME = {
    REPO_ROOT / "backend/services/cephalo_safe_engine.py",
}


def _imports_legacy_engine(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "backend.services.cephalo_engine":
            return True
        if isinstance(node, ast.Import):
            if any(alias.name == "backend.services.cephalo_engine" for alias in node.names):
                return True
    return False


def test_legacy_cephalo_engine_has_single_runtime_import_boundary():
    offenders = []
    for path in BACKEND.rglob("*.py"):
        if "tests" in path.parts:
            continue
        if _imports_legacy_engine(path) and path not in ALLOWED_RUNTIME:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"Direct runtime imports of legacy cephalo_engine: {offenders}"


def test_safe_adapter_is_the_only_allowed_runtime_consumer():
    assert _imports_legacy_engine(next(iter(ALLOWED_RUNTIME)))
