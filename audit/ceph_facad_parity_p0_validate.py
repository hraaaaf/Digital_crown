"""Proof-only FACAD / Digital Crown matrix validator."""
import json
from pathlib import Path

MATRIX = Path(__file__).resolve().parents[1] / 'docs/audits/data/CEPH_FACAD_PARITY_P0_DESKTOP_EVIDENCE_MATRIX_2026-10-17.json'


def load():
    return json.loads(MATRIX.read_text(encoding='utf-8'))
