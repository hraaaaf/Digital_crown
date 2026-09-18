import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/pharmacology_medicine_gap_audit.py"


def test_gap_audit_is_deterministic_and_fail_closed():
    first = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    second = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    assert first == second
    report = json.loads(first)
    assert report["total_medicines"] == 68
    assert report["clinical_activation_no"] == 68
    assert report["dimensions"]["regulatory_status"]["unresolved"] == 68
    assert report["rows_with_any_pending_token"] == 68
