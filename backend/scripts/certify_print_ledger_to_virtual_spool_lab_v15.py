#!/usr/bin/env python3
"""LOT04.8-C CI-only *synthetic* ledger-to-CUPS demonstration.

NOT the Cabinet print worker and NOT a clinical authorization path. The real
Cabinet preflight remains deny-only because printer certification is absent.
This harness explicitly makes a LAB claim for a made-up document, then submits
one fixed PostScript test sheet to a CUPS-PDF queue on an ephemeral GitHub
runner; it NEVER marks a patient print completed or opens a Station PDF.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import types

from sqlalchemy import create_engine, insert, select

if (
    os.environ.get("GITHUB_ACTIONS") != "true"
    or os.environ.get("DC_SYNTHETIC_VIRTUAL_SPOOL_LAB") != "1"
):
    raise SystemExit("Only an explicitly authorized synthetic GitHub Actions lab can run this")

for name, path in (("backend", "backend"), ("backend.services", "backend/services")):
    package = types.ModuleType(name)
    package.__path__ = [os.path.abspath(path)]
    sys.modules[name] = package

from backend.services.station_print_held_claims_lab import (
    SCHEMA, claim_events, claims,
    PrintClaimDuplicate, reserve_held_claim, get_claim,
)

folder = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve() / "print-lab-artifacts"
folder.mkdir(parents=True, exist_ok=True)
db_file = folder / "synthetic-ledger.db"
engine = create_engine("sqlite+pysqlite:///" + str(db_file))
SCHEMA.create_all(engine)
with engine.begin() as connection:
    connection.execute(insert(SCHEMA.tables["users"]).values(id=10))

fake = dict(
    tenant_id=10, session_id="SYNTHETIC_NOT_A_PATIENT_SESSION",
    document_kind="care_sheet", document_id="SYNTHETIC_PRINT_BRIDGE",
    document_sha256="1" * 64, printer_id="DC_VIRTUAL_PDF",
)
held = reserve_held_claim(engine, **fake)
assert held.state == "held"
try:
    reserve_held_claim(engine, **{**fake, "printer_id": "OTHER_VIRTUAL_DESTINATION"})
except PrintClaimDuplicate:
    pass
else:
    raise AssertionError("second destination was accepted")

with engine.connect() as connection:
    assert len(connection.execute(select(claims)).all()) == 1
    assert connection.execute(
        select(claim_events.c.revision, claim_events.c.transition)
    ).all() == [(1, "held_reserved")]

# Lab bypass is limited to a fixed synthetic PostScript; no claim or actual
# patient bytes are read by this script. Never use this route in production.
result = subprocess.run(
    [sys.executable, "backend/scripts/certify_v15_04_8_virtual_print.py"],
    check=True, capture_output=True, text=True, timeout=100,
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

proof_file = folder / "evidence.json"
proof = json.loads(proof_file.read_text(encoding="utf-8"))
assert proof["spool_output_created"] is True
assert proof["marker_verified_in_spool_output"] is True
assert proof["physical_paper_certified"] is False
assert get_claim(engine, tenant_id=10, delivery_key=held.delivery_key) == held

proof.update({
    "synthetic_lab_ledger_held": True,
    "single_destination_claim": True,
    "cross_destination_duplicate_denied": True,
    "claim_still_held_after_virtual_spool": True,
    "clinical_cabinet_permission_proven": False,
    "real_patient_document_printed": False,
    "printer_certification_proven": False,
    "production_path_dispatch_enabled": False,
    "lab_bypass_scope": "FIXED_NONCLINICAL_POSTSCRIPT_ONLY",
})
proof_file.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
engine.dispose()
db_file.unlink(missing_ok=True)
print("BCD_SYNTHETIC_LEDGER_TO_CUPS_PASS; NO CLINICAL PRINT AUTHORIZATION")
