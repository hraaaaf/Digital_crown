from __future__ import annotations

import ast
import builtins
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VISION_SERVICE = ROOT / "backend" / "services" / "vision_service.py"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _bootstrap_backend_namespace() -> None:
    if "backend" not in sys.modules:
        backend_pkg = types.ModuleType("backend")
        backend_pkg.__path__ = [str(ROOT / "backend")]
        backend_pkg.__package__ = "backend"
        sys.modules["backend"] = backend_pkg

    if "backend.services" not in sys.modules:
        services_pkg = types.ModuleType("backend.services")
        services_pkg.__path__ = [str(ROOT / "backend" / "services")]
        services_pkg.__package__ = "backend.services"
        sys.modules["backend.services"] = services_pkg


def check_no_eager_torch_import() -> None:
    module = ast.parse(VISION_SERVICE.read_text(encoding="utf-8"))
    top_level_imports: list[str] = []
    for node in module.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_imports.append(node.module)
    _require("torch" not in top_level_imports, "vision_service must not import torch at module scope")


def check_constructor_is_lightweight() -> None:
    _bootstrap_backend_namespace()
    from backend.services import vision_service

    engine = vision_service.VisionEngine()
    _require(engine.legacy_init_attempted is False, "VisionEngine constructor initialized legacy runtime")
    _require(engine.torch is None, "VisionEngine constructor resolved torch eagerly")
    _require(engine.model is None, "VisionEngine constructor loaded legacy model eagerly")
    _require(engine.is_ready is False, "Legacy engine must not be ready before first fallback demand")


def check_winerror_1455_fail_closed() -> None:
    _bootstrap_backend_namespace()
    from backend.services import vision_service

    engine = vision_service.VisionEngine()
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "torch":
            raise OSError(1455, "Le fichier de pagination est insuffisant")
        return real_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=guarded_import):
        engine._initialize_legacy_engine()

    _require(engine.legacy_init_attempted is True, "Legacy fallback attempt was not recorded")
    _require(engine.torch is None, "Torch remained bound after WinError 1455")
    _require(engine.model is None, "Legacy model exists after WinError 1455")
    _require(engine.is_ready is False, "Legacy engine became ready after WinError 1455")


def main() -> int:
    check_no_eager_torch_import()
    check_constructor_is_lightweight()
    check_winerror_1455_fail_closed()
    print("LAZY_PYTORCH_BOOT_GATE=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
