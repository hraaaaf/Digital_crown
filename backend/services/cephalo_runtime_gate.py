"""LOT08.2-I — fail-closed SRPose38 / legacy automatic cephalo activation.

Embedding a model is a packaging decision, never authorization to interpret
patient anatomy. Until an evidence-backed medical activation contract exists,
only a disposable, demonstrably synthetic non-frozen test process may infer.

No developer or end-user environment flag can enable this feature inside a
PyInstaller executable. This module is stdlib-only for earliest boot checks.
"""
from __future__ import annotations

import os
import sys


def can_run_cephalo_auto_inference() -> bool:
    """Allow only isolated synthetic LAB execution; deny all packaged/clinical use.

    In-memory SQLite may be used by tests in isolated runtime; a persistent
    SQLite target is permitted only on GitHub-hosted CI with the explicit
    isolated-runtime flag. There is no production opt-in while the scientific
    identity of the 38 channels remains unverified.
    """
    if bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS"):
        return False
    if os.environ.get("ENVIRONMENT", "").strip().lower() not in {"test", "rehearsal"}:
        return False
    if os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME", "").strip().lower() not in {"1", "true"}:
        return False
    database = os.environ.get("DATABASE_URL", "").strip()
    if database == "sqlite:///:memory:":
        return True
    return os.environ.get("GITHUB_ACTIONS") == "true" and database.startswith("sqlite:///")


CEPHALO_AUTO_HOLD_REASON = (
    "Repérage céphalométrique automatique désactivé : "
    "validation anatomique et activation clinique non établies. "
    "Aucune interprétation automatique n'a été effectuée. "
    "Placement manuel des repères requis."
)
