"""Synthetic integration-only check for CORS headers from Pocket AND master.

Does not import the application, open a clinic DB, run a network call or mutate data.
"""
import ast
from pathlib import Path


def test_merged_cors_header_contract():
    src = Path(__file__).resolve().parents[1] / "backend" / "main.py"
    module = ast.parse(src.read_text(encoding="utf-8"))
    candidates = [
        node for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_middleware"
        and node.args and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "CORSMiddleware"
    ]
    assert len(candidates) == 1, "Expected one effective CORSMiddleware registration"
    options = {kw.arg: ast.literal_eval(kw.value) for kw in candidates[0].keywords
               if kw.arg in {"allow_headers", "expose_headers"}}
    assert {"Authorization", "Content-Type", "Accept", "Idempotency-Key"} <= set(options["allow_headers"])
    assert {"Content-Disposition", "X-Document-Id", "X-Idempotent-Replay",
            "X-Total-Count", "X-Cephalo-Analysis-Id", "X-Cephalo-Revision",
            "X-Cephalo-Archive-Replayed"} <= set(options["expose_headers"])
